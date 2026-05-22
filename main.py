import PySimpleGUI as sg
import threading
import os
import sys
import json
import asyncio
from datetime import datetime
from pathlib import Path

# ===========================
# COLOR & STYLE CONFIG
# ===========================
DARK_BG = '#0d1117'
DARKER_BG = '#010409'
CARD_BG = '#161b22'
ACCENT_COLOR = '#58a6ff'
SUCCESS_COLOR = '#3fb950'
ERROR_COLOR = '#f85149'
WARNING_COLOR = '#d29922'
TEXT_COLOR = '#c9d1d9'
SECONDARY_TEXT = '#8b949e'

# ===========================
# SETUP LOGGERS
# ===========================
LOG_FILE = Path('output') / f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
Path('output').mkdir(exist_ok=True)

class Logger:
    def __init__(self):
        self.logs = []
    
    def log(self, message, color='white'):
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_msg = f"[{timestamp}] {message}"
        self.logs.append(log_msg)
        print(f"\033[{self._get_color_code(color)}m{log_msg}\033[0m")
        self._save_to_file(log_msg)
    
    def _get_color_code(self, color):
        colors = {
            'green': 32,
            'red': 31,
            'yellow': 33,
            'cyan': 36,
            'white': 37
        }
        return colors.get(color, 37)
    
    def _save_to_file(self, message):
        try:
            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(message + '\n')
        except:
            pass
    
    def clear(self):
        self.logs = []

# ===========================
# FILE SIZE MANAGEMENT
# ===========================
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

class FileManager:
    @staticmethod
    def check_and_split_file(filepath):
        """اگر فایل بیشتر از 5MB باشد، تقسیم کند"""
        if not os.path.exists(filepath):
            return
        
        file_size = os.path.getsize(filepath)
        if file_size > MAX_FILE_SIZE:
            base_path = filepath.rsplit('.', 1)[0]
            ext = filepath.rsplit('.', 1)[1] if '.' in filepath else 'json'
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            os.remove(filepath)
            
            chunk_size = len(content) // (file_size // MAX_FILE_SIZE + 1)
            for i, chunk in enumerate([content[j:j+chunk_size] for j in range(0, len(content), chunk_size)]):
                new_path = f"{base_path}_part{i+1}.{ext}"
                with open(new_path, 'w', encoding='utf-8') as f:
                    f.write(chunk)

class DuplicateChecker:
    def __init__(self):
        self.seen_items = set()
        self.database_file = Path('output') / 'seen_items.json'
        self.load_database()
    
    def load_database(self):
        """قبلی‌های ذخیره شده را لود کند"""
        if self.database_file.exists():
            try:
                with open(self.database_file, 'r', encoding='utf-8') as f:
                    self.seen_items = set(json.load(f))
            except:
                self.seen_items = set()
    
    def is_duplicate(self, item_id):
        """چک کند آیا item تکراری است"""
        return item_id in self.seen_items
    
    def add_item(self, item_id):
        """یک item جدید اضافه کند"""
        self.seen_items.add(item_id)
        self.save_database()
    
    def save_database(self):
        """database رو ذخیره کند"""
        try:
            with open(self.database_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.seen_items), f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def clear(self):
        """database رو پاک کند"""
        self.seen_items = set()
        if self.database_file.exists():
            os.remove(self.database_file)

# ===========================
# CATEGORY LOADER
# ===========================
class CategoryManager:
    def __init__(self):
        self.categories_map = self._load_all_categories()
    
    def _load_all_categories(self):
        """تمام کتگوری‌ها را لود کند"""
        categories = {
            'Digikala': self._load_category('digikala'),
            'Emalls': self._load_category('emalls'),
            'Isam': self._load_category('isam'),
            'Pindo': self._load_category('pindo'),
            'Shapino': self._load_category('shapino'),
            'Snap Shop': self._load_category('snap_shop'),
            'Torob': self._load_category('torob'),
            'Basalam': self._load_category('basalam'),
        }
        return categories
    
    def _load_category(self, shop_name):
        """کتگوری‌های یک فروشگاه را لود کند"""
        try:
            module = __import__(f'categori.{shop_name}_categori', fromlist=['get_categories'])
            categories = module.get_categories()
            return categories if categories else []
        except Exception as e:
            print(f"خطا در بارگذاری دسته‌بندی {shop_name}: {e}")
            return []
    
    def get_categories(self, shop_name):
        """کتگوری‌های یک فروشگاه را برگرداند"""
        return self.categories_map.get(shop_name, [])

