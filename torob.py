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
OUTPUT_FOLDER = 'output'
MAX_SCROLL_ATTEMPTS = 10
SCROLL_PAUSE = 0.5
MAX_FILE_SIZE_MB = 5
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# ANSI Colors for prettier logging
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Foreground
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Background
    BG_BLUE = '\033[44m'
    BG_GREEN = '\033[42m'

def log_header(text):
    """Log with header style."""
    print(f"\n{Colors.BOLD}{Colors.BG_BLUE}{Colors.WHITE} {text} {Colors.RESET}")

def log_success(text):
    """Log success message."""
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def log_error(text):
    """Log error message."""
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def log_info(text):
    """Log info message."""
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.RESET}")

def log_warning(text):
    """Log warning message."""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

def log_progress(current, total, text=""):
    """Log progress."""
    percent = (current / total) * 100
    bar_length = 30
    filled = int(bar_length * current / total)
    bar = "█" * filled + "░" * (bar_length - filled)
    print(f"{Colors.CYAN}[{bar}] {current}/{total} ({percent:.1f}%) {text}{Colors.RESET}")

def ensure_output_folder():
    """Create output directory if it doesn't exist."""
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
        log_success(f"Created output folder: {OUTPUT_FOLDER}")

def get_csv_filename(shop_name=""):
    """Return the path to the CSV file with rotation."""
    base_name = f"torob_{shop_name}" if shop_name else "torob_products"
    return os.path.join(OUTPUT_FOLDER, f"{base_name}.csv")

def get_existing_products():
    """Load existing products from CSV into a set of hashes for deduplication."""
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
                    # Store link for direct comparison
                    existing_links.add(row['link'])
                    
                    # Create hash from name + price for duplicate detection
                    if 'name' in row and 'price' in row:
                        unique_str = f"{row['name']}_{row['price']}"
                        hash_obj = hashlib.md5(unique_str.encode())
                        existing_hashes.add(hash_obj.hexdigest())
        
        log_info(f"Loaded {len(existing_links)} existing products from {csv_file}")
    except Exception as e:
        log_warning(f"Could not read existing products: {str(e)[:50]}")
    
    return existing_hashes, existing_links

def is_duplicate(product, existing_hashes):
    """Check if product is already in database."""
    unique_str = f"{product['name']}_{product['price']}"
    hash_obj = hashlib.md5(unique_str.encode())
    return hash_obj.hexdigest() in existing_hashes

def get_file_size_mb(filepath):
    """Get file size in MB."""
    if os.path.exists(filepath):
        return os.path.getsize(filepath) / (1024 * 1024)
    return 0

def get_new_csv_filename(base_filename):
    """Get a new CSV filename if current one is too large."""
    if not os.path.exists(base_filename):
        return base_filename
    
    size_mb = get_file_size_mb(base_filename)
    if size_mb < MAX_FILE_SIZE_MB:
        return base_filename
    
    # Create new file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_path = base_filename.replace('.csv', '')
    new_filename = f"{base_path}_{timestamp}.csv"
    
    log_warning(f"CSV file {base_filename} is {size_mb:.2f}MB. Creating new file: {new_filename}")
    return new_filename

