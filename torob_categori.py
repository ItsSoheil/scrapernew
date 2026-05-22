import asyncio
import pandas as pd
import aiohttp
import logging
from datetime import datetime

# تنظیمات لاگینگ حرفه‌ای
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# لیست نهایی برای ذخیره نتایج
all_categories = []
processed_ids = set()

async def fetch_children(session, cat_id, current_breadcrumb, parent_name, depth):
    """
    دریافت فرزندان و چاپ مسیر کامل
    """
    url = f"https://www.torob.com/api/getCat/?catid={cat_id}"
    try:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                if data.get("message") == "success" and "children" in data:
                    children = data["children"]
                    
                    for child in children:
                        child_id = child["id"]
                        child_title = child["title"]
                        
                        # بررسی تکراری نبودن ID
                        if child_id in processed_ids:
                            continue
                            
                        processed_ids.add(child_id)
                        
                        # ساخت مسیر کامل برای نمایش
                        if depth == 0:
                            full_breadcrumb = child_title
                        else:
                            full_breadcrumb = f"{current_breadcrumb} > {child_title}"
                        
                        # ذخیره در لیست
                        parent_value = parent_name if depth > 0 else "" 
                        
                        all_categories.append({
                            "depth": depth,
                            "name": child_title,
                            "parent": parent_value, 
                            "breadcrumb": full_breadcrumb,
                            "id": child_id # این متغیر برای پردازش استفاده می‌شود اما در خروجی نهایی حذف خواهد شد
                        })
                        
                        # چاپ تمیز در کنسول
                        indent = "  " * depth
                        logger.info(f"{indent}├── {child_title}")
                        
                        if child.get("has_children", False):
                            await asyncio.sleep(0.05)
                            await fetch_children(session, child_id, full_breadcrumb, child_title, depth + 1)
                else:
                    logger.warning(f"API returned success message but no children for ID: {cat_id}")
            else:
                logger.error(f"HTTP Error {response.status} for URL: {url}")
    except Exception as e:
        logger.error(f"An error occurred while fetching ID {cat_id}: {e}")

async def main():
    global all_categories, processed_ids
    
    logger.info("🚀 Starting Torob API Crawler...")
    start_time = datetime.now()
    
    async with aiohttp.ClientSession() as session:
        url_root = "https://www.torob.com/api/getCat/?catid=0"
        try:
            async with session.get(url_root) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("message") == "success" and "children" in data:
                        children = data["children"]
                        logger.info(f"Found {len(children)} main categories")
                        
                        for child in children:
                            child_id = child["id"]
                            child_title = child["title"]
                            
                            if child_id in processed_ids:
                                continue
                                
                            processed_ids.add(child_id)
                            
                            full_breadcrumb = child_title
                            
                            all_categories.append({
                                "depth": 0,
                                "name": child_title,
                                "parent": "", 
                                "breadcrumb": full_breadcrumb,
                                "id": child_id
                            })
                            
                            logger.info(f"├── {child_title}")
                            
                            if child.get("has_children", False):
                                await asyncio.sleep(0.05)
                                await fetch_children(session, child_id, full_breadcrumb, child_title, 1)
                    else:
                        logger.warning("Could not fetch root categories from API")
                else:
                    logger.error(f"HTTP Error: {response.status}")
        except Exception as e:
            logger.error(f"Fatal Error: {e}")
            
    end_time = datetime.now()
    duration = end_time - start_time
    
    logger.info(f"Processing finished in {duration.total_seconds():.2f} seconds.")
    logger.info(f"Total unique categories processed: {len(all_categories)}")
    
    if all_categories:
        try:
            df = pd.DataFrame(all_categories)
            df = df.drop_duplicates(subset=["id"])
            
            # مرتب‌سازی بر اساس عمق و نام برای خوانایی بهتر
            df = df.sort_values(by=['depth', 'parent', 'name']).reset_index(drop=True)
            
            # حذف ستون id از ستون‌های نهایی
            # لیست ستون‌هایی که می‌خواهیم در CSV بمانند
            columns_to_keep = ["depth", "name", "parent", "breadcrumb"]
            
            # اگر ستون‌های اضافی دیگری هم بود، اینجا اضافه کنید، در غیر این صورت فقط این 4 تا می‌مانند
            df = df[columns_to_keep]
                
            output_file = "torob_categories_clean.csv"
            df.to_csv(output_file, index=False, encoding="utf-8-sig")
            logger.info(f"Data successfully saved to: {output_file}")
            logger.info("Columns saved: depth, name, parent, breadcrumb")
            logger.info("Note: ID column has been removed from the final CSV.")
            
        except Exception as e:
            logger.error(f"Failed to save CSV file: {e}")
    else:
        logger.warning("No data was collected. File not saved.")

if __name__ == "__main__":
    asyncio.run(main())