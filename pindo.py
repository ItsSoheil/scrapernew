import asyncio
import csv
import os
import json
import time
import hashlib
import re
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# --- Configuration ---
OUTPUT_FOLDER = 'pindo_full_output'
MAX_SCROLL_ATTEMPTS = 50  # افزایش تعداد تلاش برای اطمینان از لود شدن همه چیز
SCROLL_PAUSE = 1.5
MAX_FILE_SIZE_MB = 10
BASE_URL = "https://www.pindo.ir"
HEADLESS = True

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
    # اصلاح Regex برای جلوگیری از خطای bad character range
    # فقط حروف انگلیسی، اعداد و خط تیره را نگه می‌داریم، بقیه را خط تیره می‌کنیم
    if not shop_name:
        safe_name = "general"
    else:
        # تبدیل نام به حروف کوچک انگلیسی و جایگزینی کاراکترهای خاص
        safe_name = re.sub(r'[^a-zA-Z0-9\s]', '', shop_name).replace(' ', '_').lower()
        # اگر خالی شد
        if not safe_name:
            safe_name = "shop"
            
    base_name = f"pindo_{safe_name}"
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
    if not product.get('name') or not product.get('price'):
        return False
        
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
    
    fieldnames = ['name', 'price', 'link', 'image', 'description', 'specs_json', 'vendor', 'scraped_at']
    
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
                if 'description' in row:
                    row['description'] = row['description'].replace('\n', ' ').replace(',', ';').strip()
                row['scraped_at'] = datetime.now().isoformat()
                writer.writerow(row)
        
        size_mb = get_file_size_mb(csv_file)
        log_success(f"Saved {len(data)} products to {csv_file} (Size: {size_mb:.2f}MB)")
    except Exception as e:
        log_error(f"Failed to save CSV: {str(e)[:100]}")

# --- JavaScript Extractors for Pindo ---
def get_product_links_js():
    return """
    () => {
        const links = [];
        // جستجوی تمام آرتیکل‌هایی که لینک محصول دارند
        const articles = document.querySelectorAll('article');
        
        articles.forEach(article => {
            // پیدا کردن لینک داخل آرتیکل
            const linkEl = article.querySelector('a[href^="/ads/"]');
            if (linkEl && linkEl.href) {
                links.push(linkEl.href);
            }
        });

        // اگر روش بالا کار نکرد، تمام لینک‌های /ads/ را بگیر
        if (links.length === 0) {
            const allLinks = document.querySelectorAll('a[href*="/ads/"]');
            allLinks.forEach(a => links.push(a.href));
        }
        
        return links;
    }
    """

