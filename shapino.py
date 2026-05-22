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
OUTPUT_FOLDER = 'shopino_output'
MAX_SCROLL_ATTEMPTS = 20
SCROLL_PAUSE = 1.0
MAX_FILE_SIZE_MB = 5
BASE_URL = "https://shopino.app"

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
    percent = (current / total) * 100 if total > 0 else 0
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
    base_name = f"shopino_{shop_name}" if shop_name else "shopino_products"
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
    return """
    () => {
        const links = [];
        const linksEls = document.querySelectorAll('a.product-link');
        linksEls.forEach(link => {
            const href = link.getAttribute('href');
            if (href && href.startsWith('/product/')) {
                links.push(href);
            }
        });
        return links;
    }
    """

# --- Main Scraper Logic ---
async def get_product_links(page, target_url):
    log_info(f"Navigating to: {target_url}")
    await page.goto(target_url, wait_until='domcontentloaded', timeout=30000)
    await asyncio.sleep(2)
    
    links = set()
    last_height = 0
    stable_count = 0
    
    log_info("Scrolling to load all products...")
    await page.evaluate("() => window.scrollBy(0, 500)")
    await asyncio.sleep(SCROLL_PAUSE)
    
    while stable_count < MAX_SCROLL_ATTEMPTS:
        current_links = await page.evaluate(get_product_links_js())
        for link in current_links:
            if link.startswith('/'):
                full_link = f"{BASE_URL}{link}"
            else:
                full_link = link
            links.add(full_link)
        
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
    if product_url in existing_links:
        return None
    
    try:
        # تغییر مهم: استفاده از domcontentloaded به جای networkidle برای جلوگیری از Timeout
        await page.goto(product_url, wait_until='domcontentloaded', timeout=15000)
        
        # صبر می‌کنیم تا تصویر یا قیمت لود شود (نشانه لود شدن صفحه)
        # اگر این المان‌ها لود نشدند، صفحه کامل لود نشده
        try:
            await page.wait_for_selector('img[src*="shopino.app"]', timeout=5000)
        except:
            log_warning(f"Image not found for {product_url}, skipping.")
            return None

        # 1. Extract Name
        name = "نام محصول نامشخص"
        try:
            name_el = await page.query_selector('h1.text-label-x-large')
            if name_el:
                raw_name = await name_el.inner_text()
                if "|" in raw_name:
                    name = raw_name.split("|")[0].strip()
                else:
                    name = raw_name.strip()
        except Exception:
            pass

        # 2. Extract Price
        price = "0"
        try:
            price_el = await page.query_selector('span.text-label-large')
            if price_el:
                raw_price = await price_el.inner_text()
                price = "".join(c for c in raw_price if c.isdigit() or c == ',')
        except Exception:
            pass

        # 3. Extract Image (لینک مستقیم)
        image = ""
        try:
            # اول اسلایدر اصلی را چک می‌کنیم
            img_el = await page.query_selector('div.slider-viewport img')
            if img_el:
                image = await img_el.get_attribute('src')
            else:
                # فال‌بک به سایر تصاویر
                img_el = await page.query_selector('img[src*="shopino.app"]')
                if img_el:
                    image = await img_el.get_attribute('src')
            
            # اطمینان از اینکه لینک کامل است
            if image and not image.startswith('http'):
                image = f"{BASE_URL}{image}"
                
        except Exception:
            pass

        # 4. Extract Specs
        specs_dict = {}
        try:
            caption_text = await page.inner_text('div.caption')
            import re
            
            color_match = re.search(r'رنگبندی[：:]\s*(.*)', caption_text)
            if color_match:
                raw_colors = color_match.group(1).strip()
                specs_dict['colors'] = [c.strip() for c in re.split(r'[،,]', raw_colors) if c.strip()]
            
            size_match = re.search(r'سایزبندی[：:]\s*(.*)', caption_text)
            if size_match:
                raw_sizes = size_match.group(1).strip()
                specs_dict['sizes'] = [s.strip() for s in re.split(r'[،,]', raw_sizes) if s.strip()]
            else:
                size_match = re.search(r'سایز\s*:?\s*(.*)', caption_text)
                if size_match:
                    specs_dict['sizes'] = [size_match.group(1).strip()]

            material_match = re.search(r'جنس[：:]\s*(.*)', caption_text)
            if material_match:
                specs_dict['material'] = material_match.group(1).strip()
            elif 'جنس:' in caption_text or 'جنس :' in caption_text:
                mat_text = caption_text.split('جنس:')[1].split('<br>')[0].strip()
                specs_dict['material'] = mat_text
                
        except Exception:
            pass

        # 5. Extract Shop Name
        shop_name = "Unknown Shop"
        try:
            if '/shops/' in product_url:
                shop_id = product_url.split('/shops/')[1].split('/')[0]
                shop_name = f"Shopino Shop {shop_id}"
            
            shop_el = await page.query_selector('a.shop-info span')
            if shop_el:
                shop_name = await shop_el.inner_text()
        except Exception:
            pass

        product_data = {
            'name': name,
            'price': price,
            'link': product_url,
            'image': image, # لینک مستقیم
            'specs': specs_dict,
            'vendor': shop_name
        }
        
        if is_duplicate(product_data, existing_hashes):
            return None
            
        log_success(f"Extracted: {name[:30]}... | Price: {price}")
        return product_data
        
    except PlaywrightTimeoutError:
        log_warning(f"Timeout for: {product_url}")
        return None
    except Exception as e:
        log_error(f"Error extracting {product_url}: {str(e)[:50]}")
        return None

