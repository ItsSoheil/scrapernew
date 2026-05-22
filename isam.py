import asyncio
import csv
import os
import json
import time
import hashlib
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# Configuration
OUTPUT_FOLDER = 'output_esam_full'
MAX_SCROLL_ATTEMPTS = 15
SCROLL_PAUSE = 0.8
MAX_FILE_SIZE_MB = 5

# ANSI Colors
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    CYAN = '\033[36m'
    BG_BLUE = '\033[44m'
    WHITE = '\033[37m'

def log_header(text):
    print(f"\n{Colors.BOLD}{Colors.BG_BLUE}{Colors.WHITE} {text} {Colors.RESET}")

def log_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def log_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def log_info(text):
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.RESET}")

def log_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

def log_progress(current, total, text=""):
    percent = (current / total) * 100
    bar_length = 30
    filled = int(bar_length * current / total)
    bar = "█" * filled + "░" * (bar_length - filled)
    print(f"{Colors.CYAN}[{bar}] {current}/{total} ({percent:.1f}%) {text}{Colors.RESET}")

def ensure_output_folder():
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
        log_success(f"Created output folder: {OUTPUT_FOLDER}")

def get_csv_filename(shop_name=""):
    base_name = f"esam_full_{shop_name}" if shop_name else "esam_full_products"
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
        log_info(f"Loaded {len(existing_links)} existing products from {csv_file}")
    except Exception as e:
        log_warning(f"Could not read existing products: {str(e)[:50]}")
    return existing_hashes, existing_links

def is_duplicate(product, existing_hashes):
    unique_str = f"{product['name']}_{product['price']}"
    hash_obj = hashlib.md5(unique_str.encode())
    return hash_obj.hexdigest() in existing_hashes

def save_to_csv(data, shop_name=""):
    ensure_output_folder()
    if not data:
        return
    
    csv_file = get_csv_filename(shop_name)
    
    # Check file size for rotation
    if os.path.exists(csv_file) and os.path.getsize(csv_file) > MAX_FILE_SIZE_MB * 1024 * 1024:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_path = csv_file.replace('.csv', '')
        csv_file = f"{base_path}_{timestamp}.csv"
        log_warning(f"CSV file too large. Creating new file: {csv_file}")

    fieldnames = [
        'name', 'price', 'original_price', 'discount_percent', 'link', 
        'product_code', 'image', 'thumbnails', 'specs_json', 'description', 
        'seller_name', 'seller_link', 'scraped_at'
    ]
    
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
                if 'thumbnails' in row and isinstance(row['thumbnails'], list):
                    row['thumbnails'] = json.dumps(row['thumbnails'], ensure_ascii=False)
                if 'description' in row:
                    row['description'] = row['description'].replace('\n', ' ').strip()
                
                row['scraped_at'] = datetime.now().isoformat()
                writer.writerow(row)
        
        size_mb = os.path.getsize(csv_file) / (1024 * 1024)
        log_success(f"Saved {len(data)} products to {csv_file} (Size: {size_mb:.2f}MB)")
        
    except Exception as e:
        log_error(f"Failed to save CSV: {str(e)[:100]}")

async def get_product_links(page, target_url):
    log_info(f"Navigating to: {target_url}")
    await page.goto(target_url, wait_until='domcontentloaded', timeout=30000)
    await asyncio.sleep(2)
    
    links = set()
    last_height = 0
    stable_count = 0
    
    log_info("Scrolling to load all products...")
    product_selector = 'article.productCard_product-card__fHEnS'
    
    while stable_count < MAX_SCROLL_ATTEMPTS:
        product_elements = await page.query_selector_all(product_selector)
        
        for el in product_elements:
            link_el = await el.query_selector('a')
            if link_el:
                href = await link_el.get_attribute('href')
                if href and not href.startswith('javascript'):
                    if href.startswith('/'):
                        full_link = f"https://esam.ir{href}"
                    else:
                        full_link = href
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
        else:
            log_success("End of page reached")
            break
            
    return list(links)