# ===========================
# SCRAPER RUNNER
# ===========================
class ScraperRunner:
    @staticmethod
    def run_digikala_url(url, logger, stop_event):
        """اجرای اسکریپر دیجی‌کالا برای URL مستقیم"""
        try:
            import digikala_scraper
            asyncio.run(digikala_scraper.scrape_digikala_url(url, logger, stop_event))
        except Exception as e:
            logger.log(f'✗ خطا: {str(e)}', 'red')
            raise

    @staticmethod
    def run_torob_categories(logger, stop_event):
        """اجرای اسکریپر تورب برای دسته‌بندی‌ها"""
        try:
            import torob_scraper
            asyncio.run(torob_scraper.main(logger, stop_event))
        except Exception as e:
            logger.log(f'✗ خطا: {str(e)}', 'red')
            raise

# ===========================
# MAIN APPLICATION
# ===========================
def main():
    # Dark theme setup
    sg.theme('Dark')
    sg.set_options(
        font=('Segoe UI', 10),
        text_color=TEXT_COLOR,
        background_color=DARK_BG,
        element_background_color=CARD_BG,
    )

    # ============= MODE SELECTION =============
    mode_section = [
        [sg.Text('انتخاب حالت:', font=('Segoe UI', 11, 'bold'), text_color=ACCENT_COLOR)],
        [
            sg.Radio('🏪 آدرس مستقیم (URL)', 'MODE', key='MODE_URL', default=True, 
                    font=('Segoe UI', 10), background_color=DARK_BG, text_color=TEXT_COLOR,
                    enable_events=True),
            sg.Radio('📂 دسته‌بندی (Category)', 'MODE', key='MODE_CATEGORY',
                    font=('Segoe UI', 10), background_color=DARK_BG, text_color=TEXT_COLOR,
                    enable_events=True),
        ],
    ]

    # ============= INPUT SECTION - URL MODE =============
    url_input = [
        [sg.Text('انتخاب فروشگاه:', font=('Segoe UI', 10, 'bold'), text_color=ACCENT_COLOR)],
        [sg.Combo(
            ['Digikala', 'Emalls', 'Isam', 'Pindo', 'Shapino', 'Snap Shop', 'Torob', 'Basalam'],
            key='SHOP',
            default_value='Digikala',
            size=(40, 1),
            font=('Segoe UI', 10),
            readonly=True
        )],
        [sg.Text('چسباندن لینک (Ctrl+V):', font=('Segoe UI', 10, 'bold'), text_color=ACCENT_COLOR)],
        [sg.Input(
            key='URL',
            size=(60, 1),
            font=('Segoe UI', 10),
            border_width=2,
            do_not_clear=True
        )],
    ]

    # ============= INPUT SECTION - CATEGORY MODE =============
    category_input = [
        [sg.Text('انتخاب فروشگاه:', font=('Segoe UI', 10, 'bold'), text_color=ACCENT_COLOR, visible=False, key='CAT_SHOP_LABEL')],
        [sg.Combo(
            ['Digikala', 'Emalls', 'Isam', 'Pindo', 'Shapino', 'Snap Shop', 'Torob', 'Basalam'],
            key='SHOP_CAT',
            default_value='Torob',
            size=(40, 1),
            font=('Segoe UI', 10),
            readonly=True,
            enable_events=True,
            visible=False
        )],
        [sg.Text('انتخاب دسته‌بندی:', font=('Segoe UI', 10, 'bold'), text_color=ACCENT_COLOR, visible=False, key='CAT_LABEL')],
        [sg.Combo(
            [],
            key='CATEGORY',
            default_value='',
            size=(40, 1),
            font=('Segoe UI', 10),
            readonly=True,
            visible=False
        )],
    ]

    # ============= BUTTON SECTION =============
    buttons = [
        [
            sg.Button('▶ شروع', key='START', font=('Segoe UI', 11, 'bold'), size=(16, 2),
                     button_color=(DARK_BG, SUCCESS_COLOR), border_width=2),
            sg.Button('⏹ توقف', key='STOP', font=('Segoe UI', 11, 'bold'), size=(10, 2),
                     button_color=(DARK_BG, ERROR_COLOR), border_width=2, disabled=True),
            sg.Button('📁 باز کردن', key='OPEN', font=('Segoe UI', 11, 'bold'), size=(14, 2),
                     button_color=(DARK_BG, ACCENT_COLOR), border_width=2),
            sg.Button('🗑 پاک کردن', key='CLEAR', font=('Segoe UI', 11, 'bold'), size=(12, 2),
                     button_color=(DARK_BG, WARNING_COLOR), border_width=2),
            sg.Button('✕ خروج', key='EXIT', font=('Segoe UI', 11, 'bold'), size=(10, 2),
                     button_color=(DARK_BG, '#555555'), border_width=2),
        ]
    ]

    # ============= CONSOLE SECTION =============
    console = [
        [sg.Text('📊 خروجی کنسول:', font=('Segoe UI', 11, 'bold'), text_color=ACCENT_COLOR)],
        [sg.Multiline(
            size=(120, 16),
            key='OUTPUT',
            font=('Courier New', 9),
            autoscroll=True,
            background_color=DARKER_BG,
            text_color=TEXT_COLOR,
            border_width=2
        )],
    ]

    # ============= STATUS BAR =============
    status = [
        [
            sg.Text('وضعیت:', font=('Segoe UI', 10, 'bold'), text_color=ACCENT_COLOR, size=(8, 1)),
            sg.Text('آماده', key='STATUS', font=('Segoe UI', 10, 'bold'), text_color=SUCCESS_COLOR, size=(25, 1)),
            sg.Text('│', text_color=SECONDARY_TEXT),
            sg.ProgressBar(100, size=(30, 15), key='PROGRESS',
                          bar_color=(SUCCESS_COLOR, CARD_BG), border_width=1),
            sg.Text('', key='PROGRESS_TEXT', font=('Segoe UI', 9), text_color=SECONDARY_TEXT, size=(15, 1))
        ]
    ]

    # ============= FINAL LAYOUT =============
    layout = [
        [sg.Text('█ وب اسکریپر پرو', font=('Segoe UI', 28, 'bold'), text_color=ACCENT_COLOR, background_color=DARK_BG)],
        [sg.Text('━' * 80, text_color=ACCENT_COLOR, background_color=DARK_BG)],
        [sg.Text()],
        mode_section,
        [sg.Text()],
        url_input,
        category_input,
        [sg.Text()],
        buttons,
        [sg.Text()],
        console,
        [sg.Text()],
        status,
    ]

    window = sg.Window(
        'Web Scraper Pro',
        layout,
        size=(1400, 950),
        background_color=DARK_BG,
        finalize=True,
        resizable=True
    )

    logger = Logger()
    duplicate_checker = DuplicateChecker()
    category_manager = CategoryManager()
    scraper_thread = None
    is_running = False
    stop_event = threading.Event()

    logger.log('▸ برنامه شروع شد', 'cyan')
    logger.log('▸ آماده برای اسکریپ وب', 'green')
    window['OUTPUT'].update('▸ برنامه شروع شد\n▸ آماده برای اسکریپ وب\n')

    def update_status(text, color='white'):
        window['STATUS'].update(text, text_color=color)

    def update_output(text):
        current = window['OUTPUT'].get()
        window['OUTPUT'].update(current + text + '\n')

    def toggle_mode():
        """بین دو حالت تبدیل کند"""
        is_url_mode = values['MODE_URL']
        
        # URL mode elements
        window['SHOP'].update(visible=is_url_mode)
        window['URL'].update(visible=is_url_mode)
        
        # Category mode elements
        window['CAT_SHOP_LABEL'].update(visible=not is_url_mode)
        window['SHOP_CAT'].update(visible=not is_url_mode)
        window['CAT_LABEL'].update(visible=not is_url_mode)
        window['CATEGORY'].update(visible=not is_url_mode)
        
        if not is_url_mode:
            update_categories_dropdown()

    def update_categories_dropdown():
        """کتگوری‌های انتخاب شده فروشگاه را به‌روزرسانی کند"""
        shop = values['SHOP_CAT']
        categories = category_manager.get_categories(shop)
        if categories:
            window['CATEGORY'].update(values=categories, value=categories[0])
        else:
            window['CATEGORY'].update(values=[], value='')

    def run_scraper(shop_name, mode, url=None, category=None):
        nonlocal is_running
        is_running = True
        window['START'].update(disabled=True)
        window['STOP'].update(disabled=False)
        stop_event.clear()
        
        try:
            if mode == 'url':
                update_status(f'درحال اسکریپ {shop_name}...', 'yellow')
                msg = f'\n{"═"*100}\n▶ شروع اسکریپ از {shop_name}\n🔗 آدرس: {url}\n{"═"*100}\n'
                update_output(msg)
                logger.log(f'▶ شروع اسکریپ از {shop_name}', 'cyan')
                logger.log(f'🔗 آدرس: {url}', 'cyan')
                
                # Run Digikala scraper for URL mode
                if shop_name.lower() == 'digikala':
                    try:
                        ScraperRunner.run_digikala_url(url, logger, stop_event)
                    except Exception as e:
                        logger.log(f'✗ خطا در اسکریپ: {str(e)}', 'red')
                        update_status(f'✗ خطا: {str(e)[:40]}', 'red')
                        return
                else:
                    logger.log(f'✗ فروشگاه {shop_name} برای حالت URL پشتیبانی نمی‌شود', 'red')
                    update_status(f'✗ پشتیبانی نشده', 'red')
                    return
            
            else:  # category mode
                update_status(f'درحال اسکریپ {shop_name} - دسته‌بندی‌ها...', 'yellow')
                msg = f'\n{"═"*100}\n▶ شروع اسکریپ از {shop_name}\n📂 حالت: دسته‌بندی‌ها\n{"═"*100}\n'
                update_output(msg)
                logger.log(f'▶ شروع اسکریپ از {shop_name}', 'cyan')
                
                # Run category scraper
                if shop_name.lower() == 'torob':
                    try:
                        ScraperRunner.run_torob_categories(logger, stop_event)
                    except Exception as e:
                        logger.log(f'✗ خطا در اسکریپ: {str(e)}', 'red')
                        update_status(f'✗ خطا: {str(e)[:40]}', 'red')
                        return
                else:
                    logger.log(f'✗ فروشگاه {shop_name} برای حالت دسته‌بندی پشتیبانی نمی‌شود', 'red')
                    update_status(f'✗ پشتیبانی نشده', 'red')
                    return
            
            # Check and split files if needed
            if not stop_event.is_set():
                output_dir = Path('output')
                for file in output_dir.glob('*.json'):
                    FileManager.check_and_split_file(str(file))
                
                msg = f'\n{"═"*100}\n✓ اسکریپ با موفقیت تکمیل شد\n{"═"*100}\n'
                update_output(msg)
                logger.log(f'✓ اسکریپ با موفقیت تکمیل شد', 'green')
                update_status('✓ تکمیل شد', 'green')
            else:
                msg = f'\n{"═"*100}\n⚠ اسکریپ توسط کاربر متوقف شد\n{"═"*100}\n'
                update_output(msg)
                logger.log(f'⚠ اسکریپ توسط کاربر متوقف شد', 'yellow')
                update_status('⚠ متوقف شد', 'yellow')
            
        except Exception as e:
            msg = f'\n{"═"*100}\n✗ خطا: {str(e)}\n{"═"*100}\n'
            update_output(msg)
            logger.log(f'✗ خطا: {str(e)}', 'red')
            update_status(f'✗ خطا: {str(e)[:40]}', 'red')
            
        finally:
            is_running = False
            window['START'].update(disabled=False)
            window['STOP'].update(disabled=True)

    # ============= MAIN EVENT LOOP =============
    while True:
        event, values = window.read(timeout=100)

        if event == sg.WINDOW_CLOSED or event == 'EXIT':
            logger.log('▸ برنامه بسته شد', 'cyan')
            break

        # MODE CHANGED
        if event in ['MODE_URL', 'MODE_CATEGORY']:
            toggle_mode()

        # SHOP CHANGED IN CATEGORY MODE
        if event == 'SHOP_CAT':
            update_categories_dropdown()

        # START BUTTON
        if event == 'START':
            if values['MODE_URL']:  # URL Mode
                shop = values['SHOP']
                url = values['URL'].strip()

                if not url:
                    sg.popup_error('⚠️ لطفا یک آدرس وارد کنید!', background_color=CARD_BG, text_color=TEXT_COLOR)
                    update_status('خطا: آدرس خالی است', 'red')
                    logger.log('✗ خطا: آدرس خالی است', 'red')
                    continue

                if not url.startswith('http'):
                    sg.popup_error('⚠️ آدرس باید با http:// یا https:// شروع شود', background_color=CARD_BG, text_color=TEXT_COLOR)
                    update_status('خطا: آدرس نامعتبر', 'red')
                    logger.log('✗ خطا: فرمت آدرس نامعتبر است', 'red')
                    continue

                if is_running:
                    sg.popup_warning('⚠️ در حال اسکریپ!', background_color=CARD_BG, text_color=TEXT_COLOR)
                    continue

                logger.log(f'▸ شروع {shop}...', 'cyan')
                scraper_thread = threading.Thread(
                    target=run_scraper,
                    args=(shop, 'url', url),
                    daemon=True
                )
                scraper_thread.start()

            else:  # Category Mode
                shop = values['SHOP_CAT']

                if is_running:
                    sg.popup_warning('⚠️ در حال اسکریپ!', background_color=CARD_BG, text_color=TEXT_COLOR)
                    continue

                logger.log(f'▸ شروع {shop}...', 'cyan')
                scraper_thread = threading.Thread(
                    target=run_scraper,
                    args=(shop, 'category', None, None),
                    daemon=True
                )
                scraper_thread.start()

        # STOP BUTTON
        if event == 'STOP':
            if is_running:
                logger.log('⚠ توقف درخواست شده', 'yellow')
                update_output('⚠ اسکریپ توسط کاربر متوقف شد')
                update_status('درحال توقف...', 'yellow')
                stop_event.set()

        # OPEN FOLDER
        if event == 'OPEN':
            if os.path.exists('output'):
                try:
                    if sys.platform == 'win32':
                        os.startfile('output')
                    elif sys.platform == 'darwin':
                        os.system('open output')
                    else:
                        os.system('xdg-open output')
                    logger.log('▸ پوشه خروجی باز شد', 'green')
                except Exception as e:
                    logger.log(f'✗ خطا: {e}', 'red')
            else:
                logger.log('✗ پوشه خروجی یافت نشد', 'red')
                update_status('پوشه خروجی یافت نشد', 'red')

        # CLEAR LOGS
        if event == 'CLEAR':
            window['OUTPUT'].update('')
            logger.clear()
            logger.log('▸ کنسول پاک شد', 'cyan')
            window['OUTPUT'].update('▸ کنسول پاک شد\n')
            update_status('آماده', 'green')

    window.close()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n✗ برنامه توسط کاربر متوقف شد')
    except Exception as e:
        print(f'\n✗ خطای بحرانی: {e}')