def save_to_csv(data, shop_name=""):
    """Save list of product dictionaries to CSV with rotation."""
    ensure_output_folder()
    if not data:
        return

    csv_file = get_csv_filename(shop_name)
    csv_file = get_new_csv_filename(csv_file)
    
    fieldnames = ['name', 'price', 'link', 'image', 'specs_json', 'brand', 'warranty', 'scraped_at']
    
    try:
        # Check if file exists to decide on header
        file_exists = os.path.exists(csv_file)
        
        with open(csv_file, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
            
            if not file_exists:
                writer.writeheader()
            
            for row in data:
                # Convert specs dict to JSON string
                if 'specs' in row and isinstance(row['specs'], dict):
                    row['specs_json'] = json.dumps(row['specs'], ensure_ascii=False)
                    del row['specs']
                
                # Add timestamp
                row['scraped_at'] = datetime.now().isoformat()
                
                writer.writerow(row)
        
        size_mb = get_file_size_mb(csv_file)
        log_success(f"Saved {len(data)} products to {csv_file} (Size: {size_mb:.2f}MB)")
        
    except Exception as e:
        log_error(f"Failed to save CSV: {str(e)[:100]}")

def get_specs_extractor_js():
    """JavaScript function to extract specs from the DOM."""
    return """
    () => {
        const result = {};
        const container = document.querySelector('.specs-content') || 
                          document.querySelector('[class*="specs"]');
        
        if (!container) return result;

        const keySpecsContainer = container.querySelector('.key-specs-container');
        if (keySpecsContainer) {
            const pairs = keySpecsContainer.querySelectorAll('.keys-values');
            for (let i = 0; i < pairs.length; i += 2) {
                const keyEl = pairs[i];
                const valueEl = pairs[i + 1];
                
                if (keyEl && valueEl) {
                    const key = keyEl.innerText.trim();
                    const value = valueEl.innerText.trim();
                    if (key && value) {
                        result[key] = value;
                    }
                }
            }
        }

        const detailTitles = container.querySelectorAll('.detail-title');
        detailTitles.forEach((title) => {
            const key = title.innerText.trim();
            let nextEl = title.nextElementSibling;
            while (nextEl && !nextEl.classList.contains('detail-value')) {
                nextEl = nextEl.nextElementSibling;
            }
            
            if (nextEl) {
                const value = nextEl.innerText.trim();
                if (key && value) {
                    result[key] = value;
                }
            }
        });

        return result;
    }
    """

async def get_product_links(page, target_url):
    """Navigate to shop URL and scroll to load all products."""
    log_info(f"Navigating to: {target_url}")
    await page.goto(target_url, wait_until='domcontentloaded', timeout=30000)
    await asyncio.sleep(2)

    links = set()
    last_height = 0
    scroll_count = 0
    stable_count = 0

    log_info("Scrolling to load all products...")

    while stable_count < MAX_SCROLL_ATTEMPTS:
        product_links = await page.query_selector_all('a[href*="/p/"]')
        
        for link in product_links:
            href = await link.get_attribute('href')
            if href and not href.startswith('javascript'):
                if href.startswith('/'):
                    full_link = f"https://torob.com{href}"
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
            scroll_count += 1
            log_progress(len(links), len(links) + 10, f"Found {len(links)} products")
        else:
            log_success("End of page reached")
            break

    return list(links)

async def extract_product_details(page, product_url, seen_links, existing_hashes, existing_links):
    """Navigate to product page and extract details."""
    
    # Check if already processed or exists
    if product_url in seen_links:
        log_warning("Product already processed in this session")
        return None
    
    if product_url in existing_links:
        log_warning("Product already in database")
        return None
    
    seen_links.add(product_url)
    
    try:
        await page.goto(product_url, wait_until='domcontentloaded', timeout=15000)
        await asyncio.sleep(0.5)

        # Extract Name
        name = "Unknown Product"
        name_el = await page.query_selector('h1')
        if name_el:
            name = (await name_el.inner_text()).strip()
        else:
            name_el = await page.query_selector('div.Showcase_name__hrttI')
            if name_el:
                name = (await name_el.inner_text()).strip()

        # Extract Price
        price = "0"
        price_els = await page.query_selector_all('div.Showcase_buy_box_text__otYW_')
        if len(price_els) >= 2:
            price = await price_els[1].inner_text()
            
        # Extract Image
        image = ""
        img_el = await page.query_selector('img[src*="image.torob.com"]')
        if img_el:
            image = await img_el.get_attribute('src')
        
        if not image:
            img_el = await page.query_selector('img[alt*="تصویر"]')
            if img_el:
                image = await img_el.get_attribute('src')

        # Extract Specs
        specs_dict = await page.evaluate(get_specs_extractor_js())
        
        # Extract Brand and Warranty
        brand = specs_dict.pop('برند', '') or specs_dict.pop('Brand', '') or ""
        warranty = specs_dict.pop('گارانتی', '') or specs_dict.pop('Warranty', '') or ""
        
        cleaned_specs = {k: v for k, v in specs_dict.items() if v}

        product_data = {
            'name': name,
            'price': price,
            'link': product_url,
            'image': image,
            'specs': cleaned_specs,
            'brand': brand,
            'warranty': warranty
        }
        
        # Check for duplicates before returning
        if is_duplicate(product_data, existing_hashes):
            log_warning(f"Duplicate: {name[:30]}...")
            return None
        
        log_success(f"Extracted: {name[:40]}...")
        return product_data
        
    except PlaywrightTimeoutError:
        log_warning(f"Timeout for: {product_url}")
        return None
    except Exception as e:
        log_error(f"Error extracting {product_url}: {str(e)[:50]}")
        return None

async def scrape_torob_detailed():
    """Main scraper function."""
    log_header("🚀 TOROB ADVANCED SCRAPER")
    
    url = input(f"\n{Colors.BOLD}Enter Torob Shop URL:{Colors.RESET} ").strip()
    
    if not url.startswith("http"):
        log_error("Invalid URL. Please provide a full URL starting with http/https.")
        return

    ensure_output_folder()
    
    # Load existing products
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
            # Step 1: Get all links
            log_header("📜 COLLECTING PRODUCT LINKS")
            product_links = await get_product_links(page, url)
            
            if not product_links:
                log_error("No products found on the page.")
                await browser.close()
                return
            
            log_success(f"Found {len(product_links)} product links")
            
            # Step 2: Extract details
            log_header("🔍 EXTRACTING PRODUCT DETAILS")
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
                    log_progress(idx, len(product_links), f"({len(all_products)} new products)")
            
            # Step 3: Save to CSV
            if all_products:
                log_header("💾 SAVING RESULTS")
                
                # Extract shop name from URL for filename
                shop_name = url.split('/shop/')[-1].split('/')[0] if '/shop/' in url else "general"
                save_to_csv(all_products, shop_name)
                
                elapsed = round(time.time() - start_time, 2)
                
                log_header("🎉 SCRAPING COMPLETE")
                log_success(f"Total New Products: {len(all_products)}")
                log_info(f"Duplicate/Existing: {skipped_count}")
                log_info(f"Time Taken: {elapsed} seconds")
                log_info(f"Average Speed: {len(product_links)/elapsed:.2f} products/sec")
                
                # Show sample
                log_header("📋 SAMPLE DATA (First 3 Products)")
                for i, product in enumerate(all_products[:3], 1):
                    print(f"\n{Colors.BOLD}Product {i}:{Colors.RESET}")
                    print(f"  {Colors.CYAN}Name:{Colors.RESET} {product['name']}")
                    print(f"  {Colors.CYAN}Price:{Colors.RESET} {product['price']}")
                    print(f"  {Colors.CYAN}Brand:{Colors.RESET} {product['brand']}")
                    print(f"  {Colors.CYAN}Link:{Colors.RESET} {product['link'][:50]}...")
                    if product['specs']:
                        specs_preview = json.dumps(product['specs'], ensure_ascii=False)[:80]
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
        asyncio.run(scrape_torob_detailed())
    except KeyboardInterrupt:
        log_warning("\nScraping cancelled by user")
    except Exception as e:
        log_error(f"Unexpected error: {e}")