async def extract_product_details(page, product_url, seen_links, existing_hashes, existing_links):
    if product_url in seen_links:
        return None
    if product_url in existing_links:
        return None
    
    seen_links.add(product_url)
    
    try:
        await page.goto(product_url, wait_until='domcontentloaded', timeout=15000)
        await asyncio.sleep(1) # Extra wait for dynamic content
        
        # 1. Name
        name = "Unknown Product"
        name_el = await page.query_selector('h1.product_heading__sK_4i')
        if name_el:
            name = (await name_el.inner_text()).strip()
            
        # 2. Product Code
        product_code = ""
        code_el = await page.query_selector('[class*="position-relative"] span') # Heuristic for "شماره کالا"
        if code_el:
            text = await code_el.inner_text()
            if "شماره کالا" in text:
                # Extract number from "شماره کالا: 38014918"
                parts = text.split(":")
                if len(parts) > 1:
                    product_code = parts[-1].strip()
        else:
            # Fallback: look for data-iditem in the main container if available
            main_container = await page.query_selector('article.productCard_product-card__fHEnS') # This is from list view, might not be here
            # Try finding it in meta or specific divs
            # Based on HTML: <span class="text-sm text-secondary-emphasis position-relative">شماره کالا: 38014918</span>
            code_selector = await page.query_selector('span.text-secondary-emphasis.position-relative')
            if code_selector:
                txt = await code_selector.inner_text()
                if ":" in txt:
                    product_code = txt.split(":")[1].strip()

        # 3. Price & Discount
        original_price = ""
        current_price = ""
        discount_percent = ""
        
        # Original Price (Strikethrough)
        del_el = await page.query_selector('del.text-sm')
        if del_el:
            original_price = (await del_el.inner_text()).replace('تومان', '').replace(',', '').strip()
            
        # Current Price
        price_p_el = await page.query_selector('p.text-md.fw-bold.mb-0')
        if price_p_el:
            current_price = (await price_p_el.inner_text()).replace('تومان', '').replace(',', '').strip()
            
        # Discount Badge
        discount_el = await page.query_selector('span.bg-danger.px-2')
        if discount_el:
            discount_percent = (await discount_el.inner_text()).replace('%', '').strip()

        price_display = f"{current_price} تومان"
        if original_price:
            price_display += f" (اصلی: {original_price})"
            
        # 4. Images
        main_image = ""
        img_main_el = await page.query_selector('img.productImage_product-main-image__bulWS')
        if img_main_el:
            main_image = await img_main_el.get_attribute('src')
            
        thumbnails = []
        thumbs_el = await page.query_selector_all('img.productImage_mini-image__XGnED')
        for thumb in thumbs_el:
            src = await thumb.get_attribute('src')
            if src:
                thumbnails.append(src)

        # 5. Seller Info
        seller_name = ""
        seller_link = ""
        seller_el = await page.query_selector('a[href*="orderusername"]')
        if seller_el:
            seller_name = await seller_el.inner_text()
            seller_link = await seller_el.get_attribute('href')
            if seller_link and not seller_link.startswith('http'):
                seller_link = f"https://esam.ir{seller_link}"

        # 6. Specs (Attributes)
        specs_dict = await page.evaluate("""
        () => {
            const result = {};
            const container = document.querySelector('.tabDetail_product__details__FdTzJ');
            if (!container) return result;
            
            const table = container.querySelector('table.table_table__UCqXF');
            if (!table) return result;

            const rows = table.querySelectorAll('tbody tr');
            rows.forEach(row => {
                const cells = row.querySelectorAll('td');
                if (cells.length >= 2) {
                    const key = cells[0].innerText.trim();
                    const valueCell = cells[1];
                    const link = valueCell.querySelector('a');
                    const value = link ? link.innerText.trim() : valueCell.innerText.trim();
                    if (key && value) {
                        result[key] = value;
                    }
                }
            });
            return result;
        }
        """)

        # 7. Description (More Information Tab)
        description = ""
        # Note: In SPA, the description might be in the same div but hidden or in a different tabpane
        # Based on HTML: #product-tabs-tabpane-moreInformation
        desc_container = await page.query_selector('#product-tabs-tabpane-moreInformation .tabDetail_product__details__FdTzJ')
        if desc_container:
            # Get the text content, skipping the title "توضیحات بیشتر"
            paragraphs = await desc_container.query_selector_all('p')
            desc_texts = []
            for p in paragraphs:
                txt = await p.inner_text()
                if txt and "توضیحات بیشتر" not in txt:
                    desc_texts.append(txt)
            description = "\n".join(desc_texts)
            
        product_data = {
            'name': name,
            'price': price_display,
            'original_price': original_price,
            'discount_percent': discount_percent,
            'link': product_url,
            'product_code': product_code,
            'image': main_image,
            'thumbnails': thumbnails,
            'specs': specs_dict,
            'description': description,
            'seller_name': seller_name,
            'seller_link': seller_link,
            'scraped_at': datetime.now().isoformat()
        }
        
        if is_duplicate(product_data, existing_hashes):
            return None
        
        log_success(f"Extracted Full Data: {name[:30]}...")
        return product_data
        
    except PlaywrightTimeoutError:
        log_warning(f"Timeout for: {product_url}")
        return None
    except Exception as e:
        log_error(f"Error extracting {product_url}: {str(e)[:50]}")
        return None

