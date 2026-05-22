import json
import csv

def json_to_csv_structure(json_data):
    """
    داده‌های JSON دسته‌بندی را دریافت کرده و آن را به لیستی از دیکشنری‌ها
    با ساختار {root, parent, item} تبدیل می‌کند.
    """
    parsed_data = []
    
    # بررسی می‌کنیم که آیا ورودی دیکشنری است یا لیست
    # در حالت ایده‌آل ورودی لیستی از دسته‌های اصلی است
    if isinstance(json_data, dict):
        categories = json_data.get('categories', [json_data])
    elif isinstance(json_data, list):
        categories = json_data
    else:
        return parsed_data

    for root_category in categories:
        root_title = root_category.get("title", "")
        root_url = root_category.get("url", "")
        children = root_category.get("children", [])
        
        # اگر دسته اصلی خالی باشد، نادیده گرفته شود
        if not root_title:
            continue

        # اگر زیردسته‌ای وجود ندارد، خود دسته اصلی به عنوان آیتم نهایی ثبت می‌شود
        if not children:
            parsed_data.append({
                "root": root_title,
                "parent": "",
                "item": root_title
            })
            continue

        # پردازش زیردسته‌ها
        for child in children:
            child_title = child.get("title", "")
            child_url = child.get("url", "")
            
            if not child_title:
                continue

            # در این ساختار، سطح دوم همان parent است و خود child_item است
            # اگر ساختار عمیق‌تر بود، نیاز به حلقه‌های تو در تو داشتیم
            # اما با توجه به JSON ارسالی، ساختار دو سطحی است (Root -> Children)
            
            parsed_data.append({
                "root": root_title,
                "parent": child_title,
                "item": child_title
            })

    return parsed_data

def save_to_csv(data, filename="basalam_categories_hierarchy.csv"):
    """
    داده‌های پردازش شده را در یک فایل CSV ذخیره می‌کند.
    """
    if not data:
        print("داده‌ای برای ذخیره وجود ندارد.")
        return
    
    with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        # هدر فایل
        writer.writerow(["Root Category (دسته اصلی)", "Parent Category (زیردسته)", "Item Name (محصول/آیتم)"])
        
        for row in data:
            writer.writerow([row["root"], row["parent"], row["item"]])
            
    print(f"فایل {filename} با موفقیت ساخته شد.")
    print(f"تعداد رکوردها: {len(data)}")

