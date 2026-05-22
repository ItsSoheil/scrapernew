import asyncio
import csv
import re
from playwright.async_api import async_playwright
import time
from queue import Queue
from threading import Thread
import sys

# --- Configuration ---
OUTPUT_CSV = "esam_categories_complete.csv"
BASE_URL = "https://esam.ir/categories"
MAX_CONCURRENT_PAGES = 30  # ↑ بیشتر
TIMEOUT = 3000  # ↓ کمتر
MAX_RETRIES = 1
DELAY_BETWEEN_REQUESTS = 0

class ProgressTracker:
    def __init__(self):
        self.processed = 0
        self.errors = 0
        self.start_time = time.time()
        self.processed_ids = set()

tracker = ProgressTracker()

# --- CSV Writer Thread ---
csv_queue = Queue(maxsize=1000)
csv_stop_event = False

def csv_writer_thread():
    """نوشتن CSV بدون هیچ لاگ"""
    global csv_stop_event
    
    try:
        with open(OUTPUT_CSV, 'w', encoding='utf-8-sig', newline='', buffering=10000) as f:
            writer = csv.DictWriter(f, fieldnames=['title', 'full_path'])
            writer.writeheader()
            
            batch = []
            
            while True:
                try:
                    item = csv_queue.get(timeout=0.5)
                    
                    if item is None:
                        if batch:
                            writer.writerows(batch)
                            f.flush()
                        break
                    
                    batch.append(item)
                    
                    if len(batch) >= 200:  # ↑ بیشتر
                        writer.writerows(batch)
                        batch = []
                        
                except:
                    if batch:
                        writer.writerows(batch)
                        batch = []
                    if csv_stop_event:
                        break
    except:
        pass

def extract_category_id(url):
    """استخراج ID بدون try/except اضافی"""
    match = re.search(r'/categories/(\d+)', url)
    return match.group(1) if match else None

async def extract_subcategories_from_page(page):
    """استخراج بدون هیچ تاخیری"""
    try:
        await asyncio.wait_for(
            page.wait_for_selector('a[href*="/categories/"]', timeout=TIMEOUT),
            timeout=TIMEOUT/1000
        )
    except:
        return []
    
    try:
        category_links = await page.query_selector_all('a[href*="/categories/"]')
    except:
        return []
    
    subcategories = []
    seen_ids = set()
    
    for link in category_links:
        try:
            href = await link.get_attribute('href')
            text = (await link.inner_text()).strip()
            
            if len(text) < 2 or '/categories/' not in href:
                continue
            
            cat_id = extract_category_id(href)
            if not cat_id or cat_id in seen_ids or cat_id in tracker.processed_ids:
                continue
            
            seen_ids.add(cat_id)
            
            if not href.startswith('http'):
                href = f"https://esam.ir{href}"
            
            subcategories.append({
                'id': cat_id,
                'title': text,
                'link': href
            })
        except:
            continue
    
    return subcategories

async def crawl_category_recursive(page, url, parent_path, depth=0, semaphore=None):
    """Recursive بدون تاخیر"""
    if depth > 6:
        return
    
    async with semaphore:
        try:
            await asyncio.wait_for(
                page.goto(url, wait_until='domcontentloaded'),
                timeout=TIMEOUT/1000
            )
        except:
            return
        
        subcats = await extract_subcategories_from_page(page)
        
        if not subcats:
            tracker.processed += 1
            return
        
        for subcat in subcats:
            cat_id = subcat['id']
            cat_title = subcat['title']
            cat_link = subcat['link']
            
            if cat_id in tracker.processed_ids:
                continue
            
            tracker.processed_ids.add(cat_id)
            current_path = f"{parent_path} > {cat_title}" if parent_path else cat_title
            
            # نوشتن بلا تاخیر
            try:
                csv_queue.put_nowait({
                    'title': cat_title,
                    'full_path': current_path
                })
            except:
                csv_queue.put({
                    'title': cat_title,
                    'full_path': current_path
                })
            
            tracker.processed += 1
            
            # Recursive
            await crawl_category_recursive(
                page, cat_link, current_path, depth + 1, semaphore
            )

async def main():
    global csv_stop_event
    
    writer_thread = Thread(target=csv_writer_thread, daemon=True)
    writer_thread.start()
    
    browser = None
    start_time = time.time()
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-gpu',
                    '--disable-web-resources',
                    '--disable-extensions',
                    '--disable-sync',  # ✨ جدید
                    '--disable-background-networking',  # ✨ جدید
                    '--disable-client-side-phishing-detection',  # ✨ جدید
                    '--disable-component-extensions-with-background-pages'  # ✨ جدید
                ]
            )
            
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
                ignore_https_errors=True,
                extra_http_headers={'DNT': '1'}
            )
            
            context.set_default_timeout(TIMEOUT)
            context.set_default_navigation_timeout(TIMEOUT)
            
            semaphore = asyncio.Semaphore(MAX_CONCURRENT_PAGES)
            
            main_page = await context.new_page()
            
            try:
                await asyncio.wait_for(
                    main_page.goto(BASE_URL, wait_until='domcontentloaded'),
                    timeout=TIMEOUT/1000
                )
            except:
                csv_stop_event = True
                csv_queue.put(None)
                await context.close()
                return
            
            root_cats = await extract_subcategories_from_page(main_page)
            
            if not root_cats:
                csv_stop_event = True
                csv_queue.put(None)
                await context.close()
                return
            
            # ایجاد صفحات
            all_pages = [main_page]
            for _ in range(MAX_CONCURRENT_PAGES - 1):
                try:
                    page = await context.new_page()
                    all_pages.append(page)
                except:
                    pass
            
            # Processing
            for i, root_cat in enumerate(root_cats):
                cat_id = root_cat['id']
                if cat_id in tracker.processed_ids:
                    continue
                
                tracker.processed_ids.add(cat_id)
                page = all_pages[i % len(all_pages)]
                
                # نوشتن دسته اصلی
                try:
                    csv_queue.put_nowait({
                        'title': root_cat['title'],
                        'full_path': root_cat['title']
                    })
                except:
                    csv_queue.put({
                        'title': root_cat['title'],
                        'full_path': root_cat['title']
                    })
                
                tracker.processed += 1
                
                # Recursive
                await crawl_category_recursive(
                    page, root_cat['link'], root_cat['title'],
                    depth=1, semaphore=semaphore
                )
            
            # بستن
            for page in all_pages:
                try:
                    await page.close()
                except:
                    pass
            
            await context.close()
            
            csv_stop_event = True
            csv_queue.put(None)
            writer_thread.join(timeout=5)
            
            elapsed = time.time() - start_time
            
            # فقط نتیجه نهایی
            print(f"\n✓ Completed: {tracker.processed} categories in {elapsed:.1f}s ({tracker.processed/elapsed:.1f}/s)")
    
    except:
        csv_stop_event = True
        csv_queue.put(None)
    
    finally:
        if browser:
            try:
                await browser.close()
            except:
                pass

if __name__ == "__main__":
    asyncio.run(main())