async def scrape_esam_full():
    log_header("🚀 ESAM.IR FULL DATA SCRAPER")
    
    url = input(f"\n{Colors.BOLD}Enter Esam Shop URL:{Colors.RESET} ").strip()
    
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
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        start_time = time.time()
        
        try:
            log_header("📜 COLLECTING PRODUCT LINKS")
            product_links = await get_product_links(page, url)
            
            if not product_links:
                log_error("No products found.")
                await browser.close()
                return
            
            log_success(f"Found {len(product_links)} product links")
            
            log_header("🔍 EXTRACTING FULL DETAILS")
            all_products = []
            seen_links = set()
            skipped_count = 0
            
            for idx, link in enumerate(product_links, 1):
                print(f"{Colors.DIM}[{idx}/{len(product_links)}]{Colors.RESET} ", end="")
                
                product_data = await extract_product_details(
                    page, link, seen_links, existing_hashes, existing_links
                )
                
                if product_data:
                    all_products.append(product_data)
                else:
                    skipped_count += 1
                
                await asyncio.sleep(0.3)
                
                if idx % 10 == 0:
                    log_progress(idx, len(product_links), f"({len(all_products)} new)")
            
            if all_products:
                log_header("💾 SAVING RESULTS")
                shop_name = ""
                if 'orderusername=' in url:
                    shop_name = url.split('orderusername=')[-1].split('&')[0]
                elif '/shop/' in url:
                    shop_name = url.split('/shop/')[-1].split('/')[0]
                if not shop_name:
                    shop_name = "general"
                    
                save_to_csv(all_products, shop_name)
                
                elapsed = round(time.time() - start_time, 2)
                
                log_header("🎉 SCRAPING COMPLETE")
                log_success(f"Total New Products: {len(all_products)}")
                log_info(f"Duplicate/Existing: {skipped_count}")
                log_info(f"Time Taken: {elapsed} seconds")
                
                # Sample Output
                log_header("📋 SAMPLE DATA (First Product)")
                if all_products:
                    p = all_products[0]
                    print(f"\n{Colors.BOLD}Name:{Colors.RESET} {p['name']}")
                    print(f"{Colors.BOLD}Price:{Colors.RESET} {p['price']}")
                    print(f"{Colors.BOLD}Discount:{Colors.RESET} {p['discount_percent']}%")
                    print(f"{Colors.BOLD}Seller:{Colors.RESET} {p['seller_name']}")
                    print(f"{Colors.BOLD}Code:{Colors.RESET} {p['product_code']}")
                    print(f"{Colors.BOLD}Specs:{Colors.RESET} {json.dumps(p['specs'], ensure_ascii=False)[:100]}...")
                    print(f"{Colors.BOLD}Desc:{Colors.RESET} {p['description'][:100]}...")
                    
            else:
                log_warning("No new products to save.")
                
        except Exception as e:
            log_error(f"Fatal Error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await browser.close()
            log_info("Browser closed")

if __name__ == "__main__":
    try:
        asyncio.run(scrape_esam_full())
    except KeyboardInterrupt:
        log_warning("\nScraping cancelled by user")
    except Exception as e:
        log_error(f"Unexpected error: {e}")