# ------------------------------------------------------------------
# محل قرارگیری داده‌های JSON
# لطفاً متغیر زیر را با محتوای JSON خود جایگزین کنید
# ------------------------------------------------------------------
json_input = """
[
  {
    "title": "خانه و آشپزخانه",
    "url": "https://basalam.com/cat/home",
    "children": [
      {
        "title": "دکوراسیون منزل",
        "url": "https://basalam.com/cat/home/%D8%AF%DA%A9%D9%88%D8%B1%D8%A7%D8%B3%DB%8C%D9%88%D9%86-%D9%85%D9%86%D8%B2%D9%84",
        "children": []
      },
      {
        "title": "ظروف سرو و پذیرایی",
        "url": "https://basalam.com/cat/home/%D8%B8%D8%B1%D9%88%D9%81-%D8%B3%D8%B1%D9%88-%D9%BE%D8%B0%DB%8C%D8%B1%D8%A7%DB%8C%DB%8C",
        "children": []
      },
      {
        "title": "فرش و گلیم",
        "url": "https://basalam.com/cat/home/%D9%81%D8%B1%D8%B4-%DA%AF%D9%84%DB%8C%D9%85",
        "children": []
      },
      {
        "title": "لوازم آشپزخانه",
        "url": "https://basalam.com/cat/home/%D9%84%D9%88%D8%A7%D8%B2%D9%85-%D8%A2%D8%B4%D9%BE%D8%B2%D8%AE%D8%A7%D9%86%D9%87",
        "children": []
      },
      {
        "title": "لوازم حمام و دستشویی",
        "url": "https://basalam.com/cat/home/%D9%84%D9%88%D8%A7%D8%B2%D9%85-%D8%AD%D9%85%D8%A7%D9%85-%D8%AF%D8%B3%D8%AA%D8%B4%D9%88%DB%8C%DB%8C",
        "children": []
      },
      {
        "title": "لوازم شستشو و نظم منزل",
        "url": "https://basalam.com/cat/home/%D9%84%D9%88%D8%A7%D8%B2%D9%85-%D8%B4%D8%B3%D8%AA%D8%B4%D9%88-%D9%86%D8%B8%D9%85-%D9%85%D9%86%D8%B2%D9%84",
        "children": []
      },
      {
        "title": "مبلمان و صنایع چوب",
        "url": "https://basalam.com/cat/home/%D9%85%D8%A8%D9%84%D9%85%D8%A7%D9%86-%D8%B5%D9%86%D8%A7%DB%8C%D8%B9-%DA%86%D9%88%D8%A8",
        "children": []
      },
      {
        "title": "کالای خواب",
        "url": "https://basalam.com/cat/home/%DA%A9%D8%A7%D9%84%D8%A7%DB%8C-%D8%AE%D9%88%D8%A7%D8%A8",
        "children": []
      },
      {
        "title": "آینه دکوراتیو",
        "url": "https://basalam.com/cat/home/%D8%A2%DB%8C%D9%86%D9%87-%D8%AF%DA%A9%D9%88%D8%B1%D8%A7%D8%AA%DB%8C%D9%88",
        "children": []
      },
      {
        "title": "استیکر و پوستر دیواری",
        "url": "https://basalam.com/cat/home/%D8%A7%D8%B3%D8%AA%DB%8C%DA%A9%D8%B1-%D9%BE%D9%88%D8%B3%D8%AA%D8%B1-%D8%AF%DB%8C%D9%88%D8%A7%D8%B1%DB%8C",
        "children": []
      },
      {
        "title": "ساعت دیواری، ایستاده و رومیزی",
        "url": "https://basalam.com/cat/home/%D8%B3%D8%A7%D8%B9%D8%AA-%D8%AF%DB%8C%D9%88%D8%A7%D8%B1%DB%8C-%D8%A7%DB%8C%D8%B3%D8%AA%D8%A7%D8%AF%D9%87-%D8%B1%D9%88%D9%85%DB%8C%D8%B2%DB%8C",
        "children": []
      },
      {
        "title": "شمع، عود و لوازم تزئینی",
        "url": "https://basalam.com/cat/home/%D8%B4%D9%85%D8%B9-%D8%B9%D9%88%D8%AF-%D9%84%D9%88%D8%A7%D8%B2%D9%85-%D8%AA%D8%B2%D8%A6%DB%8C%D9%86%DB%8C",
        "children": []
      },
      {
        "title": "قاب عکس و تابلو",
        "url": "https://basalam.com/cat/home/%D9%82%D8%A7%D8%A8-%D8%B9%DA%A9%D8%B3-%D8%AA%D8%A7%D8%A8%D9%84%D9%88",
        "children": []
      },
      {
        "title": "لوازم دکوراتیو",
        "url": "https://basalam.com/cat/home/%D9%84%D9%88%D8%A7%D8%B2%D9%85-%D8%AF%DA%A9%D9%88%D8%B1%D8%A7%D8%AA%DB%8C%D9%88",
        "children": []
      },
      {
        "title": "لوستر و چراغ آویز",
        "url": "https://basalam.com/cat/home/%D9%84%D9%88%D8%B3%D8%AA%D8%B1-%DA%86%D8%B1%D8%A7%D8%BA-%D8%A2%D9%88%DB%8C%D8%B2",
        "children": []
      },
      {
        "title": "مجسمه و تندیس",
        "url": "https://basalam.com/cat/home/%D9%85%D8%AC%D8%B3%D9%85%D9%87-%D8%AA%D9%86%D8%AF%DB%8C%D8%B3",
        "children": []
      },
      {
        "title": "پارچه",
        "url": "https://basalam.com/cat/home/%D9%BE%D8%A7%D8%B1%DA%86%D9%87",
        "children": []
      },
      {
        "title": "پرده",
        "url": "https://basalam.com/cat/home/%D9%BE%D8%B1%D8%AF%D9%87",
        "children": []
      },
      {
        "title": "چراغ خواب و آباژور",
        "url": "https://basalam.com/cat/home/%DA%86%D8%B1%D8%A7%D8%BA-%D8%AE%D9%88%D8%A7%D8%A8-%D8%A2%D8%A8%D8%A7%DA%98%D9%88%D8%B1",
        "children": []
      },
      {
        "title": "کاغذ دیواری",
        "url": "https://basalam.com/cat/home/%DA%A9%D8%A7%D8%BA%D8%B0-%D8%AF%DB%8C%D9%88%D8%A7%D8%B1%DB%8C",
        "children": []
      },
      {
        "title": "کوسن، رومیزی و شال مبل",
        "url": "https://basalam.com/cat/home/%DA%A9%D9%88%D8%B3%D9%86-%D8%B1%D9%88%D9%85%DB%8C%D8%B2%DB%8C-%D8%B4%D8%A7%D9%84-%D9%85%D8%A8%D9%84",
        "children": []
      }
    ]
  },
  {
    "title": "لوازم خانگی برقی",
    "url": "https://basalam.com/cat/appliances",
    "children": [
      {
        "title": "یخچال و فریزر",
        "url": "https://basalam.com/cat/appliances/%DB%8C%D8%AE%DA%86%D8%A7%D9%84-%D9%81%D8%B1%DB%8C%D8%B2%D8%B1",
        "children": []
      },
      {
        "title": "اجاق گاز",
        "url": "https://basalam.com/cat/appliances/%D8%A7%D8%AC%D8%A7%D9%82-%DA%AF%D8%A7%D8%B2",
        "children": []
      },
      {
        "title": "صوتی و تصویری",
        "url": "https://basalam.com/cat/appliances/%D8%B5%D9%88%D8%AA%DB%8C-%D8%AA%D8%B5%D9%88%DB%8C%D8%B1%DB%8C",
        "children": []
      },
      {
        "title": "تهویه، سرمایش و گرمایش",
        "url": "https://basalam.com/cat/appliances/%D8%AA%D9%87%D9%88%DB%8C%D9%87-%D8%B3%D8%B1%D9%85%D8%A7%DB%8C%D8%B4-%DA%AF%D8%B1%D9%85%D8%A7%DB%8C%D8%B4",
        "children": []
      },
      {
        "title": "خردکن و غذاساز",
        "url": "https://basalam.com/cat/appliances/%D8%AE%D8%B1%D8%AF%DA%A9%D9%86-%D8%BA%D8%B0%D8%A7%D8%B3%D8%A7%D8%B2",
        "children": []
      },
      {
        "title": "دستگاه تصفیه آب",
        "url": "https://basalam.com/cat/appliances/%D8%AF%D8%B3%D8%AA%DA%AF%D8%A7%D9%87-%D8%AA%D8%B5%D9%81%DB%8C%D9%87-%D8%A2%D8%A8",
        "children": []
      },
      {
        "title": "لوازم برقی شستشو و نظافت",
        "url": "https://basalam.com/cat/appliances/%D9%84%D9%88%D8%A7%D8%B2%D9%85-%D8%A8%D8%B1%D9%82%DB%8C-%D8%B4%D8%B3%D8%AA%D8%B4%D9%88-%D9%86%D8%B8%D8%A7%D9%81%D8%AA",
        "children": []
      },
      {
        "title": "لوازم برقی پخت و پز",
        "url": "https://basalam.com/cat/appliances/%D9%84%D9%88%D8%A7%D8%B2%D9%85-%D8%A8%D8%B1%D9%82%DB%8C-%D9%BE%D8%AE%D8%AA-%D9%BE%D8%B2",
        "children": []
      },
      {
        "title": "لوازم ویژه خانگی برقی",
        "url": "https://basalam.com/cat/appliances/%D9%84%D9%88%D8%A7%D8%B2%D9%85-%D9%88%DB%8C%DA%98%D9%87-%D8%AE%D8%A7%D9%86%DA%AF%DB%8C-%D8%A8%D8%B1%D9%82%DB%8C",
        "children": []
      },
      {
        "title": "نوشیدنی ساز",
        "url": "https://basalam.com/cat/appliances/%D9%86%D9%88%D8%B4%DB%8C%D8%AF%D9%86%DB%8C-%D8%B3%D8%A7%D8%B2",
        "children": []
      },
      {
        "title": "چرخ خیاطی",
        "url": "https://basalam.com/cat/appliances/%DA%86%D8%B1%D8%AE-%D8%AE%DB%8C%D8%A7%D8%B7%DB%8C",
        "children": []
      },
      {
        "title": "یخچال فریزر دوقلو",
        "url": "https://basalam.com/cat/appliances/%DB%8C%D8%AE%DA%86%D8%A7%D9%84-%D9%81%D8%B1%DB%8C%D8%B2%D8%B1-%D8%AF%D9%88%D9%82%D9%84%D9%88",
        "children": []
      },
      {
        "title": "یخچال فریزر ساید بای ساید",
        "url": "https://basalam.com/cat/appliances/%DB%8C%D8%AE%DA%86%D8%A7%D9%84-%D9%81%D8%B1%DB%8C%D8%B2%D8%B1-%D8%B3%D8%A7%DB%8C%D8%AF-%D8%A8%D8%A7%DB%8C-%D8%B3%D8%A7%DB%8C%D8%AF",
        "children": []
      },
      {
        "title": "یخچال فریزر بالا پایین و کمبی",
        "url": "https://basalam.com/cat/appliances/%DB%8C%D8%AE%DA%86%D8%A7%D9%84-%D9%81%D8%B1%DB%8C%D8%B2%D8%B1-%D8%A8%D8%A7%D9%84%D8%A7-%D9%BE%D8%A7%DB%8C%DB%8C%D9%86-%DA%A9%D9%85%D8%A8%DB%8C",
        "children": []
      },
      {
        "title": "یخچال کوچک و هتلی",
        "url": "https://basalam.com/cat/appliances/%DB%8C%D8%AE%DA%86%D8%A7%D9%84-%DA%A9%D9%88%DA%86%DA%A9-%D9%87%D8%AA%D9%84%DB%8C",
        "children": []
      },
      {
        "title": "فریزر",
        "url": "https://basalam.com/cat/appliances/%D9%81%D8%B1%DB%8C%D8%B2%D8%B1",
        "children": []
      },
      {
        "title": "یخچال بر اساس برند",
        "url": "https://basalam.com/cat/appliances/%DB%8C%D8%AE%DA%86%D8%A7%D9%84-%D8%A8%D8%B1-%D8%A7%D8%B3%D8%A7%D8%B3-%D8%A8%D8%B1%D9%86%D8%AF",
        "children": []
      },
      {
        "title": "سایر یخچال فریر",
        "url": "https://basalam.com/cat/appliances/%D8%B3%D8%A7%DB%8C%D8%B1-%DB%8C%D8%AE%DA%86%D8%A7%D9%84-%D9%81%D8%B1%DB%8C%D8%B1",
        "children": []
      }
    ]
  },
  {
    "title": "مد و پوشاک",
    "url": "https://basalam.com/cat/apparel",
    "children": [
      {
        "title": "کیف و کفش",
        "url": "https://basalam.com/cat/apparel/%DA%A9%DB%8C%D9%81-%DA%A9%D9%81%D8%B4",
        "children": []
      },
      {
        "title": "لباس و پوشاک زنانه",
        "url": "https://basalam.com/cat/apparel/%D9%84%D8%A8%D8%A7%D8%B3-%D9%BE%D9%88%D8%B4%D8%A7%DA%A9-%D8%B2%D9%86%D8%A7%D9%86%D9%87",
        "children": []
      },
      {
        "title": "لباس و پوشاک مردانه",
        "url": "https://basalam.com/cat/apparel/%D9%84%D8%A8%D8%A7%D8%B3-%D9%BE%D9%88%D8%B4%D8%A7%DA%A9-%D9%85%D8%B1%D8%AF%D8%A7%D9%86%D9%87",
        "children": []
      },
      {
        "title": "لباس و پوشاک بچگانه",
        "url": "https://basalam.com/cat/apparel/%D9%84%D8%A8%D8%A7%D8%B3-%D9%BE%D9%88%D8%B4%D8%A7%DA%A9-%D8%A8%DA%86%DA%AF%D8%A7%D9%86%D9%87",
        "children": []
      },
      {
        "title": "اکسسوری و زیورآلات زنانه و مردانه",
        "url": "https://basalam.com/cat/apparel/%D8%A7%DA%A9%D8%B3%D8%B3%D9%88%D8%B1%DB%8C-%D8%B2%DB%8C%D9%88%D8%B1%D8%A2%D9%84%D8%A7%D8%AA-%D8%B2%D9%86%D8%A7%D9%86%D9%87-%D9%85%D8%B1%D8%AF%D8%A7%D9%86%D9%87",
        "children": []
      },
      {
        "title": "اکسسوری و زیورآلات کودک و نوجوان",
        "url": "https://basalam.com/cat/apparel/%D8%A7%DA%A9%D8%B3%D8%B3%D9%88%D8%B1%DB%8C-%D8%B2%DB%8C%D9%88%D8%B1%D8%A2%D9%84%D8%A7%D8%AA-%DA%A9%D9%88%D8%AF%DA%A9-%D9%86%D9%88%D8%AC%D9%88%D8%A7%D9%86",
        "children": []
      },
      {
        "title": "لباس و پوشاک ورزشی",
        "url": "https://basalam.com/cat/apparel/%D9%84%D8%A8%D8%A7%D8%B3-%D9%BE%D9%88%D8%B4%D8%A7%DA%A9-%D9%88%D8%B1%D8%B2%D8%B4%DB%8C",
        "children": []
      },
      {
        "title": "سایر مد و پوشاک",
        "url": "https://basalam.com/cat/apparel/%D8%B3%D8%A7%DB%8C%D8%B1-%D9%85%D8%AF-%D9%BE%D9%88%D8%B4%D8%A7%DA%A9",
        "children": []
      },
      {
        "title": "دمپایی و صندل",
        "url": "https://basalam.com/cat/apparel/%D8%AF%D9%85%D9%BE%D8%A7%DB%8C%DB%8C-%D8%B5%D9%86%D8%AF%D9%84",
        "children": []
      },
      {
        "title": "کفش و کتانی",
        "url": "https://basalam.com/cat/apparel/%DA%A9%D9%81%D8%B4-%DA%A9%D8%AA%D8%A7%D9%86%DB%8C",
        "children": []
      },
      {
        "title": "کیف و کوله",
        "url": "https://basalam.com/cat/apparel/%DA%A9%DB%8C%D9%81-%DA%A9%D9%88%D9%84%D9%87",
        "children": []
      }
    ]
  },
  {
    "title": "آرایشی و بهداشتی",
    "url": "https://basalam.com/cat/beauty",
    "children": [
      {
        "title": "لوازم مراقب پوست",
        "url": "https://basalam.com/cat/beauty/%D9%84%D9%88%D8%A7%D8%B2%D9%85-%D9%85%D8%B1%D8%A7%D9%82%D8%A8-%D9%BE%D9%88%D8%B3%D8%AA",
        "children": []
      },
      {
        "title": "لوازم آرایشی",
        "url": "https://basalam.com/cat/beauty/%D9%84%D9%88%D8%A7%D8%B2%D9%85-%D8%A2%D8%B1%D8%A7%DB%8C%D8%B4%DB%8C",
        "children": []
      },
      {
        "title": "عطر و ادکلن",
        "url": "https://basalam.com/cat/beauty/%D8%B9%D8%B7%D8%B1-%D8%A7%D8%AF%DA%A9%D9%84%D9%86",
        "children": []
      },
      {
        "title": "لوازم شخصی برقی",
        "url": "https://basalam.com/cat/beauty/%D9%84%D9%88%D8%A7%D8%B2%D9%85-%D8%B4%D8%AE%D8%B5%DB%8C-%D8%A8%D8%B1%D9%82%DB%8C",
        "children": []
      },
      {
        "title": "زیبایی و سلامت مو",
        "url": "https://basalam.com/cat/beauty/%D8%B2%DB%8C%D8%A8%D8%A7%DB%8C%DB%8C-%D8%B3%D9%84%D8%A7%D9%85%D8%AA-%D9%85%D9%88",
        "children": []
      },
      {
        "title": "زیبایی و بهداشت ناخن",
        "url": "https://basalam.com/cat/beauty/%D8%B2%DB%8C%D8%A8%D8%A7%DB%8C%DB%8C-%D8%A8%D9%87%D8%AF%D8%A7%D8%B4%D8%AA-%D9%86%D8%A7%D8%AE%D9%86",
        "children": []
      },
      {
        "title": "لوازم بهداشتی",
        "url": "https://basalam.com/cat/beauty/%D9%84%D9%88%D8%A7%D8%B2%D9%85-%D8%A8%D9%87%D8%AF%D8%A7%D8%B4%D8%AA%DB%8C",
        "children": []
      },
      {
        "title": "دستگاه‌های زیبایی",
        "url": "https://basalam.com/cat/beauty/%D8%AF%D8%B3%D8%AA%DA%AF%D8%A7%D9%87-%D9%87%D8%A7%DB%8C-%D8%B2%DB%8C%D8%A8%D8%A7%DB%8C%DB%8C",
        "children": []
      },
      {
        "title": "تجهیزات آرایشگاهی",
        "url": "https://basalam.com/cat/beauty/%D8%AA%D8%AC%D9%87%DB%8C%D8%B2%D8%A7%D8%AA-%D8%A2%D8%B1%D8%A7%DB%8C%D8%B4%DA%AF%D8%A7%D9%87%DB%8C",
        "children": []
      },
      {
        "title": "روغن آرایشی و مراقبتی",
        "url": "https://basalam.com/cat/beauty/%D8%B1%D9%88%D8%BA%D9%86-%D8%A2%D8%B1%D8%A7%DB%8C%D8%B4%DB%8C-%D9%85%D8%B1%D8%A7%D9%82%D8%A8%D8%AA%DB%8C",
        "children": []
      },
      {
        "title": "آبرسان و مرطوب کننده",
        "url": "https://basalam.com/cat/beauty/%D8%A2%D8%A8%D8%B1%D8%B3%D8%A7%D9%86-%D9%85%D8%B1%D8%B7%D9%88%D8%A8-%DA%A9%D9%86%D9%86%D8%AF%D9%87",
        "children": []
      },
      {
        "title": "اسکراب و لایه بردار",
        "url": "https://basalam.com/cat/beauty/%D8%A7%D8%B3%DA%A9%D8%B1%D8%A7%D8%A8-%D9%84%D8%A7%DB%8C%D9%87-%D8%A8%D8%B1%D8%AF%D8%A7%D8%B1",
        "children": []
      },
      {
        "title": "ترمیم کننده و ضد التهاب",
        "url": "https://basalam.com/cat/beauty/%D8%AA%D8%B1%D9%85%DB%8C%D9%85-%DA%A9%D9%86%D9%86%D8%AF%D9%87-%D8%B6%D8%AF-%D8%A7%D9%84%D8%AA%D9%87%D8%A7%D8%A8",
        "children": []
      },
      {
        "title": "روشن کننده و سفید کننده",
        "url": "https://basalam.com/cat/beauty/%D8%B1%D9%88%D8%B4%D9%86-%DA%A9%D9%86%D9%86%D8%AF%D9%87-%D8%B3%D9%81%DB%8C%D8%AF-%DA%A9%D9%86%D9%86%D8%AF%D9%87",
        "children": []
      },
      {
        "title": "سایر لوازم مراقب پوست",
        "url": "https://basalam.com/cat/beauty/%D8%B3%D8%A7%DB%8C%D8%B1-%D9%84%D9%88%D8%A7%D8%B2%D9%85-%D9%85%D8%B1%D8%A7%D9%82%D8%A8-%D9%BE%D9%88%D8%B3%D8%AA",
        "children": []
      },
      {
        "title": "ضد آفتاب",
        "url": "https://basalam.com/cat/beauty/%D8%B6%D8%AF-%D8%A2%D9%81%D8%AA%D8%A7%D8%A8",
        "children": []
      },
      {
        "title": "ضد جوش و آکنه",
        "url": "https://basalam.com/cat/beauty/%D8%B6%D8%AF-%D8%AC%D9%88%D8%B4-%D8%A2%DA%A9%D9%86%D9%87",
        "children": []
      },
      {
        "title": "ضد لک",
        "url": "https://basalam.com/cat/beauty/%D8%B6%D8%AF-%D9%84%DA%A9",
        "children": []
      },
      {
        "title": "ضد چروک",
        "url": "https://basalam.com/cat/beauty/%D8%B6%D8%AF-%DA%86%D8%B1%D9%88%DA%A9",
        "children": []
      },
      {
        "title": "لیفتینگ و سفت کننده",
        "url": "https://basalam.com/cat/beauty/%D9%84%DB%8C%D9%81%D8%AA%DB%8C%D9%86%DA%AF-%D8%B3%D9%81%D8%AA-%DA%A9%D9%86%D9%86%D8%AF%D9%87",
        "children": []
      },
      {
        "title": "ماسک صورت و بدن",
        "url": "https://basalam.com/cat/beauty/%D9%85%D8%A7%D8%B3%DA%A9-%D8%B5%D9%88%D8%B1%D8%AA-%D8%A8%D8%AF%D9%86",
        "children": []
      },
      {
        "title": "پاک‌کننده آرایش و شستشوی صورت",
        "url": "https://basalam.com/cat/beauty/%D9%BE%D8%A7%DA%A9-%DA%A9%D9%86%D9%86%D8%AF%D9%87-%D8%A2%D8%B1%D8%A7%DB%8C%D8%B4-%D8%B4%D8%B3%D8%AA%D8%B4%D9%88%DB%8C-%D8%B5%D9%88%D8%B1%D8%AA",
        "children": []
      },
      {
        "title": "کرم دور چشم",
        "url": "https://basalam.com/cat/beauty/%DA%A9%D8%B1%D9%85-%D8%AF%D9%88%D8%B1-%DA%86%D8%B4%D9%85",
        "children": []
      },
      {
        "title": "کرم روز و شب",
        "url": "https://basalam.com/cat/beauty/%DA%A9%D8%B1%D9%85-%D8%B1%D9%88%D8%B2-%D8%B4%D8%A8",
        "children": []
      }
    ]
  },
  {
    "title": "مواد غذایی و سوپر مارکت",
    "url": "https://basalam.com/cat/grocery",
    "children": [
      {
        "title": "آجیل و خشکبار",
        "url": "https://basalam.com/cat/grocery/%D8%A2%D8%AC%DB%8C%D9%84-%D8%AE%D8%B4%DA%A9%D8%A8%D8%A7%D8%B1",
        "children": []
      },
      {
        "title": "تنقلات",
        "url": "https://basalam.com/cat/grocery/%D8%AA%D9%86%D9%82%D9%84%D8%A7%D8%AA",
        "children": []
      },
      {
        "title": "دسر و شیرینی جات",
        "url": "https://basalam.com/cat/grocery/%D8%AF%D8%B3%D8%B1-%D8%B4%DB%8C%D8%B1%DB%8C%D9%86%DB%8C-%D8%AC%D8%A7%D8%AA",
        "children": []
      },
      {
        "title": "شور و ترشی",
        "url": "https://basalam.com/cat/grocery/%D8%B4%D9%88%D8%B1-%D8%AA%D8%B1%D8%B4%DB%8C",
        "children": []
      },
      {
        "title": "لوازم بهداشت خانگی",
        "url": "https://basalam.com/cat/grocery/%D9%84%D9%88%D8%A7%D8%B2%D9%85-%D8%A8%D9%87%D8%AF%D8%A7%D8%B4%D8%AA-%D8%AE%D8%A7%D9%86%DA%AF%DB%8C",
        "children": []
      },
      {
        "title": "محصولات صبحانه",
        "url": "https://basalam.com/cat/grocery/%D9%85%D8%AD%D8%B5%D9%88%D9%84%D8%A7%D8%AA-%D8%B5%D8%A8%D8%AD%D8%A7%D9%86%D9%87",
        "children": []
      },
      {
        "title": "محصولات لبنی",
        "url": "https://basalam.com/cat/grocery/%D9%85%D8%AD%D8%B5%D9%88%D9%84%D8%A7%D8%AA-%D9%84%D8%A8%D9%86%DB%8C",
        "children": []
      },
      {
        "title": "محصولات پروتئینی",
        "url": "https://basalam.com/cat/grocery/%D9%85%D8%AD%D8%B5%D9%88%D9%84%D8%A7%D8%AA-%D9%BE%D8%B1%D9%88%D8%AA%D8%A6%DB%8C%D9%86%DB%8C",
        "children": []
      },
      {
        "title": "میوه و تره بار",
        "url": "https://basalam.com/cat/grocery/%D9%85%DB%8C%D9%88%D9%87-%D8%AA%D8%B1%D9%87-%D8%A8%D8%A7%D8%B1",
        "children": []
      },
      {
        "title": "نوشیدنی های سرد",
        "url": "https://basalam.com/cat/grocery/%D9%86%D9%88%D8%B4%DB%8C%D8%AF%D9%86%DB%8C-%D9%87%D8%A7%DB%8C-%D8%B3%D8%B1%D8%AF",
        "children": []
      },
      {
        "title": "نوشیدنی های گرم",
        "url": "https://basalam.com/cat/grocery/%D9%86%D9%88%D8%B4%DB%8C%D8%AF%D9%86%DB%8C-%D9%87%D8%A7%DB%8C-%DA%AF%D8%B1%D9%85",
        "children": []
      },
      {
        "title": "چاشنی و افزودنی ها",
        "url": "https://basalam.com/cat/grocery/%DA%86%D8%A7%D8%B4%D9%86%DB%8C-%D8%A7%D9%81%D8%B2%D9%88%D8%AF%D9%86%DB%8C-%D9%87%D8%A7",
        "children": []
      },
      {
        "title": "کالاهای خام و اساسی",
        "url": "https://basalam.com/cat/grocery/%DA%A9%D8%A7%D9%84%D8%A7%D9%87%D8%A7%DB%8C-%D8%AE%D8%A7%D9%85-%D8%A7%D8%B3%D8%A7%D8%B3%DB%8C",
        "children": []
      },
      {
        "title": "کنسرو و غذای آماده",
        "url": "https://basalam.com/cat/grocery/%DA%A9%D9%86%D8%B3%D8%B1%D9%88-%D8%BA%D8%B0%D8%A7%DB%8C-%D8%A2%D9%85%D8%A7%D8%AF%D9%87",
        "children": []
      },
      {
        "title": "آجیل",
        "url": "https://basalam.com/cat/grocery/%D8%A2%D8%AC%DB%8C%D9%84",
        "children": []
      },
      {
        "title": "بادام درختی",
        "url": "https://basalam.com/cat/grocery/%D8%A8%D8%A7%D8%AF%D8%A7%D9%85-%D8%AF%D8%B1%D8%AE%D8%AA%DB%8C",
        "children": []
      },
      {
        "title": "بادام زمینی",
        "url": "https://basalam.com/cat/grocery/%D8%A8%D8%A7%D8%AF%D8%A7%D9%85-%D8%B2%D9%85%DB%8C%D9%86%DB%8C",
        "children": []
      },
      {
        "title": "بادام هندی",
        "url": "https://basalam.com/cat/grocery/%D8%A8%D8%A7%D8%AF%D8%A7%D9%85-%D9%87%D9%86%D8%AF%DB%8C",
        "children": []
      },
      {
        "title": "برنجک",
        "url": "https://basalam.com/cat/grocery/%D8%A8%D8%B1%D9%86%D8%AC%DA%A9",
        "children": []
      },
      {
        "title": "تخمه",
        "url": "https://basalam.com/cat/grocery/%D8%AA%D8%AE%D9%85%D9%87",
        "children": []
      },
      {
        "title": "خرما",
        "url": "https://basalam.com/cat/grocery/%D8%AE%D8%B1%D9%85%D8%A7",
        "children": []
      },
      {
        "title": "سنجد",
        "url": "https://basalam.com/cat/grocery/%D8%B3%D9%86%D8%AC%D8%AF",
        "children": []
      },
      {
        "title": "شاهدانه",
        "url": "https://basalam.com/cat/grocery/%D8%B4%D8%A7%D9%87%D8%AF%D8%A7%D9%86%D9%87",
        "children": []
      },
      {
        "title": "عناب",
        "url": "https://basalam.com/cat/grocery/%D8%B9%D9%86%D8%A7%D8%A8",
        "children": []
      },
      {
        "title": "فندق",
        "url": "https://basalam.com/cat/grocery/%D9%81%D9%86%D8%AF%D9%82",
        "children": []
      },
      {
        "title": "میوه خشک",
        "url": "https://basalam.com/cat/grocery/%D9%85%DB%8C%D9%88%D9%87-%D8%AE%D8%B4%DA%A9",
        "children": []
      },
      {
        "title": "نخودچی",
        "url": "https://basalam.com/cat/grocery/%D9%86%D8%AE%D9%88%D8%AF%DA%86%DB%8C",
        "children": []
      },
      {
        "title": "پسته",
        "url": "https://basalam.com/cat/grocery/%D9%BE%D8%B3%D8%AA%D9%87",
        "children": []
      },
      {
        "title": "کشمش و مویز",
        "url": "https://basalam.com/cat/grocery/%DA%A9%D8%B4%D9%85%D8%B4-%D9%85%D9%88%DB%8C%D8%B2",
        "children": []
      },
      {
        "title": "گردو",
        "url": "https://basalam.com/cat/grocery/%DA%AF%D8%B1%D8%AF%D9%88",
        "children": []
      },
      {
        "title": "گندمک",
        "url": "https://basalam.com/cat/grocery/%DA%AF%D9%86%D8%AF%D9%85%DA%A9",
        "children": []
      }
    ]
  },
  {
    "title": "ابزارآلات و تجهیزات",
    "url": "https://basalam.com/cat/tools",
    "children": [
      {
        "title": "ابزار برقی و شارژی",
        "url": "https://basalam.com/cat/tools/%D8%A7%D8%A8%D8%B2%D8%A7%D8%B1-%D8%A8%D8%B1%D9%82%DB%8C-%D8%B4%D8%A7%D8%B1%DA%98%DB%8C",
        "children": []
      },
      {
        "title": "ابزار دقیق و اندازه‌گیری",
        "url": "https://basalam.com/cat/tools/%D8%A7%D8%A8%D8%B2%D8%A7%D8%B1-%D8%AF%D9%82%DB%8C%D9%82-%D8%A7%D9%86%D8%AF%D8%A7%D8%B2%D9%87-%DA%AF%DB%8C%D8%B1%DB%8C",
        "children": []
      },
      {
        "title": "ابزار غیر برقی",
        "url": "https://basalam.com/cat/tools/%D8%A7%D8%A8%D8%B2%D8%A7%D8%B1-%D8%BA%DB%8C%D8%B1-%D8%A8%D8%B1%D9%82%DB%8C",
        "children": []
      },
      {
        "title": "تجهیزات بسته‌ بندی و حمل بار",
        "url": "https://basalam.com/cat/tools/%D8%AA%D8%AC%D9%87%DB%8C%D8%B2%D8%A7%D8%AA-%D8%A8%D8%B3%D8%AA%D9%87-%D8%A8%D9%86%D8%AF%DB%8C-%D8%AD%D9%85%D9%84-%D8%A8%D8%A7%D8%B1",
        "children": []
      },
      {
        "title": "تجهیزات ساختمان",
        "url": "https://basalam.com/cat/tools/%D8%AA%D8%AC%D9%87%DB%8C%D8%B2%D8%A7%D8%AA-%D8%B3%D8%A7%D8%AE%D8%AA%D9%85%D8%A7%D9%86",
        "children": []
      },
      {
        "title": "تجهیزات صنعت غذا و نوشیدنی",
        "url": "https://basalam.com/cat/tools/%D8%AA%D8%AC%D9%87%DB%8C%D8%B2%D8%A7%D8%AA-%D8%B5%D9%86%D8%B9%D8%AA-%D8%BA%D8%B0%D8%A7-%D9%86%D9%88%D8%B4%DB%8C%D8%AF%D9%86%DB%8C",
        "children": []
      },
      {
        "title": "تجهیزات صنعتی",
        "url": "https://basalam.com/cat/tools/%D8%AA%D8%AC%D9%87%DB%8C%D8%B2%D8%A7%D8%AA-%D8%B5%D9%86%D8%B9%D8%AA%DB%8C",
        "children": []
      },
      {
        "title": "تجهیزات فروشگاهی",
        "url": "https://basalam.com/cat/tools/%D8%AA%D8%AC%D9%87%DB%8C%D8%B2%D8%A7%D8%AA-%D9%81%D8%B1%D9%88%D8%B4%DA%AF%D8%A7%D9%87%DB%8C",
        "children": []
      },
      {
        "title": "تجهیزات نقاشی و بنایی",
        "url": "https://basalam.com/cat/tools/%D8%AA%D8%AC%D9%87%DB%8C%D8%B2%D8%A7%D8%AA-%D9%86%D9%82%D8%A7%D8%B4%DB%8C-%D8%A8%D9%86%D8%A7%DB%8C%DB%8C",
        "children": []
      },
      {
        "title": "تجهیزات نگهداری و پرورش حیوانات",
        "url": "https://basalam.com/cat/tools/%D8%AA%D8%AC%D9%87%DB%8C%D8%B2%D8%A7%D8%AA-%D9%86%DA%AF%D9%87%D8%AF%D8%A7%D8%B1%DB%8C-%D9%BE%D8%B1%D9%88%D8%B1%D8%B4-%D8%AD%DB%8C%D9%88%D8%A7%D9%86%D8%A7%D8%AA",
        "children": []
      },
      {
        "title": "تجهیزات کفش و چرم",
        "url": "https://basalam.com/cat/tools/%D8%AA%D8%AC%D9%87%DB%8C%D8%B2%D8%A7%D8%AA-%DA%A9%D9%81%D8%B4-%DA%86%D8%B1%D9%85",
        "children": []
      },
      {
        "title": "قطعات الکترونیک",
        "url": "https://basalam.com/cat/tools/%D9%82%D8%B7%D8%B9%D8%A7%D8%AA-%D8%A7%D9%84%DA%A9%D8%AA%D8%B1%D9%88%D9%86%DB%8C%DA%A9",
        "children": []
      },
      {
        "title": "لوازم ایمنی و حفاظتی",
        "url": "https://basalam.com/cat/tools/%D9%84%D9%88%D8%A7%D8%B2%D9%85-%D8%A7%DB%8C%D9%85%D9%86%DB%8C-%D8%AD%D9%81%D8%A7%D8%B8%D8%AA%DB%8C",
        "children": []
      },
      {
        "title": "کشاورزی، باغبانی و گلخانه",
        "url": "https://basalam.com/cat/tools/%DA%A9%D8%B4%D8%A7%D9%88%D8%B1%D8%B2%DB%8C-%D8%A8%D8%A7%D8%BA%D8%A8%D8%A7%D9%86%DB%8C-%DA%AF%D9%84%D8%AE%D8%A7%D9%86%D9%87",
        "children": []
      },
      {
        "title": "ابزار اتصال و جوش",
        "url": "https://basalam.com/cat/tools/%D8%A7%D8%A8%D8%B2%D8%A7%D8%B1-%D8%A7%D8%AA%D8%B5%D8%A7%D9%84-%D8%AC%D9%88%D8%B4",
        "children": []
      },
      {
        "title": "ابزار برش و تراشکاری",
        "url": "https://basalam.com/cat/tools/%D8%A7%D8%A8%D8%B2%D8%A7%D8%B1-%D8%A8%D8%B1%D8%B4-%D8%AA%D8%B1%D8%A7%D8%B4%DA%A9%D8%A7%D8%B1%DB%8C",
        "children": []
      },
      {
        "title": "ابزار دمش و مکش",
        "url": "https://basalam.com/cat/tools/%D8%A7%D8%A8%D8%B2%D8%A7%D8%B1-%D8%AF%D9%85%D8%B4-%D9%85%DA%A9%D8%B4",
        "children": []
      },
      {
        "title": "ابزار سنباده، رنده و پولیش",
        "url": "https://basalam.com/cat/tools/%D8%A7%D8%A8%D8%B2%D8%A7%D8%B1-%D8%B3%D9%86%D8%A8%D8%A7%D8%AF%D9%87-%D8%B1%D9%86%D8%AF%D9%87-%D9%BE%D9%88%D9%84%DB%8C%D8%B4",
        "children": []
      },
      {
        "title": "ابزار سوراخکاری و پیچاندن",
        "url": "https://basalam.com/cat/tools/%D8%A7%D8%A8%D8%B2%D8%A7%D8%B1-%D8%B3%D9%88%D8%B1%D8%A7%D8%AE%DA%A9%D8%A7%D8%B1%DB%8C-%D9%BE%DB%8C%DA%86%D8%A7%D9%86%D8%AF%D9%86",
        "children": []
      },
      {
        "title": "سایر ابزارهای برقی",
        "url": "https://basalam.com/cat/tools/%D8%B3%D8%A7%DB%8C%D8%B1-%D8%A7%D8%A8%D8%B2%D8%A7%D8%B1%D9%87%D8%A7%DB%8C-%D8%A8%D8%B1%D9%82%DB%8C",
        "children": []
      },
      {
        "title": "ویبره کاشی، سرامیک و بتن",
        "url": "https://basalam.com/cat/tools/%D9%88%DB%8C%D8%A8%D8%B1%D9%87-%DA%A9%D8%A7%D8%B4%DB%8C-%D8%B3%D8%B1%D8%A7%D9%85%DB%8C%DA%A9-%D8%A8%D8%AA%D9%86",
        "children": []
      },
      {
        "title": "موتور برق و ژنراتور",
        "url": "https://basalam.com/cat/tools/%DA%98%D9%86%D8%B1%D8%A7%D8%AA%D9%88%D8%B1-%D9%85%D9%88%D8%AA%D9%88%D8%B1-%D8%A8%D8%B1%D9%82",
        "children": []
      }
    ]
  },
  {
    "title": "فرهنگی هنری",
    "url": "https://basalam.com/cat/cultural",
    "children": [
      {
        "title": "لوازم التحریر",
        "url": "https://basalam.com/cat/cultural/%D9%84%D9%88%D8%A7%D8%B2%D9%85-%D8%A7%D9%84%D8%AA%D8%AD%D8%B1%DB%8C%D8%B1",
        "children": []
      },
      {
        "title": "محصولات مذهبی",
        "url": "https://basalam.com/cat/cultural/%D9%85%D8%AD%D8%B5%D9%88%D9%84%D8%A7%D8%AA-%D9%85%D8%B0%D9%87%D8%A8%DB%8C",
        "children": []
      },
      {
        "title": "ابزار کار هنری و دستی",
        "url": "https://basalam.com/cat/cultural/%D8%A7%D8%A8%D8%B2%D8%A7%D8%B1-%DA%A9%D8%A7%D8%B1-%D9%87%D9%86%D8%B1%DB%8C-%D8%AF%D8%B3%D8%AA%DB%8C",
        "children": []
      },
      {
        "title": "خدمات و محتوای فرهنگی",
        "url": "https://basalam.com/cat/cultural/%D8%AE%D8%AF%D9%85%D8%A7%D8%AA-%D9%85%D8%AD%D8%AA%D9%88%D8%A7%DB%8C-%D9%81%D8%B1%D9%87%D9%86%DA%AF%DB%8C",
        "children": []
      },
      {
        "title": "صنایع دستی",
        "url": "https://basalam.com/cat/cultural/%D8%B5%D9%86%D8%A7%DB%8C%D8%B9-%D8%AF%D8%B3%D8%AA%DB%8C",
        "children": []
      },
      {
        "title": "ملزومات هدیه و مهمانی",
        "url": "https://basalam.com/cat/cultural/%D9%85%D9%84%D8%B2%D9%88%D9%85%D8%A7%D8%AA-%D9%87%D8%AF%DB%8C%D9%87-%D9%85%D9%87%D9%85%D8%A7%D9%86%DB%8C",
        "children": []
      },
      {
        "title": "دفتر",
        "url": "https://basalam.com/cat/cultural/%D8%AF%D9%81%D8%AA%D8%B1",
        "children": []
      },
      {
        "title": "کلاسور و دفتر کلاسوری",
        "url": "https://basalam.com/cat/cultural/%DA%A9%D9%84%D8%A7%D8%B3%D9%88%D8%B1-%D8%AF%D9%81%D8%AA%D8%B1-%DA%A9%D9%84%D8%A7%D8%B3%D9%88%D8%B1%DB%8C",
        "children": []
      },
      {
        "title": "نوشت‌ افزار",
        "url": "https://basalam.com/cat/cultural/%D9%86%D9%88%D8%B4%D8%AA-%D8%A7%D9%81%D8%B2%D8%A7%D8%B1",
        "children": []
      },
      {
        "title": "جامدادی",
        "url": "https://basalam.com/cat/cultural/%D8%AC%D8%A7%D9%85%D8%AF%D8%A7%D8%AF%DB%8C",
        "children": []
      },
      {
        "title": "لوازم طراحی و نقاشی",
        "url": "https://basalam.com/cat/cultural/%D9%84%D9%88%D8%A7%D8%B2%D9%85-%D8%B7%D8%B1%D8%A7%D8%AD%DB%8C-%D9%86%D9%82%D8%A7%D8%B4%DB%8C",
        "children": []
      },
      {
        "title": "سایر لوازم التحریر",
        "url": "https://basalam.com/cat/cultural/%D8%B3%D8%A7%DB%8C%D8%B1-%D9%84%D9%88%D8%A7%D8%B2%D9%85-%D8%A7%D9%84%D8%AA%D8%AD%D8%B1%DB%8C%D8%B1",
        "children": []
      },
      {
        "title": "لوازم التحریر اداری",
        "url": "https://basalam.com/cat/cultural/%D9%84%D9%88%D8%A7%D8%B2%D9%85-%D8%A7%D9%84%D8%AA%D8%AD%D8%B1%DB%8C%D8%B1-%D8%A7%D8%AF%D8%A7%D8%B1%DB%8C",
        "children": []
      },
      {
        "title": "برچسب و استیکر",
        "url": "https://basalam.com/cat/cultural/%D8%A8%D8%B1%DA%86%D8%B3%D8%A8-%D8%A7%D8%B3%D8%AA%DB%8C%DA%A9%D8%B1",
        "children": []
      },
      {
        "title": "کاغذ و مقوا",
        "url": "https://basalam.com/cat/cultural/%DA%A9%D8%A7%D8%BA%D8%B0-%D9%85%D9%82%D9%88%D8%A7",
        "children": []
      },
      {
        "title": "ابزار طراحی و مهندسی",
        "url": "https://basalam.com/cat/cultural/%D8%A7%D8%A8%D8%B2%D8%A7%D8%B1-%D8%B7%D8%B1%D8%A7%D8%AD%DB%8C-%D9%85%D9%87%D9%86%D8%AF%D8%B3%DB%8C",
        "children": []
      },
      {
        "title": "جلد کتاب و دفتر",
        "url": "https://basalam.com/cat/cultural/%D8%AC%D9%84%D8%AF-%DA%A9%D8%AA%D8%A7%D8%A8-%D8%AF%D9%81%D8%AA%D8%B1",
        "children": []
      },
      {
        "title": "آلبوم عکس",
        "url": "https://basalam.com/cat/cultural/%D8%A2%D9%84%D8%A8%D9%88%D9%85-%D8%B9%DA%A9%D8%B3",
        "children": []
      },
      {
        "title": "تقویم، سررسید و سالنامه",
        "url": "https://basalam.com/cat/cultural/%D8%AA%D9%82%D9%88%DB%8C%D9%85-%D8%B3%D8%B1%D8%B1%D8%B3%DB%8C%D8%AF-%D8%B3%D8%A7%D9%84%D9%86%D8%A7%D9%85%D9%87",
        "children": []
      }
    ]
  },
  {
    "title": "خودرو و موتورسیکلت",
    "url": "https://basalam.com/cat/auto",
    "children": [
      {
        "title": "تجهیزات موتور سیکلت",
        "url": "https://basalam.com/cat/auto/%D8%AA%D8%AC%D9%87%DB%8C%D8%B2%D8%A7%D8%AA-%D9%85%D9%88%D8%AA%D9%88%D8%B1-%D8%B3%DB%8C%DA%A9%D9%84%D8%AA",
        "children": []
      },
      {
        "title": "لوازم جانبی خودرو",
        "url": "https://basalam.com/cat/auto/%D9%84%D9%88%D8%A7%D8%B2%D9%85-%D8%AC%D8%A7%D9%86%D8%A8%DB%8C-%D8%AE%D9%88%D8%AF%D8%B1%D9%88",
        "children": []
      },
      {
        "title": "لوازم مصرفی خودرو",
        "url": "https://basalam.com/cat/auto/%D9%84%D9%88%D8%A7%D8%B2%D9%85-%D9%85%D8%B5%D8%B1%D9%81%DB%8C-%D8%AE%D9%88%D8%AF%D8%B1%D9%88",
        "children": []
      },
      {
        "title": "لوازم یدکی خودرو",
        "url": "https://basalam.com/cat/auto/%D9%84%D9%88%D8%A7%D8%B2%D9%85-%DB%8C%D8%AF%DA%A9%DB%8C-%D8%AE%D9%88%D8%AF%D8%B1%D9%88",
        "children": []
      },
      {
        "title": "موتور سیکلت",
        "url": "https://basalam.com/cat/auto/%D9%85%D9%88%D8%AA%D9%88%D8%B1-%D8%B3%DB%8C%DA%A9%D9%84%D8%AA",
        "children": []
      },
      {
        "title": "لوازم جانبی موتور سیکلت",
        "url": "https://basalam.com/cat/auto/%D9%84%D9%88%D8%A7%D8%B2%D9%85-%D8%AC%D8%A7%D9%86%D8%A8%DB%8C-%D9%85%D9%88%D8%AA%D9%88%D8%B1-%D8%B3%DB%8C%DA%A9%D9%84%D8%AA",
        "children": []
      },
      {
        "title": "لوازم مصرفی موتور سیکلت",
        "url": "https://basalam.com/cat/auto/%D9%84%D9%88%D8%A7%D8%B2%D9%85-%D9%85%D8%B5%D8%B1%D9%81%DB%8C-%D9%85%D9%88%D8%AA%D9%88%D8%B1-%D8%B3%DB%8C%DA%A9%D9%84%D8%AA",
        "children": []
      },
      {
        "title": "لوازم یدکی موتور سیکلت",
        "url": "https://basalam.com/cat/auto/%D9%84%D9%88%D8%A7%D8%B2%D9%85-%DB%8C%D8%AF%DA%A9%DB%8C-%D9%85%D9%88%D8%AA%D9%88%D8%B1-%D8%B3%DB%8C%DA%A9%D9%84%D8%AA",
        "children": []
      }
    ]
  },
  {
    "title": "کتاب",
    "url": "https://basalam.com/cat/book",
    "children": [
      {
        "title": "کتاب روانشناسی و موفقیت",
        "url": "https://basalam.com/cat/book/%DA%A9%D8%AA%D8%A7%D8%A8-%D8%B1%D9%88%D8%A7%D9%86%D8%B4%D9%86%D8%A7%D8%B3%DB%8C-%D9%85%D9%88%D9%81%D9%82%DB%8C%D8%AA",
        "children": []
      },
      {
        "title": "ادبیات",
        "url": "https://basalam.com/cat/book/%D8%A7%D8%AF%D8%A8%DB%8C%D8%A7%D8%AA",
        "children": []
      },
      {
        "title": "کتاب کودک و نوجوان",
        "url": "https://basalam.com/cat/book/%DA%A9%D8%AA%D8%A7%D8%A8-%DA%A9%D9%88%D8%AF%DA%A9-%D9%86%D9%88%D8%AC%D9%88%D8%A7%D9%86",
        "children": []
      },
      {
        "title": "کتاب درسی و کمک درسی",
        "url": "https://basalam.com/cat/book/%DA%A9%D8%AA%D8%A7%D8%A8-%D8%AF%D8%B1%D8%B3%DB%8C-%DA%A9%D9%85%DA%A9-%D8%AF%D8%B1%D8%B3%DB%8C",
        "children": []
      },
      {
        "title": "کتاب دانشگاهی",
        "url": "https://basalam.com/cat/book/%DA%A9%D8%AA%D8%A7%D8%A8-%D8%AF%D8%A7%D9%86%D8%B4%DA%AF%D8%A7%D9%87%DB%8C",
        "children": []
      },
      {
        "title": "کتاب آموزش زبان",
        "url": "https://basalam.com/cat/book/%DA%A9%D8%AA%D8%A7%D8%A8-%D8%A2%D9%85%D9%88%D8%B2%D8%B4-%D8%B2%D8%A8%D8%A7%D9%86",
        "children": []
      },
      {
        "title": "خانواده و سبک زندگی",
        "url": "https://basalam.com/cat/book/%D8%AE%D8%A7%D9%86%D9%88%D8%A7%D8%AF%D9%87-%D8%B3%D8%A8%DA%A9-%D8%B2%D9%86%D8%AF%DA%AF%DB%8C",
        "children": []
      },
      {
        "title": "کتاب مذهبی",
        "url": "https://basalam.com/cat/book/%DA%A9%D8%AA%D8%A7%D8%A8-%D9%85%D8%B0%D9%87%D8%A8%DB%8C",
        "children": []
      },
      {
        "title": "کتاب تاریخ و جغرافیا",
        "url": "https://basalam.com/cat/book/%DA%A9%D8%AA%D8%A7%D8%A8-%D8%AA%D8%A7%D8%B1%DB%8C%D8%AE-%D8%AC%D8%BA%D8%B1%D8%A7%D9%81%DB%8C%D8%A7",
        "children": []
      },
      {
        "title": "کتاب فلسفه و منطق",
        "url": "https://basalam.com/cat/book/%DA%A9%D8%AA%D8%A7%D8%A8-%D9%81%D9%84%D8%B3%D9%81%D9%87-%D9%85%D9%86%D8%B7%D9%82",
        "children": []
      },
      {
        "title": "کتاب هنر",
        "url": "https://basalam.com/cat/book/%DA%A9%D8%AA%D8%A7%D8%A8-%D9%87%D9%86%D8%B1",
        "children": []
      },
      {
        "title": "کتاب های پر فروش",
        "url": "https://basalam.com/cat/book/%DA%A9%D8%AA%D8%A7%D8%A8-%D9%87%D8%A7%DB%8C-%D9%BE%D8%B1-%D9%81%D8%B1%D9%88%D8%B4",
        "children": []
      },
      {
        "title": "سایر کتاب ها",
        "url": "https://basalam.com/cat/book/%D8%B3%D8%A7%DB%8C%D8%B1-%DA%A9%D8%AA%D8%A7%D8%A8-%D9%87%D8%A7",
        "children": []
      },
      {
        "title": "مجلات",
        "url": "https://basalam.com/cat/book/%D9%85%D8%AC%D9%84%D8%A7%D8%AA",
        "children": []
      },
      {
        "title": "خودشناسی و خودسازی",
        "url": "https://basalam.com/cat/book/%D8%AE%D9%88%D8%AF%D8%B4%D9%86%D8%A7%D8%B3%DB%8C-%D8%AE%D9%88%D8%AF%D8%B3%D8%A7%D8%B2%DB%8C",
        "children": []
      },
      {
        "title": "کتاب اعتماد و عزت نفس",
        "url": "https://basalam.com/cat/book/%DA%A9%D8%AA%D8%A7%D8%A8-%D8%A7%D8%B9%D8%AA%D9%85%D8%A7%D8%AF-%D8%B9%D8%B2%D8%AA-%D9%86%D9%81%D8%B3",
        "children": []
      },
      {
        "title": "کتاب افسردگی",
        "url": "https://basalam.com/cat/book/%DA%A9%D8%AA%D8%A7%D8%A8-%D8%A7%D9%81%D8%B3%D8%B1%D8%AF%DA%AF%DB%8C",
        "children": []
      },
      {
        "title": "کتاب توسعه فردی و موفقیت",
        "url": "https://basalam.com/cat/book/%DA%A9%D8%AA%D8%A7%D8%A8-%D8%AA%D9%88%D8%B3%D8%B9%D9%87-%D9%81%D8%B1%D8%AF%DB%8C-%D9%85%D9%88%D9%81%D9%82%DB%8C%D8%AA",
        "children": []
      },
      {
        "title": "کتاب روانشناسی شخصیت",
        "url": "https://basalam.com/cat/book/%DA%A9%D8%AA%D8%A7%D8%A8-%D8%B1%D9%88%D8%A7%D9%86%D8%B4%D9%86%D8%A7%D8%B3%DB%8C-%D8%B4%D8%AE%D8%B5%DB%8C%D8%AA",
        "children": []
      },
      {
        "title": "کتاب کنترل خشم",
        "url": "https://basalam.com/cat/book/%DA%A9%D8%AA%D8%A7%D8%A8-%DA%A9%D9%86%D8%AA%D8%B1%D9%84-%D8%AE%D8%B4%D9%85",
        "children": []
      }
    ]
  },
  {
    "title": "سلامت و پزشکی",
    "url": "https://basalam.com/cat/health",
    "children": [
      {
        "title": "تجهیزات سلامتی",
        "url": "https://basalam.com/cat/health/%D8%AA%D8%AC%D9%87%DB%8C%D8%B2%D8%A7%D8%AA-%D8%B3%D9%84%D8%A7%D9%85%D8%AA%DB%8C",
        "children": []
      },
      {
        "title": "تجهیزات پزشکی",
        "url": "https://basalam.com/cat/health/%D8%AA%D8%AC%D9%87%DB%8C%D8%B2%D8%A7%D8%AA-%D9%BE%D8%B2%D8%B4%DA%A9%DB%8C",
        "children": []
      },
      {
        "title": "دارو و پماد درمانی",
        "url": "https://basalam.com/cat/health/%D8%AF%D8%A7%D8%B1%D9%88-%D9%BE%D9%85%D8%A7%D8%AF-%D8%AF%D8%B1%D9%85%D8%A7%D9%86%DB%8C",
        "children": []
      },
      {
        "title": "عطاری و گیاهان دارویی",
        "url": "https://basalam.com/cat/health/%D8%B9%D8%B7%D8%A7%D8%B1%DB%8C-%DA%AF%DB%8C%D8%A7%D9%87%D8%A7%D9%86-%D8%AF%D8%A7%D8%B1%D9%88%DB%8C%DB%8C",
        "children": []
      },
      {
        "title": "مکمل های دارویی و غذایی",
        "url": "https://basalam.com/cat/health/%D9%85%DA%A9%D9%85%D9%84-%D9%87%D8%A7%DB%8C-%D8%AF%D8%A7%D8%B1%D9%88%DB%8C%DB%8C-%D8%BA%D8%B0%D8%A7%DB%8C%DB%8C",
        "children": []
      },
      {
        "title": "مکمل ورزشی و بدنسازی",
        "url": "https://basalam.com/cat/health/%D9%85%DA%A9%D9%85%D9%84-%D9%88%D8%B1%D8%B2%D8%B4%DB%8C-%D8%A8%D8%AF%D9%86%D8%B3%D8%A7%D8%B2%DB%8C",
        "children": []
      },
      {
        "title": "تب سنج و دماسنج",
        "url": "https://basalam.com/cat/health/%D8%AA%D8%A8-%D8%B3%D9%86%D8%AC-%D8%AF%D9%85%D8%A7%D8%B3%D9%86%D8%AC",
        "children": []
      },
      {
        "title": "تجهیزات ارتوپدی و حرکتی",
        "url": "https://basalam.com/cat/health/%D8%AA%D8%AC%D9%87%DB%8C%D8%B2%D8%A7%D8%AA-%D8%A7%D8%B1%D8%AA%D9%88%D9%BE%D8%AF%DB%8C-%D8%AD%D8%B1%DA%A9%D8%AA%DB%8C",
        "children": []
      },
      {
        "title": "تجهیزات فیزیوتراپی",
        "url": "https://basalam.com/cat/health/%D8%AA%D8%AC%D9%87%DB%8C%D8%B2%D8%A7%D8%AA-%D9%81%DB%8C%D8%B2%DB%8C%D9%88%D8%AA%D8%B1%D8%A7%D9%BE%DB%8C",
        "children": []
      },
      {
        "title": "تست قند خون و لوازم جانبی",
        "url": "https://basalam.com/cat/health/%D8%AA%D8%B3%D8%AA-%D9%82%D9%86%D8%AF-%D8%AE%D9%88%D9%86-%D9%84%D9%88%D8%A7%D8%B2%D9%85-%D8%AC%D8%A7%D9%86%D8%A8%DB%8C",
        "children": []
      },
      {
        "title": "سایر تجهیزات سلامتی",
        "url": "https://basalam.com/cat/health/%D8%B3%D8%A7%DB%8C%D8%B1-%D8%AA%D8%AC%D9%87%DB%8C%D8%B2%D8%A7%D8%AA-%D8%B3%D9%84%D8%A7%D9%85%D8%AA%DB%8C",
        "children": []
      },
      {
        "title": "سمعک",
        "url": "https://basalam.com/cat/health/%D8%B3%D9%85%D8%B9%DA%A9",
        "children": []
      },
      {
        "title": "شکم بند لاغری و ورزشی",
        "url": "https://basalam.com/cat/health/%D8%B4%DA%A9%D9%85-%D8%A8%D9%86%D8%AF-%D9%84%D8%A7%D8%BA%D8%B1%DB%8C-%D9%88%D8%B1%D8%B2%D8%B4%DB%8C",
        "children": []
      },
      {
        "title": "شیلد محافظ صورت",
        "url": "https://basalam.com/cat/health/%D8%B4%DB%8C%D9%84%D8%AF-%D9%85%D8%AD%D8%A7%D9%81%D8%B8-%D8%B5%D9%88%D8%B1%D8%AA",
        "children": []
      },
      {
        "title": "فشارسنج",
        "url": "https://basalam.com/cat/health/%D9%81%D8%B4%D8%A7%D8%B1%D8%B3%D9%86%D8%AC",
        "children": []
      },
      {
        "title": "لوازم جانبی فشارسنج",
        "url": "https://basalam.com/cat/health/%D9%84%D9%88%D8%A7%D8%B2%D9%85-%D8%AC%D8%A7%D9%86%D8%A8%DB%8C-%D9%81%D8%B4%D8%A7%D8%B1%D8%B3%D9%86%D8%AC",
        "children": []
      },
      {
        "title": "ماساژور و لوازم جانبی",
        "url": "https://basalam.com/cat/health/%D9%85%D8%A7%D8%B3%D8%A7%DA%98%D9%88%D8%B1-%D9%84%D9%88%D8%A7%D8%B2%D9%85-%D8%AC%D8%A7%D9%86%D8%A8%DB%8C",
        "children": []
      },
      {
        "title": "ماسک تنفسی و بهداشتی",
        "url": "https://basalam.com/cat/health/%D9%85%D8%A7%D8%B3%DA%A9-%D8%AA%D9%86%D9%81%D8%B3%DB%8C-%D8%A8%D9%87%D8%AF%D8%A7%D8%B4%D8%AA%DB%8C",
        "children": []
      },
      {
        "title": "پالس اکسیمتر و اکسیژن سنج",
        "url": "https://basalam.com/cat/health/%D9%BE%D8%A7%D9%84%D8%B3-%D8%A7%DA%A9%D8%B3%DB%8C%D9%85%D8%AA%D8%B1-%D8%A7%DA%A9%D8%B3%DB%8C%DA%98%D9%86-%D8%B3%D9%86%D8%AC",
        "children": []
      },
      {
        "title": "پدهای طبی",
        "url": "https://basalam.com/cat/health/%D9%BE%D8%AF%D9%87%D8%A7%DB%8C-%D8%B7%D8%A8%DB%8C",
        "children": []
      },
      {
        "title": "کالای خواب و استراحت طبی",
        "url": "https://basalam.com/cat/health/%DA%A9%D8%A7%D9%84%D8%A7%DB%8C-%D8%AE%D9%88%D8%A7%D8%A8-%D8%A7%D8%B3%D8%AA%D8%B1%D8%A7%D8%AD%D8%AA-%D8%B7%D8%A8%DB%8C",
        "children": []
      },
      {
        "title": "کمپرس سرد و گرم",
        "url": "https://basalam.com/cat/health/%DA%A9%D9%85%D9%BE%D8%B1%D8%B3-%D8%B3%D8%B1%D8%AF-%DA%AF%D8%B1%D9%85",
        "children": []
      }
    ]
  },
  {
    "title": "کالای دیجیتال",
    "url": "https://basalam.com/cat/digital",
    "children": [
      {
        "title": "گوشی موبایل",
        "url": "https://basalam.com/cat/digital/%DA%AF%D9%88%D8%B4%DB%8C-%D9%85%D9%88%D8%A8%D8%A7%DB%8C%D9%84",
        "children": []
      },
      {
        "title": "تبلت و لوازم جانبی",
        "url": "https://basalam.com/cat/digital/%D8%AA%D8%A8%D9%84%D8%AA-%D9%84%D9%88%D8%A7%D8%B2%D9%85-%D8%AC%D8%A7%D9%86%D8%A8%DB%8C",
        "children": []
      },
      {
        "title": "لپ تاپ و لوازم جانبی",
        "url": "https://basalam.com/cat/digital/%D9%84%D9%BE-%D8%AA%D8%A7%D9%BE-%D9%84%D9%88%D8%A7%D8%B2%D9%85-%D8%AC%D8%A7%D9%86%D8%A8%DB%8C",
        "children": []
      },
      {
        "title": "هدفون، هدست و هندزفری",
        "url": "https://basalam.com/cat/digital/%D9%87%D8%AF%D9%81%D9%88%D9%86-%D9%87%D8%AF%D8%B3%D8%AA-%D9%87%D9%86%D8%AF%D8%B2%D9%81%D8%B1%DB%8C",
        "children": []
      },
      {
        "title": "کامپیوتر و تجهیزات جانبی",
        "url": "https://basalam.com/cat/digital/%DA%A9%D8%A7%D9%85%D9%BE%DB%8C%D9%88%D8%AA%D8%B1-%D8%AA%D8%AC%D9%87%DB%8C%D8%B2%D8%A7%D8%AA-%D8%AC%D8%A7%D9%86%D8%A8%DB%8C",
        "children": []
      },
      {
        "title": "دوربین عکاسی و فیلم برداری",
        "url": "https://basalam.com/cat/digital/%D8%AF%D9%88%D8%B1%D8%A8%DB%8C%D9%86-%D8%B9%DA%A9%D8%A7%D8%B3%DB%8C-%D9%81%DB%8C%D9%84%D9%85-%D8%A8%D8%B1%D8%AF%D8%A7%D8%B1%DB%8C",
        "children": []
      },
      {
        "title": "ساعت و مچ بند هوشمند",
        "url": "https://basalam.com/cat/digital/%D8%B3%D8%A7%D8%B9%D8%AA-%D9%85%DA%86-%D8%A8%D9%86%D8%AF-%D9%87%D9%88%D8%B4%D9%85%D9%86%D8%AF",
        "children": []
      },
      {
        "title": "کنسول بازی و لوازم جانبی",
        "url": "https://basalam.com/cat/digital/%DA%A9%D9%86%D8%B3%D9%88%D9%84-%D8%A8%D8%A7%D8%B2%DB%8C-%D9%84%D9%88%D8%A7%D8%B2%D9%85-%D8%AC%D8%A7%D9%86%D8%A8%DB%8C",
        "children": []
      },
      {
        "title": "ماشین های اداری",
        "url": "https://basalam.com/cat/digital/%D9%85%D8%A7%D8%B4%DB%8C%D9%86-%D9%87%D8%A7%DB%8C-%D8%A7%D8%AF%D8%A7%D8%B1%DB%8C",
        "children": []
      },
      {
        "title": "لوازم جانبی گوشی موبایل",
        "url": "https://basalam.com/cat/digital/%D9%84%D9%88%D8%A7%D8%B2%D9%85-%D8%AC%D8%A7%D9%86%D8%A8%DB%8C-%DA%AF%D9%88%D8%B4%DB%8C-%D9%85%D9%88%D8%A8%D8%A7%DB%8C%D9%84",
        "children": []
      },
      {
        "title": "تجهیزات امنیتی و نظارتی",
        "url": "https://basalam.com/cat/digital/%D8%AA%D8%AC%D9%87%DB%8C%D8%B2%D8%A7%D8%AA-%D8%A7%D9%85%D9%86%DB%8C%D8%AA%DB%8C-%D9%86%D8%B8%D8%A7%D8%B1%D8%AA%DB%8C",
        "children": []
      },
      {
        "title": "باتری و لوازم جانبی",
        "url": "https://basalam.com/cat/digital/%D8%A8%D8%A7%D8%AA%D8%B1%DB%8C-%D9%84%D9%88%D8%A7%D8%B2%D9%85-%D8%AC%D8%A7%D9%86%D8%A8%DB%8C",
        "children": []
      },
      {
        "title": "لوازم جانبی صوتی و تصویری",
        "url": "https://basalam.com/cat/digital/%D9%84%D9%88%D8%A7%D8%B2%D9%85-%D8%AC%D8%A7%D9%86%D8%A8%DB%8C-%D8%B5%D9%88%D8%AA%DB%8C-%D8%AA%D8%B5%D9%88%DB%8C%D8%B1%DB%8C",
        "children": []
      },
      {
        "title": "تجهیزات استودیویی",
        "url": "https://basalam.com/cat/digital/%D8%AA%D8%AC%D9%87%DB%8C%D8%B2%D8%A7%D8%AA-%D8%A7%D8%B3%D8%AA%D9%88%D8%AF%DB%8C%D9%88%DB%8C%DB%8C",
        "children": []
      },
      {
        "title": "گوشی موبایل آیفون",
        "url": "https://basalam.com/cat/digital/brand-%DA%AF%D9%88%D8%B4%DB%8C-%D9%85%D9%88%D8%A8%D8%A7%DB%8C%D9%84-%D8%A2%DB%8C%D9%81%D9%88%D9%86",
        "children": []
      },
      {
        "title": "گوشی موبایل سامسونگ",
        "url": "https://basalam.com/cat/digital/brand-%DA%AF%D9%88%D8%B4%DB%8C-%D9%85%D9%88%D8%A8%D8%A7%DB%8C%D9%84-%D8%B3%D8%A7%D9%85%D8%B3%D9%88%D9%86%DA%AF",
        "children": []
      },
      {
        "title": "گوشی موبایل شیائومی",
        "url": "https://basalam.com/cat/digital/brand-%DA%AF%D9%88%D8%B4%DB%8C-%D9%85%D9%88%D8%A8%D8%A7%DB%8C%D9%84-%D8%B4%DB%8C%D8%A7%D8%A6%D9%88%D9%85%DB%8C",
        "children": []
      },
      {
        "title": "گوشی موبایل نوکیا",
        "url": "https://basalam.com/cat/digital/brand-%DA%AF%D9%88%D8%B4%DB%8C-%D9%85%D9%88%D8%A8%D8%A7%DB%8C%D9%84-%D9%86%D9%88%DA%A9%DB%8C%D8%A7",
        "children": []
      },
      {
        "title": "گوشی موبایل هوآوی",
        "url": "https://basalam.com/cat/digital/brand-%DA%AF%D9%88%D8%B4%DB%8C-%D9%85%D9%88%D8%A8%D8%A7%DB%8C%D9%84-%D9%87%D9%88%D8%A2%D9%88%DB%8C",
        "children": []
      },
      {
        "title": "گوشی موبایل کاجیتل",
        "url": "https://basalam.com/cat/digital/brand-%DA%AF%D9%88%D8%B4%DB%8C-%D9%85%D9%88%D8%A8%D8%A7%DB%8C%D9%84-%DA%A9%D8%A7%D8%AC%DB%8C%D8%AA%D9%84",
        "children": []
      },
      {
        "title": "گوشی موبایل جی ال ایکس",
        "url": "https://basalam.com/cat/digital/brand-%DA%AF%D9%88%D8%B4%DB%8C-%D9%85%D9%88%D8%A8%D8%A7%DB%8C%D9%84-%D8%AC%DB%8C-%D8%A7%D9%84-%D8%A7%DB%8C%DA%A9%D8%B3",
        "children": []
      },
      {
        "title": "گوشی موبایل هوپ",
        "url": "https://basalam.com/cat/digital/brand-%DA%AF%D9%88%D8%B4%DB%8C-%D9%85%D9%88%D8%A8%D8%A7%DB%8C%D9%84-%D9%87%D9%88%D9%BE",
        "children": []
      },
      {
        "title": "گوشی موبایل ال جی",
        "url": "https://basalam.com/cat/digital/brand-%DA%AF%D9%88%D8%B4%DB%8C-%D9%85%D9%88%D8%A8%D8%A7%DB%8C%D9%84-%D8%A7%D9%84-%D8%AC%DB%8C",
        "children": []
      },
      {
        "title": "گوشی موبایل آنر",
        "url": "https://basalam.com/cat/digital/brand-%DA%AF%D9%88%D8%B4%DB%8C-%D9%85%D9%88%D8%A8%D8%A7%DB%8C%D9%84-%D8%A2%D9%86%D8%B1",
        "children": []
      },
      {
        "title": "گوشی موبایل سونی",
        "url": "https://basalam.com/cat/digital/brand-%DA%AF%D9%88%D8%B4%DB%8C-%D9%85%D9%88%D8%A8%D8%A7%DB%8C%D9%84-%D8%B3%D9%88%D9%86%DB%8C",
        "children": []
      },
      {
        "title": "گوشی موبایل ریلمی",
        "url": "https://basalam.com/cat/digital/brand-%DA%AF%D9%88%D8%B4%DB%8C-%D9%85%D9%88%D8%A8%D8%A7%DB%8C%D9%84-%D8%B1%DB%8C%D9%84%D9%85%DB%8C",
        "children": []
      },
      {
        "title": "گوشی موبایل ورتو",
        "url": "https://basalam.com/cat/digital/brand-%DA%AF%D9%88%D8%B4%DB%8C-%D9%85%D9%88%D8%A8%D8%A7%DB%8C%D9%84-%D9%88%D8%B1%D8%AA%D9%88",
        "children": []
      },
      {
        "title": "سایر گوشی های موبایل",
        "url": "https://basalam.com/cat/digital/%D8%B3%D8%A7%DB%8C%D8%B1-%DA%AF%D9%88%D8%B4%DB%8C-%D9%87%D8%A7%DB%8C-%D9%85%D9%88%D8%A8%D8%A7%DB%8C%D9%84",
        "children": []
      }
    ]
  },
  {
    "title": "کودک و نوزاد و اسباب بازی",
    "url": "https://basalam.com/cat/kids",
    "children": [
      {
        "title": "اسباب بازی و سرگرمی",
        "url": "https://basalam.com/cat/kids/%D8%A7%D8%B3%D8%A8%D8%A7%D8%A8-%D8%A8%D8%A7%D8%B2%DB%8C-%D8%B3%D8%B1%DA%AF%D8%B1%D9%85%DB%8C",
        "children": []
      },
      {
        "title": "لوازم کودک و نوزاد",
        "url": "https://basalam.com/cat/kids/%D9%84%D9%88%D8%A7%D8%B2%D9%85-%DA%A9%D9%88%D8%AF%DA%A9-%D9%86%D9%88%D8%B2%D8%A7%D8%AF",
        "children": []
      },
      {
        "title": "اسباب بازی بر اساس شخصیت",
        "url": "https://basalam.com/cat/kids/%D8%A7%D8%B3%D8%A8%D8%A7%D8%A8-%D8%A8%D8%A7%D8%B2%DB%8C-%D8%A8%D8%B1-%D8%A7%D8%B3%D8%A7%D8%B3-%D8%B4%D8%AE%D8%B5%DB%8C%D8%AA",
        "children": []
      },
      {
        "title": "اسباب بازی حیوانات",
        "url": "https://basalam.com/cat/kids/%D8%A7%D8%B3%D8%A8%D8%A7%D8%A8-%D8%A8%D8%A7%D8%B2%DB%8C-%D8%AD%DB%8C%D9%88%D8%A7%D9%86%D8%A7%D8%AA",
        "children": []
      },
      {
        "title": "اسباب بازی شارژی",
        "url": "https://basalam.com/cat/kids/%D8%A7%D8%B3%D8%A8%D8%A7%D8%A8-%D8%A8%D8%A7%D8%B2%DB%8C-%D8%B4%D8%A7%D8%B1%DA%98%DB%8C",
        "children": []
      },
      {
        "title": "اسباب بازی موزیکال",
        "url": "https://basalam.com/cat/kids/%D8%A7%D8%B3%D8%A8%D8%A7%D8%A8-%D8%A8%D8%A7%D8%B2%DB%8C-%D9%85%D9%88%D8%B2%DB%8C%DA%A9%D8%A7%D9%84",
        "children": []
      },
      {
        "title": "اسباب بازی وسایل نقلیه",
        "url": "https://basalam.com/cat/kids/%D8%A7%D8%B3%D8%A8%D8%A7%D8%A8-%D8%A8%D8%A7%D8%B2%DB%8C-%D9%88%D8%B3%D8%A7%DB%8C%D9%84-%D9%86%D9%82%D9%84%DB%8C%D9%87",
        "children": []
      },
      {
        "title": "اسباب بازی کنترلی",
        "url": "https://basalam.com/cat/kids/%D8%A7%D8%B3%D8%A8%D8%A7%D8%A8-%D8%A8%D8%A7%D8%B2%DB%8C-%DA%A9%D9%86%D8%AA%D8%B1%D9%84%DB%8C",
        "children": []
      },
      {
        "title": "بازی های فکری و ساختنی",
        "url": "https://basalam.com/cat/kids/%D8%A8%D8%A7%D8%B2%DB%8C-%D9%87%D8%A7%DB%8C-%D9%81%DA%A9%D8%B1%DB%8C-%D8%B3%D8%A7%D8%AE%D8%AA%D9%86%DB%8C",
        "children": []
      },
      {
        "title": "بازی‌های مهارتی و خلاقانه",
        "url": "https://basalam.com/cat/kids/%D8%A8%D8%A7%D8%B2%DB%8C-%D9%87%D8%A7%DB%8C-%D9%85%D9%87%D8%A7%D8%B1%D8%AA%DB%8C-%D8%AE%D9%84%D8%A7%D9%82%D8%A7%D9%86%D9%87",
        "children": []
      },
      {
        "title": "تفنگ و اسباب بازی مبارزه",
        "url": "https://basalam.com/cat/kids/%D8%AA%D9%81%D9%86%DA%AF-%D8%A7%D8%B3%D8%A8%D8%A7%D8%A8-%D8%A8%D8%A7%D8%B2%DB%8C-%D9%85%D8%A8%D8%A7%D8%B1%D8%B2%D9%87",
        "children": []
      },
      {
        "title": "سایر اسباب بازی و سرگرمی",
        "url": "https://basalam.com/cat/kids/%D8%B3%D8%A7%DB%8C%D8%B1-%D8%A7%D8%B3%D8%A8%D8%A7%D8%A8-%D8%A8%D8%A7%D8%B2%DB%8C-%D8%B3%D8%B1%DA%AF%D8%B1%D9%85%DB%8C",
        "children": []
      },
      {
        "title": "عروسک",
        "url": "https://basalam.com/cat/kids/%D8%B9%D8%B1%D9%88%D8%B3%DA%A9",
        "children": []
      },
      {
        "title": "لوازم بازی و تحرک کودک",
        "url": "https://basalam.com/cat/kids/%D9%84%D9%88%D8%A7%D8%B2%D9%85-%D8%A8%D8%A7%D8%B2%DB%8C-%D8%AA%D8%AD%D8%B1%DA%A9-%DA%A9%D9%88%D8%AF%DA%A9",
        "children": []
      },
      {
        "title": "لوازم شوخی و سرگرمی",
        "url": "https://basalam.com/cat/kids/%D9%84%D9%88%D8%A7%D8%B2%D9%85-%D8%B4%D9%88%D8%AE%DB%8C-%D8%B3%D8%B1%DA%AF%D8%B1%D9%85%DB%8C",
        "children": []
      }
    ]
  },
  {
    "title": "ورزش و سفر",
    "url": "https://basalam.com/cat/sport",
    "children": [
      {
        "title": "تجهیزات اسکان",
        "url": "https://basalam.com/cat/sport/%D8%AA%D8%AC%D9%87%DB%8C%D8%B2%D8%A7%D8%AA-%D8%A7%D8%B3%DA%A9%D8%A7%D9%86",
        "children": []
      },
      {
        "title": "تجهیزات کمپینگ",
        "url": "https://basalam.com/cat/sport/%D8%AA%D8%AC%D9%87%DB%8C%D8%B2%D8%A7%D8%AA-%DA%A9%D9%85%D9%BE%DB%8C%D9%86%DA%AF",
        "children": []
      },
      {
        "title": "لوازم ورزشی",
        "url": "https://basalam.com/cat/sport/%D9%84%D9%88%D8%A7%D8%B2%D9%85-%D9%88%D8%B1%D8%B2%D8%B4%DB%8C",
        "children": []
      },
      {
        "title": "چمدان مسافرتی",
        "url": "https://basalam.com/cat/sport/%DA%86%D9%85%D8%AF%D8%A7%D9%86-%D9%85%D8%B3%D8%A7%D9%81%D8%B1%D8%AA%DB%8C",
        "children": []
      },
      {
        "title": "تجهیزات خواب مسافرتی",
        "url": "https://basalam.com/cat/sport/%D8%AA%D8%AC%D9%87%DB%8C%D8%B2%D8%A7%D8%AA-%D8%AE%D9%88%D8%A7%D8%A8-%D9%85%D8%B3%D8%A7%D9%81%D8%B1%D8%AA%DB%8C",
        "children": []
      },
      {
        "title": "زیرانداز مسافرتی و پیک نیک",
        "url": "https://basalam.com/cat/sport/%D8%B2%DB%8C%D8%B1%D8%A7%D9%86%D8%AF%D8%A7%D8%B2-%D9%85%D8%B3%D8%A7%D9%81%D8%B1%D8%AA%DB%8C-%D9%BE%DB%8C%DA%A9-%D9%86%DB%8C%DA%A9",
        "children": []
      },
      {
        "title": "سایه بان",
        "url": "https://basalam.com/cat/sport/%D8%B3%D8%A7%DB%8C%D9%87-%D8%A8%D8%A7%D9%86",
        "children": []
      },
      {
        "title": "میز و صندلی تاشو و مسافرتی",
        "url": "https://basalam.com/cat/sport/%D9%85%DB%8C%D8%B2-%D8%B5%D9%86%D8%AF%D9%84%DB%8C-%D8%AA%D8%A7%D8%B4%D9%88-%D9%85%D8%B3%D8%A7%D9%81%D8%B1%D8%AA%DB%8C",
        "children": []
      },
      {
        "title": "چادر مسافرتی، کوهنوردی و کمپینگ",
        "url": "https://basalam.com/cat/sport/%DA%86%D8%A7%D8%AF%D8%B1-%D9%85%D8%B3%D8%A7%D9%81%D8%B1%D8%AA%DB%8C-%DA%A9%D9%88%D9%87%D9%86%D9%88%D8%B1%D8%AF%DB%8C-%DA%A9%D9%85%D9%BE%DB%8C%D9%86%DA%AF",
        "children": []
      },
      {
        "title": "کیسه خواب",
        "url": "https://basalam.com/cat/sport/%DA%A9%DB%8C%D8%B3%D9%87-%D8%AE%D9%88%D8%A7%D8%A8",
        "children": []
      }
    ]
  },
  {
    "title": "طلا و جواهرات",
    "url": "https://basalam.com/cat/gold",
    "children": [
      {
        "title": "سکه طلا",
        "url": "https://basalam.com/cat/gold/%D8%B3%DA%A9%D9%87-%D8%B7%D9%84%D8%A7",
        "children": []
      },
      {
        "title": "زیورآلات طلا",
        "url": "https://basalam.com/cat/gold/%D8%B2%DB%8C%D9%88%D8%B1%D8%A2%D9%84%D8%A7%D8%AA-%D8%B7%D9%84%D8%A7",
        "children": []
      },
      {
        "title": "شمش طلا",
        "url": "https://basalam.com/cat/gold/%D8%B4%D9%85%D8%B4-%D8%B7%D9%84%D8%A7",
        "children": []
      }
    ]
  }
]
"""

# اگر داده‌ها را در فایل ذخیره کرده‌اید، می‌توانید به جای json_input از کد زیر استفاده کنید:
# with open('data.json', 'r', encoding='utf-8') as f:
#     json_input = f.read()

try:
    # تبدیل رشته JSON به آبجکت پایتون
    data_structure = json.loads(json_input)
    
    # پردازش داده‌ها
    result = json_to_csv_structure(data_structure)
    
    # ذخیره در فایل CSV
    save_to_csv(result)
    
except json.JSONDecodeError as e:
    print("خطا در خواندن فایل JSON: لطفاً مطمئن شوید فرمت JSON صحیح است.")
    print(e)
except Exception as e:
    print(f"یک خطای غیرمنتظره رخ داد: {e}")