import asyncio
import csv
import os
import json
import time
import hashlib
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# --- Configuration ---
OUTPUT_FOLDER = 'snappshop_output'
MAX_SCROLL_ATTEMPTS = 20  # تعداد تلاش برای اسکرول تا پایان صفحه
SCROLL_PAUSE = 1.0        # زمان مکث بین اسکرول‌ها برای لود شدن محتوا
MAX_FILE_SIZE_MB = 5      # حداکثر حجم فایل CSV قبل از ایجاد فایل جدید
BASE_URL = "https://snappshop.ir"

# --- ANSI Colors ---
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

def log_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE} >>> {text} <<< {Colors.RESET}")

def log_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def log_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def log_info(text):
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.RESET}")

def log_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

def log_progress(current, total, text=""):
    if total == 0: total = 1
    percent = (current / total) * 100
    bar_length = 30
    filled = int(bar_length * current / total)
    bar = "█" * filled + "░" * (bar_length - filled)
    print(f"\r{Colors.CYAN}[{bar}] {current}/{total} ({percent:.1f}%) {text}{Colors.RESET}", end="", flush=True)
    if current == total:
        print()

# --- Helper Functions ---
def ensure_output_folder():
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
        log_success(f"Created output folder: {OUTPUT_FOLDER}")

def get_csv_filename(shop_name=""):
    # حذف کاراکترهای خاص از نام فروشگاه برای جلوگیری از خطا در نام فایل
    safe_name = "".join([c for c in shop_name if c.isalnum() or c in (' ', '_', '-')]).strip()
    base_name = f"snappshop_{safe_name}" if safe_name else "snappshop_products"
    return os.path.join(OUTPUT_FOLDER, f"{base_name}.csv")

def get_existing_products():
    existing_hashes = set()
    existing_links = set()
    csv_file = get_csv_filename()
    if not os.path.exists(csv_file):
        return existing_hashes, existing_links
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row and 'link' in row:
                    existing_links.add(row['link'])
                    # ایجاد هش برای تشخیص تکراری بودن بر اساس نام و قیمت
                    if 'name' in row and 'price' in row:
                        unique_str = f"{row['name']}_{row['price']}"
                        hash_obj = hashlib.md5(unique_str.encode())
                        existing_hashes.add(hash_obj.hexdigest())
        log_info(f"Loaded {len(existing_links)} existing products for deduplication.")
    except Exception as e:
        log_warning(f"Could not read existing products: {str(e)[:50]}")
    return existing_hashes, existing_links

def is_duplicate(product, existing_hashes):
    unique_str = f"{product['name']}_{product['price']}"
    hash_obj = hashlib.md5(unique_str.encode())
    return hash_obj.hexdigest() in existing_hashes

def get_file_size_mb(filepath):
    if os.path.exists(filepath):
        return os.path.getsize(filepath) / (1024 * 1024)
    return 0

def get_new_csv_filename(base_filename):
    if not os.path.exists(base_filename):
        return base_filename
    size_mb = get_file_size_mb(base_filename)
    if size_mb < MAX_FILE_SIZE_MB:
        return base_filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_path = base_filename.replace('.csv', '')
    new_filename = f"{base_path}_{timestamp}.csv"
    log_warning(f"CSV file too large ({size_mb:.2f}MB). Creating: {new_filename}")
    return new_filename