async def extract_product_details(page, product_url, existing_links, existing_hashes):
    if product_url in existing_links:
        return None
        
    retry_count = 0
    max_retries = 2
    
    while retry_count <= max_retries:
        try:
            await page.goto(product_url, wait_until='domcontentloaded', timeout=20000)
            await asyncio.sleep(2) 
            
            # 1. Extract Name
            name = "نام محصول نامشخص"
            try:
                selectors = [
                    'h1.t-text-h5-c', 
                    'h1.color-800',
                    'h1[class*="title"]',
                    'h1'
                ]
                for sel in selectors:
                    el = await page.query_selector(sel)
                    if el:
                        text = await el.inner_text()
                        if text and len(text) > 5:
                            name = text.strip()
                            break
            except Exception as e:
                log_warning(f"Error extracting name: {e}")

            # 2. Extract Price
            price = "0"
            try:
                price_selectors = [
                    'div.t-text-h5',
                    'div.t-typo-title-s',
                    'span[class*="price"]',
                    'div[class*="price"]'
                ]
                
                found_price = False
                for sel in price_selectors:
                    els = await page.query_selector_all(sel)
                    for el in els:
                        text = await el.inner_text()
                        clean_text = re.sub(r'[^\d,]', '', text)
                        if clean_text and len(clean_text) > 3:
                            price = clean_text
                            found_price = True
                            break
                    if found_price:
                        break
            except Exception as e:
                log_warning(f"Error extracting price: {e}")

            # 3. Extract Image
            image = ""
            try:
                img_selectors = [
                    'img[data-nimg="fill"]',
                    'img.t-object-cover',
                    'img[src*="dkstatics"]'
                ]
                for sel in img_selectors:
                    el = await page.query_selector(sel)
                    if el:
                        src = await el.get_attribute('src')
                        if src and 'http' in src:
                            image = src
                            break
            except Exception as e:
                log_warning(f"Error extracting image: {e}")

            # 4. Extract Description
            description = ""
            try:
                desc_selectors = [
                    'p.t-whitespace-pre-line',
                    'div[class*="description"] p',
                    'div[class*="text"] p'
                ]
                for sel in desc_selectors:
                    el = await page.query_selector(sel)
                    if el:
                        desc = await el.inner_text()
                        if desc and len(desc) > 10:
                            description = desc.strip()
                            break
            except Exception as e:
                log_warning(f"Error extracting description: {e}")

            # 5. Extract Vendor
            shop_name = "نامشخص"
            try:
                shop_link = await page.query_selector('a[href*="/stores/"]')
                if shop_link:
                    shop_name = (await shop_link.inner_text()).strip()
            except Exception as e:
                log_warning(f"Error extracting vendor: {e}")

            # 6. Extract Specs
            specs_dict = {}
            try:
                specs_section = await page.query_selector('div[class*="specifications"], div[class*="specs"]')
                if specs_section:
                    text = await specs_section.inner_text()
                    lines = text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if ':' in line:
                            key, val = line.split(':', 1)
                            specs_dict[key.strip()] = val.strip()
            except Exception as e:
                log_warning(f"Error extracting specs: {e}")
            
            if name == "نام محصول نامشخص" and price == "0":
                retry_count += 1
                if retry_count <= max_retries:
                    log_warning(f"Data incomplete for {product_url}, retrying ({retry_count}/{max_retries})...")
                    await asyncio.sleep(2)
                    continue
                else:
                    log_error(f"Failed to extract data after retries: {product_url}")
                    return None

            product_data = {
                'name': name,
                'price': price,
                'link': product_url,
                'image': image,
                'description': description,
                'specs': specs_dict,
                'vendor': shop_name
            }
            
            if is_duplicate(product_data, existing_hashes):
                return None
                
            log_success(f"Extracted: {name[:30]}... | Price: {price}")
            return product_data

        except PlaywrightTimeoutError:
            retry_count += 1
            if retry_count <= max_retries:
                log_warning(f"Timeout for {product_url}, retrying...")
                await asyncio.sleep(2)
                continue
            else:
                log_error(f"Final Timeout for: {product_url}")
                return None
        except Exception as e:
            retry_count += 1
            if retry_count <= max_retries:
                log_warning(f"Error for {product_url}: {e}, retrying...")
                await asyncio.sleep(2)
                continue
            else:
                log_error(f"Fatal Error for {product_url}: {e}")
                return None

    return None

async def get_product_links_robust(page, target_url):
    log_info(f"Navigating to: {target_url}")
    await page.goto(target_url, wait_until='domcontentloaded', timeout=30000)
    await asyncio.sleep(3)
    
    links = set()
    last_height = 0
    stable_count = 0
    
    log_info("Starting robust scrolling process...")
    
    # چک کردن اینکه آیا در صفحه لیست هستیم
    if '/ads/' in target_url:
        log_warning("URL is a product page, not a list page. Extracting single link.")
        links.add(target_url)
        return list(links)

    # اسکرول اولیه
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
            await page.evaluate("() => window.scrollBy(0, 600)")
            await asyncio.sleep(SCROLL_PAUSE)
            log_progress(len(links), len(links) + 5, f"Found {len(links)} products so far")
        else:
            log_success("End of page reached or stable.")
            break
            
    return list(links)

async def scrape_pindo_full():
    log_header("🚀 PINDO ROBUST SCRAPER (FIXED TIMEOUTS & SCROLL)")
    
    url = input(f"\n{Colors.BOLD}Enter Pindo List URL:{Colors.RESET} ").strip()
    
    if not url.startswith("http"):
        log_error("Invalid URL.")
        return
        
    ensure_output_folder()
    existing_hashes, existing_links = get_existing_products()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=HEADLESS, 
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process'
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='fa-IR',
            timezone_id='Asia/Tehran'
        )
        page = await context.new_page()
        
        log_info("Browser launched with robust settings")
        start_time = time.time()
        
        try:
            # Step 1: Get Links
            log_header("📜 COLLECTING PRODUCT LINKS")
            product_links = await get_product_links_robust(page, url)
            
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
                
                await asyncio.sleep(0.5)
                
                if idx % 10 == 0:
                    log_progress(idx, len(product_links), f"({len(all_products)} new)")
            
            # Step 3: Save
            if all_products:
                log_header("💾 SAVING RESULTS")
                
                shop_id = "general"
                if '/stores/' in url:
                    shop_id = url.split('/stores/')[1].split('/')[0]
                
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
                    if product['description']:
                        print(f"  {Colors.CYAN}Desc:{Colors.RESET} {product['description'][:50]}...")
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
        asyncio.run(scrape_pindo_full())
    except KeyboardInterrupt:
        log_warning("\nScraping cancelled by user")
    except Exception as e:
        log_error(f"Unexpected error: {e}")