async def scrape_shopino_detailed():
    log_header("🚀 SHOPINO ADVANCED SCRAPER (FIXED TIMEOUT)")
    
    url = input(f"\n{Colors.BOLD}Enter Shopino Shop URL:{Colors.RESET} ").strip()
    
    if not url.startswith("http"):
        log_error("Invalid URL.")
        return
        
    ensure_output_folder()
    existing_hashes, existing_links = get_existing_products()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True, 
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
        )
        
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        log_info("Browser launched")
        start_time = time.time()
        
        try:
            log_header("📜 COLLECTING PRODUCT LINKS")
            product_links = await get_product_links(page, url)
            
            if not product_links:
                log_error("No products found on the page.")
                await browser.close()
                return
            
            log_success(f"Found {len(product_links)} product links")
            
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
                
                await asyncio.sleep(0.3)
                
                if idx % 10 == 0:
                    log_progress(idx, len(product_links), f"({len(all_products)} new)")
            
            if all_products:
                log_header("💾 SAVING RESULTS")
                
                shop_id = "general"
                if '/shops/' in url:
                    shop_id = url.split('/shops/')[-1].split('/')[0]
                
                save_to_csv(all_products, shop_id)
                
                elapsed = round(time.time() - start_time, 2)
                
                log_header("🎉 SCRAPING COMPLETE")
                log_success(f"Total New Products: {len(all_products)}")
                log_info(f"Skipped/Duplicates: {skipped_count}")
                log_info(f"Time Taken: {elapsed} seconds")
                
                log_header("📋 SAMPLE DATA")
                for i, product in enumerate(all_products[:3], 1):
                    print(f"\n{Colors.BOLD}Product {i}:{Colors.RESET}")
                    print(f"  {Colors.CYAN}Name:{Colors.RESET} {product['name']}")
                    print(f"  {Colors.CYAN}Price:{Colors.RESET} {product['price']}")
                    print(f"  {Colors.CYAN}Vendor:{Colors.RESET} {product['vendor']}")
                    print(f"  {Colors.CYAN}Link:{Colors.RESET} {product['link']}")
                    print(f"  {Colors.CYAN}Image:{Colors.RESET} {product['image']}")
                    if product['specs']:
                        specs_preview = json.dumps(product['specs'], ensure_ascii=False)[:100]
                        print(f"  {Colors.CYAN}Specs:{Colors.RESET} {specs_preview}...")
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
        asyncio.run(scrape_shopino_detailed())
    except KeyboardInterrupt:
        log_warning("\nScraping cancelled by user")
    except Exception as e:
        log_error(f"Unexpected error: {e}")