def save_to_csv(data, shop_name=""):
    ensure_output_folder()
    if not data:
        return
    csv_file = get_csv_filename(shop_name)
    csv_file = get_new_csv_filename(csv_file)
    fieldnames = ['name', 'price', 'link', 'image', 'specs_json', 'vendor', 'scraped_at']
    try:
        file_exists = os.path.exists(csv_file)
        with open(csv_file, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
            if not file_exists:
                writer.writeheader()
            for row in data:
                if 'specs' in row and isinstance(row['specs'], dict):
                    row['specs_json'] = json.dumps(row['specs'], ensure_ascii=False)
                    del row['specs']
                row['scraped_at'] = datetime.now().isoformat()
                writer.writerow(row)
        size_mb = get_file_size_mb(csv_file)
        log_success(f"Saved {len(data)} products to {csv_file} (Size: {size_mb:.2f}MB)")
    except Exception as e:
        log_error(f"Failed to save CSV: {str(e)[:100]}")

# --- JavaScript Extractors ---
def get_product_links_js():
    """JS to find all product cards in the list view and return their links."""
    return """
    () => {
        const links = [];
        // انتخابگر برای کارت‌های محصول در صفحه لیست
        // در HTML نمونه شما، لینک اصلی دور تگ article است
        const productCards = document.querySelectorAll('a[href*="/product/"]');
        
        productCards.forEach(linkEl => {
            const href = linkEl.getAttribute('href');
            if (href) {
                links.push(href);
            }
        });
        return links;
    }
    """

def get_images_js():
    """JS to extract all image URLs from the gallery slider."""
    return """
    () => {
        const images = [];
        // جستجو در اسلایدرهای عکس‌ها
        const slides = document.querySelectorAll('.keen-slider__slide img');
        slides.forEach(img => {
            // سعی می‌کنیم src اصلی را بگیریم
            let src = img.getAttribute('src');
            if (src) {
                // اگر src خالی بود یا relative بود، کاملش کن
                if (!src.startsWith('http')) {
                    src = 'https:' + src;
                }
                images.push(src);
            }
        });
        // همچنین چک کن که آیا عکس بزرگ اصلی دیگری هست یا نه
        const mainImg = document.querySelector('.gallery_gallery__main-img img');
        if (mainImg) {
            let src = mainImg.getAttribute('src');
            if (src && !src.startsWith('http')) src = 'https:' + src;
            if (src && !images.includes(src)) {
                images.unshift(src); // عکس اصلی را اول لیست بگذار
            }
        }
        return images;
    }
    """

def get_specs_js():
    """JS to extract product features/specs."""
    return """
    () => {
        const specs = {};
        // بر اساس HTML نمونه: ul با liهایی که span دارند
        const specList = document.querySelector('.featured-attributes_featured-attributes-container__JCqdw ul');
        if (specList) {
            const items = specList.querySelectorAll('li');
            items.forEach(li => {
                const spans = li.querySelectorAll('span');
                if (spans.length >= 2) {
                    const key = spans[0].innerText.trim();
                    const value = spans[1].innerText.trim();
                    if (key && value) {
                        specs[key] = value;
                    }
                }
            });
        }
        return specs;
    }
    """

# --- Main Scraper Logic ---
async def get_product_links(page, target_url):
    """Navigate to list page, scroll to load all products."""
    log_info(f"Navigating to: {target_url}")
    await page.goto(target_url, wait_until='domcontentloaded', timeout=30000)
    await asyncio.sleep(2) # Wait for initial render
    
    # اسکرول برای لود شدن محصولات
    links = set()
    last_height = 0
    stable_count = 0
    
    log_info("Scrolling to load all products...")
    
    while stable_count < MAX_SCROLL_ATTEMPTS:
        # Extract links from current DOM
        current_links = await page.evaluate(get_product_links_js())
        for link in current_links:
            if link.startswith('/'):
                full_link = f"{BASE_URL}{link}"
            else:
                full_link = link
            links.add(full_link)
        
        # Check height
        new_height = await page.evaluate("() => document.documentElement.scrollHeight")
        if new_height == last_height:
            stable_count += 1
        else:
            stable_count = 0
        last_height = new_height
        
        if stable_count < MAX_SCROLL_ATTEMPTS:
            await page.evaluate("() => window.scrollBy(0, 800)")
            await asyncio.sleep(SCROLL_PAUSE)
            log_progress(len(links), len(links) + 10, f"Found {len(links)} products so far")
        else:
            log_success("End of page reached.")
            break
            
    return list(links)

async def extract_product_details(page, product_url, existing_links, existing_hashes):
    """Navigate to product page and extract details."""
    if product_url in existing_links:
        return None
        
    try:
        # 1. Use 'domcontentloaded' instead of 'networkidle' to avoid hanging on slow assets
        # Increase timeout to 30s just in case
        await page.goto(product_url, wait_until='domcontentloaded', timeout=30000)
        
        # 2. Wait for React/Vue to render the content
        await asyncio.sleep(2) 
        
        # 3. Extract Name
        name = "نام محصول نامشخص"
        try:
            # بر اساس HTML: h1 با کلاس text-bold text-iransans-en-digits
            name_el = await page.query_selector('h1.text-bold.text-iransans-en-digits')
            if not name_el:
                # Fallback
                name_el = await page.query_selector('h1')
            if name_el:
                name = (await name_el.inner_text()).strip()
        except Exception:
            pass
            
        # 4. Extract Price
        price = "0"
        try:
            # بر اساس HTML: span با کلاس text-bold داخل Price_price__discounted__1kz0X
            price_el = await page.query_selector('.Price_price__discounted__1kz0X .text-bold')
            if price_el:
                price = (await price_el.inner_text()).strip()
            else:
                # Fallback برای قیمت‌های بدون تخفیف
                price_el = await page.query_selector('.pdp-top-section_left-top-section__buy-box__hQwAF .text-bold.h5')
                if price_el:
                    price = (await price_el.inner_text()).strip()
        except Exception:
            pass
            
        # 5. Extract Images (Multiple)
        images = []
        try:
            images = await page.evaluate(get_images_js())
        except Exception:
            pass
        
        # اگر عکس‌ای پیدا نشد، سعی کن عکس alt را هم چک کنی
        if not images:
            try:
                img_el = await page.query_selector('img[alt]')
                if img_el:
                    src = await img_el.get_attribute('src')
                    if src:
                        if not src.startswith('http'): src = 'https:' + src
                        images.append(src)
            except: pass
            
        # 6. Extract Specs
        specs_dict = {}
        try:
            specs_dict = await page.evaluate(get_specs_js())
        except Exception:
            pass
            
        # 7. Extract Vendor Name
        vendor = "نامشخص"
        try:
            # بر اساس HTML: دکمه‌ای که لینک فروشنده دارد
            vendor_el = await page.query_selector('a[href*="/seller/"]')
            if vendor_el:
                vendor = (await vendor_el.inner_text()).strip()
        except Exception:
            pass
            
        # 8. Check Availability (موجود بودن)
        is_available = False
        try:
            # جستجو برای دکمه "افزودن به سبد خرید"
            # کلاس دکمه: Button_module_button__e4d724c9
            buy_btn = await page.query_selector('button.Button_module_button__e4d724c9')
            if buy_btn:
                btn_text = await buy_btn.inner_text()
                if "افزودن به سبد خرید" in btn_text or "خرید" in btn_text:
                    is_available = True
                elif "ناموجود" in btn_text or "بروزرسانی" in btn_text:
                    is_available = False
                else:
                    # اگر دکمه هست ولی متنش معروف نیست، فرض میکنیم موجود است مگر کلاس خاصی داشته باشد
                    is_available = True
        except Exception:
            pass
            
        if not is_available:
            log_warning(f"Product is not available: {name[:30]}...")
            return None
            
        # Construct Product Object
        product_data = {
            'name': name,
            'price': price,
            'link': product_url,
            'image': images[0] if images else "", 
            'images_list': images, 
            'specs': specs_dict,
            'vendor': vendor
        }
        
        # Store images in specs for backup
        product_data['specs']['images_urls'] = images
        
        # Check Duplicate
        if is_duplicate(product_data, existing_hashes):
            return None
            
        log_success(f"Extracted: {name[:30]}... | Price: {price} | Available: {is_available}")
        return product_data
        
    except PlaywrightTimeoutError:
        log_warning(f"Timeout for: {product_url}")
        return None
    except Exception as e:
        log_error(f"Error extracting {product_url}: {str(e)[:50]}")
        return None

async def scrape_snappshop():
    log_header("🚀 SNAPPSHOP SCRAPER (MULTI-IMAGE & AVAILABILITY CHECK)")
    
    url = input(f"\n{Colors.BOLD}Enter SnappShop URL (e.g., Seller URL or Product List):{Colors.RESET} ").strip()
    if not url.startswith("http"):
        log_error("Invalid URL.")
        return
    
    ensure_output_folder()
    existing_hashes, existing_links = get_existing_products()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu'
            ]
        )
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        log_info("Browser launched")
        
        start_time = time.time()
        try:
            # Step 1: Get Links
            log_header("📜 COLLECTING PRODUCT LINKS")
            product_links = await get_product_links(page, url)
            
            if not product_links:
                log_error("No products found.")
                await browser.close()
                return
                
            log_success(f"Found {len(product_links)} product links")
            
            # Step 2: Extract Details
            log_header("🔍 EXTRACTING PRODUCT DETAILS")
            all_products = []
            skipped_count = 0
            
            for idx, link in enumerate(product_links, 1):
                print(f"\r{Colors.DIM}[{idx}/{len(product_links)}]{Colors.RESET} ", end="", flush=True)
                
                product_data = await extract_product_details(
                    page, link, existing_links, existing_hashes
                )
                
                if product_data:
                    all_products.append(product_data)
                    existing_links.add(link)
                else:
                    skipped_count += 1
                    
                await asyncio.sleep(0.2) # Respectful delay
                
                if idx % 10 == 0:
                    log_progress(idx, len(product_links), f"({len(all_products)} new)")
            
            # Step 3: Save
            if all_products:
                log_header("💾 SAVING RESULTS")
                # استخراج نام فروشگاه از URL برای نام‌گذاری فایل
                shop_id = "general"
                if '/seller/' in url:
                    parts = url.split('/seller/')
                    if len(parts) > 1:
                        shop_id = parts[1].split('/')[0]
                
                save_to_csv(all_products, shop_id)
                
                elapsed = round(time.time() - start_time, 2)
                log_header("🎉 SCRAPING COMPLETE")
                log_success(f"Total New Products: {len(all_products)}")
                log_info(f"Skipped/Duplicates/Unavailable: {skipped_count}")
                log_info(f"Time Taken: {elapsed} seconds")
                
                log_header("📋 SAMPLE DATA")
                for i, product in enumerate(all_products[:3], 1):
                    print(f"\n{Colors.BOLD}Product {i}:{Colors.RESET}")
                    print(f"  {Colors.CYAN}Name:{Colors.RESET} {product['name']}")
                    print(f"  {Colors.CYAN}Price:{Colors.RESET} {product['price']}")
                    print(f"  {Colors.CYAN}Vendor:{Colors.RESET} {product['vendor']}")
                    print(f"  {Colors.CYAN}Images:{Colors.RESET} {len(product['specs'].get('images_urls', []))} found")
                    print(f"  {Colors.CYAN}Link:{Colors.RESET} {product['link']}")
            else:
                log_warning("No new products to save.")
                
        except Exception as e:
            log_error(f"Fatal Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()
            log_info("Browser closed")
            log_header("✨ DONE")

if __name__ == "__main__":
    try:
        asyncio.run(scrape_snappshop())
    except KeyboardInterrupt:
        log_warning("\nScraping cancelled by user")
    except Exception as e:
        log_error(f"Unexpected error: {e}")