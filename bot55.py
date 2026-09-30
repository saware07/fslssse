import requests
import json
import base64
import uuid
import re
from datetime import datetime, timedelta
import os
import sys
import time
import logging
from io import BytesIO
from urllib.parse import urlparse
import PyPDF2
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import random
import string
from pymongo import MongoClient
from bson import ObjectId
import ddddocr
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import urllib.request
import gzip

# Fix Windows terminal encoding for Unicode output
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ocr_solver = ddddocr.DdddOcr(show_ad=False)
ocr_solver_beta = ddddocr.DdddOcr(beta=True, show_ad=False)
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["WDM_LOG"] = "0"

# ============== PROXY CONFIG ==============
# -----------------------------------------------------------------------
# UIDAI (tathya.uidai.gov.in) is often blocked on datacenter/VPS IPs.
# If captchas keep timing out, paste a working HTTP proxy below.
# Format:  "http://user:pass@host:port"   or   "http://host:port"
# Leave as empty string "" to run without proxy (direct connection).
# Set the UIDAI_PROXY environment variable in Railway to override.
# -----------------------------------------------------------------------
DEFAULT_PROXY = ""
UIDAI_PROXY = DEFAULT_PROXY

# BrightData proxies removed - blocked on .gov.in
# OwlProxy SOCKS5 Indian Residential Pool (rotating)
PROXY_POOL = [
    "socks5h://hUKy5wBHnU20_custom_zone_IN_st__city_sid_09984885_time_5:5546964@change5.owlproxy.com:7778",
    "socks5h://hUKy5wBHnU20_custom_zone_IN_st__city_sid_71037315_time_5:5546964@change5.owlproxy.com:7778",
    "socks5h://hUKy5wBHnU20_custom_zone_IN_st__city_sid_89862918_time_5:5546964@change5.owlproxy.com:7778",
    "socks5h://hUKy5wBHnU20_custom_zone_IN_st__city_sid_57951696_time_5:5546964@change5.owlproxy.com:7778",
    "socks5h://hUKy5wBHnU20_custom_zone_IN_st__city_sid_16486961_time_5:5546964@change5.owlproxy.com:7778",
    "socks5h://hUKy5wBHnU20_custom_zone_IN_st__city_sid_38354839_time_5:5546964@change5.owlproxy.com:7778",
    "socks5h://hUKy5wBHnU20_custom_zone_IN_st__city_sid_98755190_time_5:5546964@change5.owlproxy.com:7778",
    "socks5h://hUKy5wBHnU20_custom_zone_IN_st__city_sid_88999949_time_5:5546964@change5.owlproxy.com:7778",
    "socks5h://hUKy5wBHnU20_custom_zone_IN_st__city_sid_69924687_time_5:5546964@change5.owlproxy.com:7778",
    "socks5h://hUKy5wBHnU20_custom_zone_IN_st__city_sid_49915585_time_5:5546964@change5.owlproxy.com:7778",
    "socks5h://hUKy5wBHnU20_custom_zone_IN_st__city_sid_89421933_time_5:5546964@change5.owlproxy.com:7778",
    "socks5h://hUKy5wBHnU20_custom_zone_IN_st__city_sid_82512271_time_5:5546964@change5.owlproxy.com:7778",
    "socks5h://hUKy5wBHnU20_custom_zone_IN_st__city_sid_76132434_time_5:5546964@change5.owlproxy.com:7778",
    "socks5h://hUKy5wBHnU20_custom_zone_IN_st__city_sid_30829003_time_5:5546964@change5.owlproxy.com:7778",
    "socks5h://hUKy5wBHnU20_custom_zone_IN_st__city_sid_20255525_time_5:5546964@change5.owlproxy.com:7778",
    "socks5h://hUKy5wBHnU20_custom_zone_IN_st__city_sid_76190484_time_5:5546964@change5.owlproxy.com:7778",
    "socks5h://hUKy5wBHnU20_custom_zone_IN_st__city_sid_08452203_time_5:5546964@change5.owlproxy.com:7778",
    "socks5h://hUKy5wBHnU20_custom_zone_IN_st__city_sid_20127759_time_5:5546964@change5.owlproxy.com:7778",
    "socks5h://hUKy5wBHnU20_custom_zone_IN_st__city_sid_12233140_time_5:5546964@change5.owlproxy.com:7778",
    "socks5h://hUKy5wBHnU20_custom_zone_IN_st__city_sid_06945751_time_5:5546964@change5.owlproxy.com:7778",
]

use_proxy = bool(PROXY_POOL)
PROXY_CONFIG = {
    'use_proxy': use_proxy,
    'http': PROXY_POOL[0] if PROXY_POOL else '',
    'https': PROXY_POOL[0] if PROXY_POOL else ''
}

# ============== PAN SELENIUM PROXY CONFIG ==============
PAN_PROXY_HOST = "vr2-resi.proxy.arealproxy.com"
PAN_PROXY_PORT = "1337"
PAN_PROXY_USER = "e1nvi3ldfzn0_fastmode-true_country-IN"
PAN_PROXY_PASS = "jkaJ7Tlo3yF9btyu"

PAN_USER_AGENTS = [
    {'label': 'Chrome 124 / Windows 11', 'ua': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36', 'platform': 'Win32', 'vendor': 'Google Inc.', 'languages': ['en-US', 'en']},
    {'label': 'Chrome 123 / Windows 10', 'ua': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36', 'platform': 'Win32', 'vendor': 'Google Inc.', 'languages': ['en-US', 'en']},
]

# Store active PAN drivers per user chat_id
_pan_drivers = {}
_pan_drivers_lock = threading.Lock()

def store_pan_driver(chat_id, driver):
    with _pan_drivers_lock:
        old = _pan_drivers.pop(chat_id, None)
        if old:
            try: old.quit()
            except: pass
        _pan_drivers[chat_id] = driver

def get_stored_pan_driver(chat_id):
    with _pan_drivers_lock:
        return _pan_drivers.pop(chat_id, None)

def cleanup_pan_driver(chat_id):
    with _pan_drivers_lock:
        d = _pan_drivers.pop(chat_id, None)
        if d:
            try: d.quit()
            except: pass

def get_pan_driver():
    profile = random.choice(PAN_USER_AGENTS)
    options = Options()
    # Use system chromium if available (Docker/Linux)
    chrome_bin = os.environ.get('CHROME_BIN', '')
    if chrome_bin and os.path.exists(chrome_bin):
        options.binary_location = chrome_bin
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    # Use local forward proxy so Chrome never sees the auth challenge
    # (--proxy-server cannot carry credentials and CDP Fetch auth crashes the session)
    try:
        from proxy_forwarder import start_proxy_forwarder
        _lp_host, _lp_port = start_proxy_forwarder(PAN_PROXY_HOST, int(PAN_PROXY_PORT), PAN_PROXY_USER, PAN_PROXY_PASS)
        options.add_argument(f"--proxy-server={_lp_host}:{_lp_port}")
    except Exception as e:
        logger.warning(f"Local forward proxy failed ({e}), using direct proxy without auth")
        options.add_argument(f"--proxy-server={PAN_PROXY_HOST}:{PAN_PROXY_PORT}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument(f"--user-agent={profile['ua']}")
    options.add_argument(f"--lang={profile['languages'][0]}")
    options.add_argument("--log-level=3")
    options.add_argument("--silent")
    options.add_argument("--disable-logging")
    # Use system chromedriver if available
    chromedriver_path = os.environ.get('CHROMEDRIVER_PATH', '')
    if chromedriver_path and os.path.exists(chromedriver_path):
        service = Service(executable_path=chromedriver_path, log_output=os.devnull)
    else:
        service = Service(log_output=os.devnull)
    driver = webdriver.Chrome(options=options, service=service)
    # Set page load timeout to prevent hangs (short: slow-but-working pages
    # rarely fire the load event anyway; we verify by DOM content instead)
    driver.set_page_load_timeout(20)
    js_interceptor = """
    (function() {
        try {
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.chrome = window.chrome || { runtime: {} };
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        } catch(e) {}
        window.__CAPTURED_APIS__ = window.__CAPTURED_APIS__ || {};
        var origFetch = window.fetch;
        if (origFetch) {
            window.fetch = async function() {
                var args = arguments;
                var res = await origFetch.apply(this, args);
                try {
                    var u = typeof args[0] === 'string' ? args[0] : (args[0] && args[0].url ? args[0].url : '');
                    if (u && (u.includes('creditReport') || u.includes('customer') || u.includes('bureau') || u.includes('overview'))) {
                        var clone = res.clone();
                        var json = await clone.json();
                        window.__CAPTURED_APIS__[u] = json;
                    }
                } catch(e){}
                return res;
            };
        }
    })();
    """
    try:
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": js_interceptor})
    except Exception:
        pass
    return driver

def find_customer_profile(obj):
    if isinstance(obj, str):
        try:
            parsed = json.loads(obj)
            return find_customer_profile(parsed)
        except Exception:
            return None
    if isinstance(obj, dict):
        if "customerProfile" in obj and isinstance(obj["customerProfile"], dict):
            return obj["customerProfile"]
        if "mobileNumber" in obj and "panCard" in obj:
            return obj
        for k, v in obj.items():
            res = find_customer_profile(v)
            if res: return res
    elif isinstance(obj, list):
        for item in obj:
            res = find_customer_profile(item)
            if res: return res
    return None

def initiate_paisabazaar_login(driver, mobile):
    url = "https://creditreport.paisabazaar.com/credit-report/apply"
    driver.get(url)
    mobile_field = None
    start_wait = time.time()
    while time.time() - start_wait < 15:
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for idx, iframe in enumerate(iframes):
            try:
                driver.switch_to.frame(iframe)
                mobile_field = driver.find_element(By.XPATH, "//input[contains(@placeholder,'Mobile') or @type='tel' or @name='mobile' or @name='phone']")
                break
            except NoSuchElementException:
                driver.switch_to.default_content()
        if mobile_field:
            break
        try:
            mobile_field = driver.find_element(By.XPATH, "//input[contains(@placeholder,'Mobile') or @type='tel' or @name='mobile' or @name='phone']")
            break
        except NoSuchElementException:
            pass
        time.sleep(1)
    if not mobile_field:
        return False, "Mobile input field not found on portal."
    try:
        mobile_field.click()
        mobile_field.send_keys(Keys.CONTROL + "a")
        mobile_field.send_keys(Keys.BACKSPACE)
        mobile_field.send_keys(mobile)
        driver.execute_script("""
            var el = arguments[0];
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
            el.blur();
        """, mobile_field)
    except Exception as e:
        return False, f"Mobile input error: {e}"
    try: mobile_field.send_keys(Keys.ENTER)
    except Exception: pass
    try:
        btn = driver.find_element(By.XPATH, "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'get otp') or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'continue')]")
        driver.execute_script("arguments[0].click();", btn)
    except Exception: pass
    # Switch back to main page context so OTP fields can be found later
    try:
        driver.switch_to.default_content()
    except Exception:
        pass
    return True, "OTP Sent"

def submit_paisabazaar_otp_and_extract(driver, otp):
    try:
        otp_boxes = driver.find_elements(By.CSS_SELECTOR, "input[maxlength='1'], input.otp")
        if len(otp_boxes) >= len(otp):
            for i, ch in enumerate(otp):
                otp_boxes[i].click()
                otp_boxes[i].send_keys(ch)
        else:
            otp_field = driver.find_element(By.XPATH, "//input[@type='tel' or @name='otp' or @id='otp' or contains(@placeholder,'OTP') or contains(@placeholder,'otp')]")
            otp_field.clear()
            otp_field.send_keys(otp)
            otp_field.send_keys(Keys.ENTER)
        try:
            verify = driver.find_element(By.XPATH, "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'verify') or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'submit') or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'login')]")
            driver.execute_script("arguments[0].click();", verify)
        except Exception:
            pass
    except Exception as e:
        return False, f"OTP submission failed: {e}"
    time.sleep(2)
    try:
        driver.switch_to.default_content()
    except Exception:
        pass
    driver.get("https://creditreport.paisabazaar.com/bureau/report-analysis")
    profile = None
    start_time = time.time()
    while time.time() - start_time < 10:
        try:
            captured = driver.execute_script("var res = window.__CAPTURED_APIS__ || {}; res.__INITIAL_STATE__ = window.__INITIAL_STATE__ || null; return res;")
            if captured:
                found = find_customer_profile(captured)
                if found:
                    profile = found
                    break
        except Exception:
            pass
        try:
            local_data = driver.execute_script("""
                var result = {};
                for (var i = 0; i < localStorage.length; i++) {
                    var k = localStorage.key(i);
                    try { result[k] = JSON.parse(localStorage.getItem(k)); }
                    catch(e) { result[k] = localStorage.getItem(k); }
                }
                return result;
            """)
            found = find_customer_profile(local_data)
            if found:
                profile = found
                break
        except Exception:
            pass
        time.sleep(1)
    if not profile:
        try:
            cookies = {c['name']: c['value'] for c in driver.get_cookies()}
            cookie_header = "; ".join([f"{k}={v}" for k, v in cookies.items()])
            pb_access_token = cookies.get("pb-access-token", "") or driver.execute_script("return localStorage.getItem('pb-access-token') || localStorage.getItem('ssoToken') || '';")
            pb_pass_token = cookies.get("pb-pass-token", "") or cookies.get("PB_GLSS_TOKEN", "") or driver.execute_script("return localStorage.getItem('pb-pass-token') || '';")
            visit_id = cookies.get("visitId", "") or driver.execute_script("return localStorage.getItem('visitId') || '';")
            req_headers = {
                "Accept": "application/json, text/plain, */*", "Content-Type": "application/json",
                "User-Agent": driver.execute_script("return navigator.userAgent;"),
                "Origin": "https://creditreport.paisabazaar.com", "Referer": "https://creditreport.paisabazaar.com/",
                "non-app": "true", "site-origin": "BUREAU_WEB_MOBILE", "Cookie": cookie_header
            }
            if pb_access_token: req_headers["pb-access-token"] = pb_access_token
            if pb_pass_token: req_headers["pb-pass-token"] = pb_pass_token
            if visit_id: req_headers["visitid"] = visit_id
            target_url = "https://api2.paisabazaar.com/BSP/api/v1/customer/creditReport/overview"
            req = urllib.request.Request(target_url, headers=req_headers, method="GET")
            with urllib.request.urlopen(req, timeout=10) as response:
                resp_bytes = response.read()
                try:
                    resp_text = gzip.decompress(resp_bytes).decode("utf-8")
                except Exception:
                    resp_text = resp_bytes.decode("utf-8")
                parsed = json.loads(resp_text)
                found = find_customer_profile(parsed)
                if found:
                    profile = found
        except Exception:
            pass
    if profile:
        ordered_result = {
            "firstName": profile.get("firstName", ""), "lastName": profile.get("lastName", ""),
            "dob": profile.get("dob", ""), "emailId": profile.get("emailId", ""),
            "mobileNumber": profile.get("mobileNumber", ""), "panCard": profile.get("panCard", ""),
            "addressLine1": profile.get("addressLine1", "")
        }
        return True, ordered_result
    return False, "Customer profile data not found."

# ============== LOGGING SETUP ==============
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Telegram Bot Setup
TELEGRAM_BOT_TOKEN = "8795691302:AAFykIvRzKGAQ_rUKCtB3fiWVcrjQjAh_9s"



# ============== SESSION FACTORY ==============
def create_session(use_proxy=False, proxy_string=None):
    session = requests.Session()
    # Use max_retries=1 for UIDAI to avoid blocking threads for 45 s (3×15 s).
    # Retry logic is handled at the application level instead.
    session.mount('https://', requests.adapters.HTTPAdapter(
        pool_connections=5, pool_maxsize=5, max_retries=1, pool_block=False
    ))
    if use_proxy and proxy_string:
        # For SOCKS5 proxies, pass the full URL directly (auth in URL)
        if proxy_string.startswith('socks'):
            session.proxies = {'http': proxy_string, 'https': proxy_string}
            logger.info(f"SOCKS5 proxy set: {proxy_string.split('@')[1] if '@' in proxy_string else proxy_string}")
        else:
            parsed = urlparse(proxy_string)
            proxy_url = f"{parsed.scheme}://{parsed.netloc}"
            session.proxies = {'http': proxy_url, 'https': proxy_url}
            if parsed.username and parsed.password:
                import base64
                cred = f"{parsed.username}:{parsed.password}"
                encoded = base64.b64encode(cred.encode()).decode()
                session.headers['Proxy-Authorization'] = f'Basic {encoded}'
            logger.info(f"HTTP proxy set: {proxy_url}")
    else:
        logger.info("No proxy set in this session (direct connection)")
    return session


thread_local = threading.local()

def reset_uidai_session():
    """Force all threads to create a fresh UIDAI session on next access."""
    thread_local.uidai_session = None

def get_telegram_session():
    if not hasattr(thread_local, 'telegram_session') or thread_local.telegram_session is None:
        # Telegram does not require a proxy in India; direct connection is much faster (under 100ms)
        thread_local.telegram_session = create_session(False)
    return thread_local.telegram_session

def get_uidai_session():
    """Return a fresh UIDAI session with random proxy from pool + random fingerprint."""
    if PROXY_POOL:
        proxy = random.choice(PROXY_POOL)
        sess = create_session(True, proxy)
    elif PROXY_CONFIG['use_proxy'] and PROXY_CONFIG['https']:
        sess = create_session(True, PROXY_CONFIG['https'])
    else:
        sess = create_session(False)
    return sess

_SENTINEL = object()  # unique sentinel for "not yet set"

# ============== PDF PASSWORD CRACKER ==============
class PDFPasswordCracker:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=16)
        self.found_password = None
        self.stop_flag = False
        self.progress = 0
        self.total_years = 0

    def try_password(self, pdf_bytes, password):
        try:
            # Reusing in-memory bytes is extremely fast compared to disk read
            pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_bytes))
            if pdf_reader.decrypt(password):
                return True, password
            return False, None
        except Exception as e:
            return False, None

    def decrypt_pdf(self, pdf_path, password, output_path=None):
        try:
            if output_path is None:
                output_path = pdf_path.replace('.pdf', '_decrypted.pdf')
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                pdf_reader.decrypt(password)
                pdf_writer = PyPDF2.PdfWriter()
                for page in pdf_reader.pages:
                    pdf_writer.add_page(page)
                with open(output_path, 'wb') as output_file:
                    pdf_writer.write(output_file)
            logger.info(f"Decrypted PDF saved: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error decrypting PDF: {e}")
            return None

    def crack_pdf(self, pdf_path, name, progress_callback=None):
        self.found_password = None
        self.stop_flag = False
        self.progress = 0
        
        # Read the file bytes once to avoid disk I/O on every attempt
        try:
            with open(pdf_path, 'rb') as f:
                pdf_bytes = f.read()
        except Exception as e:
            logger.error(f"Failed to read PDF for cracking: {e}")
            return False, None, None

        name_upper = name.upper().strip()
        # Split into individual words for better cracking
        words = [w for w in name_upper.split() if len(w) >= 2]
        name_prefix = name_upper[:4] if len(name_upper) >= 4 else name_upper
        
        # Build prefixes from: full name first 4, each word first 4, each word first 3
        prefixes = set()
        prefixes.add(name_prefix)  # ABUL from "ABU LUISH MOLLAH"
        for w in words:
            prefixes.add(w[:4])  # ABU_, LUIS, MOLL
            prefixes.add(w[:3])  # ABU, LUI, MOL
            if len(w) >= 5:
                prefixes.add(w[:5])
        # Also no-space version
        no_space = name_upper.replace(' ', '')
        prefixes.add(no_space[:4])
        prefixes.add(no_space[:6] if len(no_space) >= 6 else no_space)
        
        current_year = datetime.now().year
        y_80_10 = list(range(1980, 2011))
        y_70_79 = list(range(1970, 1980))
        y_11_now = list(range(2011, current_year + 1))
        y_others = list(range(1940, 1970)) + list(range(1930, 1940))
        common_years = y_80_10 + y_70_79 + y_11_now + y_others
        
        # 1. High Priority: each prefix (UPPER) + year
        highly_likely = []
        for pfx in prefixes:
            for year in common_years:
                highly_likely.append(f"{pfx.upper()}{year}")
            
        # 2. Medium: lowercase/title + year
        secondary = []
        for pfx in prefixes:
            for year in common_years:
                secondary.append(f"{pfx.lower()}{year}")
                secondary.append(f"{pfx.title()}{year}")

        # 3. Low: special separators
        rare = []
        for pfx in list(prefixes)[:3]:
            for year in common_years:
                rare.append(f"{pfx.upper()}@{year}")
                rare.append(f"{pfx.upper()}#{year}")
                rare.append(f"{year}{pfx.upper()}")
        
        # Combine and deduplicate
        prioritized_passwords = []
        seen = set()
        for pwd in (highly_likely + secondary + rare):
            if pwd not in seen:
                seen.add(pwd)
                prioritized_passwords.append(pwd)
                
        # Fallback: just prefixes without years
        for pfx in prefixes:
            for p in [pfx.upper(), pfx.lower(), pfx.title()]:
                if p not in seen:
                    seen.add(p)
                    prioritized_passwords.append(p)

        # Run checks in batches of 32 using as_completed for immediate returns
        batch_size = 32
        for i in range(0, len(prioritized_passwords), batch_size):
            if self.stop_flag:
                break
            batch = prioritized_passwords[i:i+batch_size]
            futures = {self.executor.submit(self.try_password, pdf_bytes, p): p for p in batch}
            for future in as_completed(futures):
                if self.stop_flag:
                    break
                try:
                    success, found_pwd = future.result()
                    if success:
                        self.found_password = found_pwd
                        self.stop_flag = True
                        decrypted_path = self.decrypt_pdf(pdf_path, found_pwd)
                        return True, found_pwd, decrypted_path if decrypted_path else None
                except Exception:
                    continue
                    
        return False, None, None


# ============== RANDOM FINGERPRINT POOL ==============
UA_POOL = [
    ('Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36', '"Google Chrome";v="131"', '"Android"'),
    ('Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36', '"Google Chrome";v="130"', '"Android"'),
    ('Mozilla/5.0 (Linux; Android 14; SM-A546B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Mobile Safari/537.36', '"Google Chrome";v="129"', '"Android"'),
    ('Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Mobile/15E148 Safari/604.1', '"Safari";v="18"', '"iOS"'),
    ('Mozilla/5.0 (Linux; Android 13; RMX3630) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36', '"Google Chrome";v="128"', '"Android"'),
    ('Mozilla/5.0 (Linux; Android 14; V2254) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Mobile Safari/537.36', '"Google Chrome";v="127"', '"Android"'),
    ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36', '"Google Chrome";v="131"', '"Windows"'),
    ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36', '"Google Chrome";v="130"', '"macOS"'),
    ('Mozilla/5.0 (Linux; Android 12; M2101K6G) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36', '"Google Chrome";v="126"', '"Android"'),
    ('Mozilla/5.0 (Linux; Android 14; CPH2591) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36', '"Google Chrome";v="131"', '"Android"'),
]

SCREEN_POOL = ['360x800', '393x873', '412x915', '414x896', '390x844', '375x812', '360x780', '428x926', '384x854', '1920x1080', '1366x768', '1536x864']

def get_random_fingerprint():
    ua, ch_ua, platform = random.choice(UA_POOL)
    screen = random.choice(SCREEN_POOL)
    w, h = screen.split('x')
    is_mobile = '?1' if 'Mobile' in ua or 'Android' in ua or 'iPhone' in ua else '?0'
    return {
        'User-Agent': ua,
        'sec-ch-ua': f'{ch_ua}, "Chromium";v="{ch_ua.split("v=")[1] if "v=" in ch_ua else "131"}, "Not)A;Brand";v="24"',
        'sec-ch-ua-mobile': is_mobile,
        'sec-ch-ua-platform': f'{platform}',
        'viewport-width': w,
        'device-memory': str(random.choice([2, 4, 8])),
        'dnt': str(random.choice([0, 1])),
    }

# ============== AADHAAR BOT CLASS ==========================
class AadhaarBot:
    def __init__(self):
        self.base_headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en_IN',
            'Content-Type': 'application/json',
            'Origin': 'https://myaadhaar.uidai.gov.in',
            'Referer': 'https://myaadhaar.uidai.gov.in/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Mobile Safari/537.36',
            'appid': 'MYAADHAAR',
            'sec-ch-ua': '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'dnt': '1',
        }
        # Randomize fingerprint on each init
        fp = get_random_fingerprint()
        self.base_headers.update(fp)
        logger.info("AadhaarBot initialized")
        self.cracker = PDFPasswordCracker()

    @property
    def session(self):
        sess = get_uidai_session()
        sess.headers.update(self.base_headers)
        return sess

    def generate_transaction_id(self):
        return str(uuid.uuid4())

    def is_base64(self, s):
        if not isinstance(s, str) or len(s) < 100:
            return False
        if s.startswith('data:'):
            s = s.split(',')[1] if ',' in s else s
        if len(s) % 4 != 0:
            return False
        try:
            base64.b64decode(s)
            return True
        except:
            return False

    def detect_file_type(self, file_bytes):
        if file_bytes[:4] == b'%PDF':
            return 'pdf'
        elif file_bytes[:8] == b'\x89PNG\r\n\x1a\n':
            return 'png'
        elif file_bytes[:2] == b'\xff\xd8':
            return 'jpg'
        return 'unknown'

    def detect_and_decode_base64(self, data, field_name="unknown", save=False):
        decoded_items = []
        if isinstance(data, dict):
            for key, value in list(data.items()):
                if isinstance(value, str) and len(value) > 100 and self.is_base64(value):
                    try:
                        clean_base64 = value.split(',')[1] if value.startswith('data:') and ',' in value else value
                        decoded_bytes = base64.b64decode(clean_base64)
                        file_type = self.detect_file_type(decoded_bytes)
                        if save and file_type in ['pdf', 'png', 'jpg']:
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            ext = {'pdf': 'pdf', 'png': 'png', 'jpg': 'jpg'}.get(file_type, 'bin')
                            filename = os.path.abspath(f"decoded_{field_name}_{key}_{timestamp}.{ext}")
                            with open(filename, 'wb') as f:
                                f.write(decoded_bytes)
                            decoded_items.append({'field': key, 'filename': filename, 'type': file_type, 'size': len(decoded_bytes), 'data': decoded_bytes})
                            logger.info(f"Saved: {filename}")
                        elif not save:
                            decoded_items.append({'field': key, 'type': file_type, 'size': len(decoded_bytes), 'data': decoded_bytes})
                    except Exception as e:
                        logger.error(f"Base64 decode error: {e}")
                if isinstance(value, (dict, list)):
                    decoded_items.extend(self.detect_and_decode_base64(value, f"{field_name}.{key}", save))
        elif isinstance(data, list):
            for idx, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    decoded_items.extend(self.detect_and_decode_base64(item, f"{field_name}[{idx}]", save))
        return decoded_items

    def get_captcha(self, user_id, _retries=3, _delay=0.3):
        """Fetch a CAPTCHA image with up to *_retries* attempts."""
        captcha_data = {'captchaLength': '6', 'captchaType': '2', 'audioCaptchaRequired': True}
        for attempt in range(1, _retries + 1):
            transaction_id = self.generate_transaction_id()
            # Always reset session before each attempt — UIDAI drops TCP connection
            # after the startup reachability check, making the cached session stale.
            reset_uidai_session()
            if attempt > 1:
                time.sleep(_delay)
            try:
                sess = self.session
                sess.headers.update({'x-request-id': transaction_id, 'transactionId': transaction_id})
                response = sess.post(
                    'https://tathya.uidai.gov.in/audioCaptchaService/api/captcha/v3/generation',
                    json=captcha_data, timeout=45
                )
                if response.status_code != 200:
                    logger.warning(f"Captcha HTTP {response.status_code} (attempt {attempt})")
                    continue
                resp_json = response.json()
                captcha_txn_id = resp_json.get('transactionId')
                captcha_base64 = resp_json.get('imageBase64')
                if not captcha_base64:
                    for key, value in resp_json.items():
                        if isinstance(value, str) and len(value) > 100 and self.is_base64(value):
                            captcha_base64 = value
                            break
                if not captcha_base64:
                    logger.warning(f"No captcha image in response (attempt {attempt})")
                    continue
                if captcha_base64.startswith('data:image'):
                    captcha_base64 = captcha_base64.split(',')[1]
                image_bytes = base64.b64decode(captcha_base64)
                return image_bytes, captcha_txn_id, transaction_id
            except Exception as e:
                logger.error(f"Error getting captcha (attempt {attempt}/{_retries}): {str(e)}")
        return None, None, None

    def _solve_captcha_beta(self, image_bytes: bytes):
        """Fast captcha solver with PIL preprocessing + cached ddddocr beta."""
        try:
            import io
            from PIL import Image, ImageFilter, ImageEnhance, ImageOps
        except ImportError:
            return ocr_solver.classification(image_bytes)
        
        for attempt in range(2):
            try:
                img = Image.open(io.BytesIO(image_bytes))
                if img.mode != 'L':
                    img = img.convert('L')
                
                w, h = img.size
                img = img.resize((w * 2, h * 2), Image.LANCZOS)
                img = img.filter(ImageFilter.MedianFilter(size=3))
                img = ImageEnhance.Contrast(img).enhance(2.0)
                img = ImageEnhance.Sharpness(img).enhance(2.0)
                img = img.point(lambda p: 255 if p > 140 else 0)
                img = ImageOps.autocontrast(img, cutoff=5)
                
                buf = io.BytesIO()
                img.save(buf, format='PNG', optimize=True)
                processed = buf.getvalue()
                
                # Use globally cached beta model — no reload delay
                result = ocr_solver_beta.classification(processed)
                
                if result and len(result) >= 4:
                    result = ''.join(c for c in result if c.isalnum())
                    if len(result) >= 4:
                        return result[:6]
            
            except Exception as e:
                pass
        
        return ocr_solver.classification(image_bytes)

    def send_aadhaar_otp(self, user_id, eid_number, captcha_value, captcha_txn_id, transaction_id):
        # Fresh session — UIDAI drops connection after captcha, reuse causes RemoteDisconnected
        reset_uidai_session()
        sess = self.session
        sess.headers.update({'x-request-id': transaction_id, 'transactionId': transaction_id})
        otp_request_data = {
            'eidNumber': eid_number, 'idType': 'eid',
            'captchaTxnId': captcha_txn_id, 'captchaValue': captcha_value,
            'transactionId': transaction_id, 'resendOTP': False
        }
        try:
            response = sess.post(
                'https://tathya.uidai.gov.in/unifiedAppAuthService/api/v2/generate/aadhaar/otp',
                json=otp_request_data, timeout=45
            )
            if response.status_code == 200:
                resp_json = response.json()
                otp_txn_id = resp_json.get('txnId')
                status = resp_json.get('status')
                message = resp_json.get('message')
                if otp_txn_id and status == "Success":
                    return True, otp_txn_id, message
                else:
                    return False, None, message
            else:
                return False, None, f"HTTP {response.status_code}"
        except Exception as e:
            return False, None, str(e)

    def download_aadhaar_pdf(self, user_id, eid_number, otp, otp_txn_id, transaction_id, mask=False):
        # Fresh session for every download call
        reset_uidai_session()
        sess = self.session
        sess.headers.update({'x-request-id': transaction_id, 'transactionId': transaction_id})
        download_data = {'eid': eid_number, 'mask': mask, 'otp': otp, 'otpTxnId': otp_txn_id}
        try:
            response = sess.post(
                'https://tathya.uidai.gov.in/downloadAadhaarService/api/aadhaar/download',
                json=download_data, timeout=90
            )
            if response.status_code == 200:
                resp_json = response.json()
                logger.info(f"PDF download response keys: {list(resp_json.keys())} status={resp_json.get('status')} errorCode={resp_json.get('errorCode')} msg={resp_json.get('message', resp_json.get('errorMessage', 'N/A'))[:100]}")
                decoded_files = self.detect_and_decode_base64(resp_json, "aadhaar_download", save=True)
                if decoded_files:
                    return True, decoded_files[0]['filename']
                else:
                    if resp_json.get('status') == 'Error' or resp_json.get('errorCode'):
                        error_msg = resp_json.get('message', resp_json.get('errorMessage', 'Unknown error'))
                        return False, error_msg
                    else:
                        return False, "No PDF data found"
            else:
                logger.warning(f"PDF download HTTP {response.status_code}: {response.text[:200]}")
                return False, f"UIDAI Server Error (HTTP {response.status_code})"
        except Exception as e:
            logger.error(f"Download PDF exception: {e}")
            err_str = str(e)
            if "timed out" in err_str.lower() or "timeout" in err_str.lower():
                return False, "UIDAI Server Timeout. Please retry."
            return False, "UIDAI Connection Error. Please retry."

    def send_eid_otp(self, user_id, mobile, name, captcha_code, captcha_txn_id, transaction_id):
        # Fresh session — avoids RemoteDisconnected after captcha call drops TCP
        reset_uidai_session()
        sess = self.session
        sess.headers.update({'x-request-id': transaction_id, 'transactionId': transaction_id})
        request_data = {
            'mobileNumber': mobile, 'dob': None, 'email': None,
            'name': name.upper(), 'option': 'EID', 'otp': None,
            'otpTxnId': None, 'captchaTxnId': captcha_txn_id,
            'captcha': captcha_code, 'resendOtp': False
        }
        try:
            response = sess.post(
                'https://tathya.uidai.gov.in/retrieveEidUid/ext/v1/generic/retrieveuideid',
                json=request_data, timeout=30
            )
            if response.status_code == 200:
                resp_json = response.json()
                if 'responseData' in resp_json:
                    response_data = resp_json['responseData']
                    otp_txn_id = response_data.get('otpTxnId')
                    status = response_data.get('status')
                    if otp_txn_id and status == "Success":
                        return True, otp_txn_id
                    else:
                        return False, response_data.get('message', 'Unknown error')
                else:
                    return False, 'Invalid response'
            else:
                return False, f'HTTP {response.status_code}'
        except Exception as e:
            err_str = str(e)
            if "timed out" in err_str.lower() or "timeout" in err_str.lower():
                return False, "UIDAI server timeout — please try again"
            if "connection" in err_str.lower() or "refused" in err_str.lower():
                return False, "UIDAI connection failed — proxy may be down"
            return False, err_str

    def verify_eid_otp(self, user_id, mobile, name, otp_code, otp_txn_id, captcha_txn_id, captcha_code):
        # Fresh session for OTP verify
        reset_uidai_session()
        sess = self.session
        sess.headers.update({'x-request-id': self.generate_transaction_id()})
        verify_data = {
            'mobileNumber': mobile, 'dob': None, 'name': name.upper(),
            'email': None, 'option': 'EID', 'otp': otp_code,
            'otpTxnId': otp_txn_id, 'captchaTxnId': captcha_txn_id,
            'captcha': captcha_code, 'resendOtp': False
        }
        try:
            response = sess.post(
                'https://tathya.uidai.gov.in/retrieveEidUid/ext/v1/generic/retrieveuideid',
                json=verify_data, timeout=60
            )
            if response.status_code == 200:
                resp_json = response.json()
                if resp_json.get('status') == 200 or resp_json.get('status') == "Success":
                    if 'responseData' in resp_json:
                        response_data = resp_json['responseData']
                        eid_number = response_data.get('eidNumber')
                        name_from_response = response_data.get('name', name)
                        if eid_number:
                            return True, eid_number, name_from_response
                        else:
                            return False, None, "No EID found"
                    else:
                        return False, None, "Invalid response"
                else:
                    logger.warning(f"Verify EID response: {resp_json}")
                    error_details = resp_json.get('errorDetails')
                    if isinstance(error_details, dict):
                        error_msg = error_details.get('messageEnglish', 'Verification failed')
                    else:
                        error_msg = resp_json.get('message', 'Verification failed')
                    return False, None, error_msg
            else:
                return False, None, f'HTTP {response.status_code}'
        except Exception as e:
            return False, None, str(e)

    def crack_pdf_with_name(self, pdf_path, name, progress_callback=None):
        success, password, decrypted_path = self.cracker.crack_pdf(pdf_path, name, progress_callback)
        tips = None
        return success, password, decrypted_path, tips

# ============================================================
# Initialize bot
# ============================================================
bot = AadhaarBot()

# ============== CONFIG ==============
DIVIDER         = "━━━━━━━━━━━━━━━"
BOT_NAME        = "MK & GJ AadharBot"
OWNER_IDS       = {2095029151}  # Admin User IDs
OWNER_USERNAME  = "@kiran"     # Admin Username
SESSION_TIMEOUT = 180
MAINTENANCE_MODE = False  # Default, overwritten by DB below
LOG_CHANNEL_ID  = -1003968368088    # gj channel
LIMITED_PLANS = {
    'l1':   {'name': '1 Search',     'price': '$1'},
    'l5':   {'name': '5 Searches',   'price': '$5'},
    'l10':  {'name': '10 Searches',  'price': '$9'},
    'l30':  {'name': '30 Searches',  'price': '$22'},
    'l50':  {'name': '50 Searches',  'price': '$29'},
    'l100': {'name': '100 Searches', 'price': '$49'},
    'l200': {'name': '200 Searches', 'price': '$89'},
    'l500': {'name': '500 Searches', 'price': '$149'},
}

PAGE_SIZE = 10
PDF_PAGE_SIZE = 5  # PDFs per page in /pdflist

UNLIMITED_PLANS = {
    'u1d':   {'name': '1 Day Unlimited',    'price': '$2'},
    'u7d':   {'name': '7 Days Unlimited',   'price': '$10'},
    'u1m':   {'name': '1 Month Unlimited',  'price': '$35'},
    'u12m':  {'name': '12 Month Unlimited', 'price': '$99'},
    'ulife': {'name': 'Lifetime Unlimited', 'price': '$149'},
}
# Channel for PDF delivery storage (private channel)
PDF_CHANNEL_LINK = "https://t.me/+3wpSfsNnaKowNDg1"
PDF_CHANNEL_ID = -1003968368088  # gj channel
CHANNEL_USERNAME = "@alphatonsol"
CHANNEL_LINK     = "https://t.me/alphatonsol"
CHANNEL2_USERNAME = "@gujjucryptto"
CHANNEL2_LINK     = "https://t.me/gujjucryptto"

# PAN Bot link
PAN_BOT_USERNAME = "ARCTXNBOT"
PAN_BOT_LINK = f"https://t.me/{PAN_BOT_USERNAME}"

# Aadhaar Bot 2 cross-link
AADHAAR_BOT2_LINK = "https://t.me/ARCTXNBOT"

# ============== MONGO DB SETUP ==============
MONGO_URI = "mongodb+srv://thakues:thakurains@thakur2.y9dlsd5.mongodb.net/?appName=Cluster0"

# Connect to MongoDB with retry logic for cloud deployments (Railway, Render, etc.)
# MongoDB Atlas may reject initial connections from new IPs.
_mongo_retries = 5
_mongo_delay = 5  # seconds between retries
mongo_client = None
for _attempt in range(1, _mongo_retries + 1):
    try:
        logger.info(f"MongoDB connection attempt {_attempt}/{_mongo_retries}...")
        mongo_client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=15000,
            connectTimeoutMS=15000,
        )
        mongo_client.admin.command('ping')
        logger.info("MongoDB connected successfully!")
        break
    except Exception as e:
        logger.error(f"MongoDB connection attempt {_attempt}/{_mongo_retries} failed: {e}")
        if _attempt < _mongo_retries:
            logger.info(f"Retrying in {_mongo_delay} seconds...")
            time.sleep(_mongo_delay)
        else:
            logger.critical("MongoDB connection failed after all retries. Bot will start but DB features may not work.")

db = mongo_client["aadhar_bot"]
users_col = db["users"]
keys_collection = db["redeem_keys"]
pdf_logs_col = db["pdf_logs"]
settings_col = db["settings"]


# ============== MONGODB HELPER WITH RETRY ==============
def mongo_operation(func, *args, retries=2, delay=0.5, **kwargs):
    """Execute a MongoDB operation with retry logic for transient failures."""
    last_error = None
    for attempt in range(retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_error = e
            err_str = str(e).lower()
            # Only retry on transient errors (network, timeout, connection)
            if any(x in err_str for x in ['connection', 'timeout', 'network', 'not master', 'shutdown']):
                if attempt < retries:
                    logger.warning(f"MongoDB transient error (attempt {attempt + 1}/{retries + 1}): {e}")
                    time.sleep(delay * (attempt + 1))
                    continue
            # Non-transient error or max retries reached
            logger.error(f"MongoDB operation failed: {e}")
            raise
    raise last_error

def safe_mongo_find(collection, query, default=None):
    """Safely execute a MongoDB find_one with error handling."""
    try:
        return mongo_operation(collection.find_one, query)
    except Exception as e:
        logger.error(f"MongoDB find_one failed: {e}")
        return default

def safe_mongo_insert(collection, document):
    """Safely execute a MongoDB insert_one with error handling."""
    try:
        return mongo_operation(collection.insert_one, document)
    except Exception as e:
        logger.error(f"MongoDB insert_one failed: {e}")
        return None

def safe_mongo_update(collection, query, update, upsert=False):
    """Safely execute a MongoDB update_one with error handling."""
    try:
        return mongo_operation(collection.update_one, query, update, upsert=upsert)
    except Exception as e:
        logger.error(f"MongoDB update_one failed: {e}")
        return None

def safe_mongo_count(collection, query=None):
    """Safely execute a MongoDB count_documents with error handling."""
    try:
        return mongo_operation(collection.count_documents, query or {})
    except Exception as e:
        logger.error(f"MongoDB count_documents failed: {e}")
        return 0

def safe_mongo_find_all(collection, query=None, sort=None, limit=None):
    """Safely execute a MongoDB find with error handling."""
    try:
        cursor = collection.find(query or {})
        if sort:
            cursor = cursor.sort(sort)
        if limit:
            cursor = cursor.limit(limit)
        return list(cursor)
    except Exception as e:
        logger.error(f"MongoDB find failed: {e}")
        return []


# Load Maintenance Mode from DB
try:
    setting = settings_col.find_one({"_id": "config"})
    if not setting:
        settings_col.insert_one({"_id": "config", "maintenance_mode": False})
        MAINTENANCE_MODE = False
    else:
        MAINTENANCE_MODE = setting.get("maintenance_mode", False)
except Exception as e:
    logger.error(f"Error loading maintenance mode from DB: {e}")
    MAINTENANCE_MODE = False

# Load PDF Channel ID from DB (overrides env var)
try:
    pdf_setting = settings_col.find_one({"_id": "config"})
    if pdf_setting and pdf_setting.get("pdf_channel_id"):
        PDF_CHANNEL_ID = pdf_setting["pdf_channel_id"]
except Exception as e:
    logger.error(f"Error loading PDF channel ID from DB: {e}")

def get_user_log_tag(user_id):
    """Returns formatted user tag for console logs e.g. '[8735232340 @Mouktik_5911]'"""
    try:
        uid = str(user_id)
        u = get_user_cached(user_id)
        if u:
            username = u.get('username')
            first_name = u.get('first_name')
            if username:
                return f"[{uid} @{username}]"
            elif first_name and first_name != "Unknown":
                return f"[{uid} {first_name}]"
    except Exception:
        pass
    return f"[{user_id}]"

def ensure_user(user_id, referrer_id=None, first_name=None, username=None):
    uid = str(user_id)
    user = safe_mongo_find(users_col, {"_id": uid})
    if user is None:
        new_user = {
            "_id": uid,
            "first_name": first_name or "Unknown",
            "username": username,
            "credits": 0,
            "lifetime": False,
            "expiry": (datetime.now() + timedelta(hours=1)).isoformat(),
            "referred_by": str(referrer_id) if referrer_id else None,
            "referral_count": 0,
            "searches": 0,
            "pan_searches": 0,
            "joined": datetime.now().isoformat()
        }
        safe_mongo_insert(users_col, new_user)
        if referrer_id:
            rid = str(referrer_id)
            if rid != uid:
                # Give referrer +1 hour
                ref_user = safe_mongo_find(users_col, {"_id": rid})
                if ref_user:
                    current_exp = ref_user.get('expiry', '')
                    try:
                        exp_dt = datetime.fromisoformat(current_exp)
                        if exp_dt < datetime.now():
                            exp_dt = datetime.now()
                    except:
                        exp_dt = datetime.now()
                    new_exp = (exp_dt + timedelta(hours=1)).isoformat()
                    safe_mongo_update(users_col,
                        {"_id": rid},
                        {"$set": {"expiry": new_exp}, "$inc": {"referral_count": 1}}
                    )
        # Log new user
        try:
            uname_str = f"@{username}" if username else "N/A"
            msg = (
                f"\U0001f7e2 <b>NEW USER ALERT</b>\n"
                f"\u2014\u2014\u2014\u2014\u2014\u2014\u2014\u2014\u2014\u2014\u2014\u2014\u2014\u2014\n"
                f"\U0001f464 <b>Name:</b> {first_name or 'Unknown'}\n"
                f"\U0001f468\U0001f3fb <b>User:</b> {uname_str}\n"
                f"\U0001f194 <b>ID:</b> <code>{uid}</code>"
            )
            if referrer_id:
                referrer = users_col.find_one({"_id": str(referrer_id)})
                ref_uname = f"@{referrer.get('username')}" if referrer and referrer.get('username') else "Unknown"
                msg += (
                    f"\n🔗 <b>Referred By:</b> {ref_uname} (<code>{referrer_id}</code>)\n"
                    f"\u2014\u2014\u2014\u2014\u2014\u2014\u2014\u2014\u2014\u2014\u2014\u2014\u2014\u2014"
                )
            send_log(msg)
        except Exception:
            pass
        return True
    else:
        # Update name/username if changed
        current_first = user.get('first_name')
        current_user = user.get('username')
        
        upd = {}
        # Update first_name only if it's provided and different
        if first_name and first_name != current_first:
            upd['first_name'] = first_name
            
        # Always update username if it's different, even if it's None (removed)
        if username != current_user:
            upd['username'] = username
            
        if upd:
            safe_mongo_update(users_col, {"_id": uid}, {"$set": upd})
    return False

def get_user(user_id):
    return safe_mongo_find(users_col, {"_id": str(user_id)})

# ============== USER DATA CACHE ==============
_user_cache = {}
_user_cache_lock = threading.Lock()
_CACHE_TTL = 30  # Cache TTL in seconds

def get_user_cached(user_id):
    """Get user with caching to reduce MongoDB queries."""
    uid = str(user_id)
    with _user_cache_lock:
        if uid in _user_cache:
            cached_time, cached_user = _user_cache[uid]
            if time.time() - cached_time < _CACHE_TTL:
                return cached_user
    
    # Cache miss - fetch from DB
    user = safe_mongo_find(users_col, {"_id": uid})
    
    with _user_cache_lock:
        _user_cache[uid] = (time.time(), user)
    
    return user

def invalidate_user_cache(user_id):
    """Invalidate cache for a user after updates."""
    uid = str(user_id)
    with _user_cache_lock:
        _user_cache.pop(uid, None)


def check_expiry(user):
    if user and user.get('expiry'):
        try:

            if datetime.fromisoformat(user['expiry']) > datetime.now():
                return True
        except Exception:
            pass
    return False

def check_and_notify_expiry(chat_id):
    u = get_user_cached(chat_id)
    if not u: return
    
    expiry_str = u.get('expiry')
    if expiry_str and not u.get('lifetime'):
        try:

            expiry_dt = datetime.fromisoformat(expiry_str)
            if expiry_dt <= datetime.now() and not u.get('expiry_notified'):
                safe_mongo_update(users_col, {"_id": str(chat_id)}, {"$set": {"expiry_notified": True}})
                
                balance = int(u.get('credits', 0))
                
                msg_text = (
                    f"🚨 <b>Your Premium Plan Has Expired!</b>\n\n"
                    f"Your unlimited access has come to an end, but don't worry! "
                    f"We've successfully safely restored your previous credits exactly where you left off.\n\n"
                    f"💰 <b>Current Balance:</b> {balance} Searches\n\n"
                    f"⚡ <b>Ready to keep the power going?</b>\n"
                    f"Upgrade again to enjoy uninterrupted, unlimited searches and stay ahead of the game! 🚀\n\n"
                    f"Tap /buy to view our latest premium plans or /profile to check your account."
                )
                send_message(chat_id, msg_text)
                
                name = u.get('first_name', 'Unknown')
                username = u.get('username')
                username_str = f" @{username}" if username else ""
                plan_days = u.get('unlimited_days')
                status_str = f"{plan_days} Days Unlimited ended" if plan_days else "Unlimited ended"
                
                log_text = (
                    f"⏰ <b>UNLIMITED PLAN EXPIRED</b>\n"
                    f"👤 User: <b>{name}</b>{username_str} (<code>{chat_id}</code>)\n"
                    f"💰 Status: {status_str}\n"
                    f"🔄 Restored Credits: {balance}"
                )
                send_log(log_text)
        except Exception as e:
            logger.error(f"Error checking/notifying expiry: {e}")

def get_credits(user_id):
    # Admins always have unlimited access
    if int(user_id) in OWNER_IDS:
        return float('inf')
    u = get_user_cached(user_id)
    if u is None:
        return 0
    if u.get('lifetime') or check_expiry(u):
        return float('inf')
    return u.get('credits', 0)

def is_lifetime(user_id):
    # Admins always have lifetime access
    if int(user_id) in OWNER_IDS:
        return True
    u = get_user_cached(user_id)
    return (u.get('lifetime', False) or check_expiry(u)) if u else False

def has_credits(user_id):
    return get_credits(user_id) > 0

def add_credits(user_id, amount, make_lifetime=False):
    uid = str(user_id)
    invalidate_user_cache(user_id)
    user = get_user(user_id)
    if user is None:
        new_user = {
            "_id": uid,
            "credits": 0,
            "lifetime": False,
            "referred_by": None,
            "referral_count": 0,
            "searches": 0,
            "pan_searches": 0,
            "joined": datetime.now().isoformat()
        }
        users_col.insert_one(new_user)
    
    if make_lifetime:
        safe_mongo_update(users_col, {"_id": uid}, {"$set": {"lifetime": True, "is_premium": True}})
    else:
        safe_mongo_update(users_col, {"_id": uid}, {"$inc": {"credits": amount}, "$set": {"is_premium": True}})

def deduct_credit(user_id):
    uid = str(user_id)
    invalidate_user_cache(user_id)
    user = get_user(user_id)
    if user:
        upd = {"$inc": {"searches": 1}}
        if not user.get('lifetime'):
            new_credits = max(0, user.get('credits', 0) - 1)
            upd["$set"] = {"credits": new_credits}
        safe_mongo_update(users_col, {"_id": uid}, upd)

def all_users():
    docs = users_col.find({})
    return {doc["_id"]: doc for doc in docs}

def show_user_profile_admin(chat_id, target_uid, message_id=None):
    user_doc = users_col.find_one({"_id": str(target_uid)})
    if not user_doc:
        send_message(chat_id, f"❌ User {target_uid} not found.")
        return
        
    uid = user_doc.get('_id')
    username = user_doc.get('username')
    username_display = f"@{username}" if username else "N/A"
    searches = user_doc.get('searches', 0)
    
    cr = get_credits(uid)
    subscription_display = "♾️ Unlimited" if cr == float('inf') else f"{int(cr)} Searches"
    if user_doc.get('banned'):
        subscription_display = "🔴 Banned / Revoked"

    pan_searches = user_doc.get('pan_searches', 0)
    
    text = (
        f"── <b>PROFILE OVERVIEW</b> ──\n\n"
        f"<b>Username:</b> {username_display}\n"
        f"<b>User ID:</b> {uid}\n"
        f"<b>Total Searches:</b> {searches}\n"
        f"<b>PAN Searches:</b> {pan_searches}\n"
        f"<b>Credits:</b> {subscription_display}\n"
        f"<b>Referrals:</b> {user_doc.get('referral_count', 0)}"
    )
    
    kb = {
        'inline_keyboard': [
            [{'text': '✏️  Edit User', 'callback_data': f'edit_user_{uid}'}],
            [{'text': '⬅️  Back to Panel', 'callback_data': 'panel_back'}]
        ]
    }
    
    if message_id:
        edit_message(chat_id, message_id, text, reply_markup=kb)
    else:
        send_message(chat_id, text, reply_markup=kb)

def get_admin_panel_data():
    total_users = safe_mongo_count(users_col) if users_col is not None else 0
    # Use MongoDB aggregation instead of fetching all users into Python
    total_searches = 0
    total_credits = 0
    if users_col is not None:
        try:
            pipeline = [
                {'$group': {
                    '_id': None,
                    'total_searches': {'$sum': '$searches'},
                    'total_credits': {'$sum': {
                        '$cond': [
                            {'$ne': ['$lifetime', True]},
                            {'$ifNull': ['$credits', 0]},
                            0
                        ]
                    }}
                }}
            ]
            result = list(users_col.aggregate(pipeline))
            if result:
                total_searches = result[0].get('total_searches', 0)
                total_credits = result[0].get('total_credits', 0)
        except Exception as e:
            logger.warning(f"Admin aggregation failed, falling back: {e}")
            all_users = safe_mongo_find_all(users_col)
            total_searches = sum(u.get("searches", 0) for u in all_users)
            total_credits = sum(u.get("credits", 0) for u in all_users if not u.get('lifetime'))
    pending_codes = safe_mongo_count(keys_collection, {"used": False}) if keys_collection is not None else 0
    total_codes = safe_mongo_count(keys_collection) if keys_collection is not None else 0
    
    text = (
        "\u2727 <b>Admin Panel</b>\n"
        "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
        f"\u25c6 Users: <b>{total_users}</b> | \u25c6 Lookups: <b>{total_searches}</b>\n"
        f"\u25c6 Revenue: <b>\u20b9{total_credits * 10}</b>\n"
        f"\u25c6 Codes: <b>{pending_codes} unused</b> / {total_codes} total\n\n"
        "Choose an action \u2193"
    )
    
    kb = {
        'inline_keyboard': [
            [
                {'text': '\U0001f465 Total Users', 'callback_data': 'panel_users_0'},
                {'text': '\U0001f4cb Lookup History', 'callback_data': 'panel_logs'}
            ],
            [
                {'text': '\u26a1 Activate Plan', 'callback_data': 'panel_search_user'},
                {'text': '\U0001f4b0 Add Credits', 'callback_data': 'panel_add_access'}
            ],
            [
                {'text': '\U0001f50d Check User', 'callback_data': 'panel_search_user'},
                {'text': '\U0001f511 Create Code', 'callback_data': 'panel_gen_key'}
            ],
            [
                {'text': '\U0001f4c4 View Delivered PDFs', 'callback_data': 'panel_view_pdfs_0'},
                {'text': '\U0001f4cb PAN Searches', 'callback_data': 'panel_view_pan_0'}
            ],
            [
                {'text': '\U0001f4e2 Broadcast', 'callback_data': 'panel_broadcast'}
            ],
            [
                {'text': '\U0001f4dd View All Codes', 'callback_data': 'panel_view_codes'},
                {'text': '\U0001f3e0 Main Menu', 'callback_data': 'panel_main_menu'}
            ]
        ]
    }
    return text, kb


def show_users_page(chat_id, page=0, message_id=None):
    """Send a paginated active users list to admin."""
    all_docs = list(users_col.find({}).sort("joined", -1))
    total = len(all_docs)
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    chunk = all_docs[page * PAGE_SIZE:(page + 1) * PAGE_SIZE]

    lines = [f"<b>👥 Total Users: {total}</b>\n"]
    for i, u in enumerate(chunk, start=page * PAGE_SIZE + 1):
        uid  = u['_id']
        name = u.get('first_name', 'Unknown')
        uname = u.get('username')
        plan = "Unlimited" if u.get('lifetime') else f"{u.get('credits', 0)} searches"
        uname_str = f" (@{uname})" if uname else ""
        lines.append(f"{i}. <b>{name}</b>{uname_str}")
        lines.append(f"  → ID: <code>{uid}</code> | Plan: {plan}")

    lines.append(f"\nPage {page + 1} of {total_pages}")

    nav = []
    if page > 0:
        nav.append({'text': '⬅️ Prev', 'callback_data': f'panel_users_{page - 1}'})
    if page < total_pages - 1:
        nav.append({'text': 'Next ➡️', 'callback_data': f'panel_users_{page + 1}'})
    
    kb = {
        'inline_keyboard': [
            nav,
            [{'text': '⬅️  Back to Panel', 'callback_data': 'panel_back'}]
        ]
    }

    edit_message(chat_id, message_id, "\n".join(lines), reply_markup=kb)


# PDF_PAGE_SIZE removed - use PDF_PAGE_SIZE

def show_pdf_list_page(chat_id, page=0, message_id=None):
    """Send a paginated list of all PDF deliveries to admin."""
    all_docs = list(pdf_logs_col.find({}).sort("timestamp", -1))
    total = len(all_docs)
    total_pages = max(1, (total + PDF_PAGE_SIZE - 1) // PDF_PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    chunk = all_docs[page * PDF_PAGE_SIZE:(page + 1) * PDF_PAGE_SIZE]

    lines = [f"<b>📄 All PDF Deliveries: {total}</b>\n"]
    if not chunk:
        lines.append("\n<i>No PDF deliveries found.</i>")
    else:
        for i, log in enumerate(chunk, start=page * PDF_PAGE_SIZE + 1):
            uid = log.get('user_id', 'N/A')
            uname = log.get('username', 'N/A')
            name = log.get('name', 'Unknown')
            ref = log.get('eid_or_mobile', 'N/A')
            ts = log.get('timestamp', 'N/A')
            # Format timestamp nicely
            try:
    
                dt = datetime.fromisoformat(ts)
                ts_display = dt.strftime("%d-%b %y %I:%M %p")
            except:
                ts_display = ts[:16] if len(ts) > 16 else ts
            uname_str = f"@{uname}" if uname and uname != 'N/A' else "N/A"
            record_type = log.get('type', 'aadhaar')
            type_label = "📋 PAN" if record_type == 'pan' else "📄 Aadhaar"
            lines.append(f"{i}. <b>{name}</b> ({uname_str}) [{type_label}]")
            lines.append(f"   🆔 <code>{uid}</code> | 🔢 {ref}")
            lines.append(f"   🕐 {ts_display}")

    lines.append(f"\nPage {page + 1} of {total_pages}")

    nav = []
    if page > 0:
        nav.append({'text': '⬅️ Prev', 'callback_data': f'pdflist_{page - 1}'})
    if page < total_pages - 1:
        nav.append({'text': 'Next ➡️', 'callback_data': f'pdflist_{page + 1}'})

    kb = {'inline_keyboard': [nav] if nav else []}
    kb['inline_keyboard'].append([{'text': '⬅️  Back to Panel', 'callback_data': 'panel_back'}])

    edit_message(chat_id, message_id, "\n".join(lines), reply_markup=kb)

# ============== ADMIN PDF VIEWER =============
def show_pdf_deliveries_page(chat_id, page=0, message_id=None):
    """Show paginated list of delivered PDFs with user details for admin.
    Each entry has a button to re-download the PDF from the storage channel."""
    all_docs = list(pdf_logs_col.find({}).sort("timestamp", -1))
    total = len(all_docs)
    total_pages = max(1, (total + 5 - 1) // 5)  # 5 per page
    page = max(0, min(page, total_pages - 1))
    chunk = all_docs[page * 5:(page + 1) * 5]

    if total == 0:
        text = (
            f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
            f"<b>[ Delivered PDFs ]</b>\n\n"
            f"No PDFs delivered yet."
        )
        kb = {'inline_keyboard': [[{'text': '\u2b05\ufe0f  Back to Panel', 'callback_data': 'panel_back'}]]}
        if message_id:
            edit_message(chat_id, message_id, text, reply_markup=kb)
        else:
            send_message(chat_id, text, reply_markup=kb)
        return

    lines = [f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"]
    lines.append(f"<b>[ Delivered PDFs  |  {total} total ]</b>\n")

    # Build inline keyboard with a Get PDF button per entry
    kb_rows = []

    for i, log in enumerate(chunk, start=page * 5 + 1):
        uid = log.get('user_id', 'N/A')
        uname = log.get('username', 'N/A')
        name = log.get('name', 'Unknown')
        ref = log.get('eid_or_mobile', 'N/A')
        ts = log.get('timestamp', 'N/A')
        fname = log.get('name', 'Unknown')
        log_id = log.get('_id')
        has_channel_msg = log.get('channel_message_id') is not None

        try:
            dt = datetime.fromisoformat(ts)
            ts_display = dt.strftime("%d-%b %y %I:%M %p")
        except:
            ts_display = ts[:16] if len(ts) > 16 else ts

        uname_str = f"@{uname}" if uname and uname != 'N/A' else "N/A"
        record_type = log.get('type', 'aadhaar')
        type_label = "📋 PAN" if record_type == 'pan' else "📄 Aadhaar"
        lines.append(f"{i}. <b>{fname}</b> ({uname_str}) [{type_label}]")
        lines.append(f"   \U0001f194 <code>{uid}</code> | \U0001f522 {ref}")
        lines.append(f"   \U0001f550 {ts_display}\n")

        # Add Get PDF button only for Aadhaar records with channel message (PAN has no PDF)
        if has_channel_msg and log_id and record_type != 'pan':
            kb_rows.append([{'text': f'\U0001f4e5 Get PDF — {fname} ({uname_str})', 'callback_data': f'admin_get_pdf_{log_id}'}])

    lines.append(f"Page {page + 1} of {total_pages}")

    nav = []
    if page > 0:
        nav.append({'text': '\u2b05 Prev', 'callback_data': f'panel_view_pdfs_{page - 1}'})
    if page < total_pages - 1:
        nav.append({'text': 'Next \u27a1\ufe0f', 'callback_data': f'panel_view_pdfs_{page + 1}'})

    kb = {'inline_keyboard': kb_rows if kb_rows else []}
    if nav:
        kb['inline_keyboard'].append(nav)
    kb['inline_keyboard'].append([{'text': '\u2b05\ufe0f  Back to Panel', 'callback_data': 'panel_back'}])

    text = "\n".join(lines)
    if message_id:
        edit_message(chat_id, message_id, text, reply_markup=kb)
    else:
        send_message(chat_id, text, reply_markup=kb)

# ============== ADMIN PAN SEARCH VIEWER =============
def show_pan_searches_page(chat_id, page=0, message_id=None):
    """Show paginated list of PAN search history for admin."""
    all_docs = list(pdf_logs_col.find({"type": "pan"}).sort("timestamp", -1))
    total = len(all_docs)
    total_pages = max(1, (total + 5 - 1) // 5)  # 5 per page
    page = max(0, min(page, total_pages - 1))
    chunk = all_docs[page * 5:(page + 1) * 5]

    if total == 0:
        text = (
            f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
            f"<b>[ PAN Searches ]</b>\n\n"
            f"No PAN searches recorded yet."
        )
        kb = {'inline_keyboard': [[{'text': '\u2b05\ufe0f  Back to Panel', 'callback_data': 'panel_back'}]]}
        if message_id:
            edit_message(chat_id, message_id, text, reply_markup=kb)
        else:
            send_message(chat_id, text, reply_markup=kb)
        return

    lines = [f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"]
    lines.append(f"<b>[ PAN Searches  |  {total} total ]</b>\n")

    for i, log in enumerate(chunk, start=page * 5 + 1):
        uid = log.get('user_id', 'N/A')
        uname = log.get('username', 'N/A')
        name = log.get('name', 'Unknown')
        ts = log.get('timestamp', 'N/A')
        pan_details = log.get('pan_details', {})
        pan_num = pan_details.get('pan', log.get('eid_or_mobile', 'N/A'))
        dob = pan_details.get('dob', 'N/A')
        email = pan_details.get('email', 'N/A')
        mobile = pan_details.get('mobile', 'N/A')
        address = pan_details.get('address', 'N/A')

        try:
            dt = datetime.fromisoformat(ts)
            ts_display = dt.strftime("%d-%b %y %I:%M %p")
        except:
            ts_display = ts[:16] if len(ts) > 16 else ts

        uname_str = f"@{uname}" if uname and uname != 'N/A' else "N/A"
        lines.append(f"{i}. <b>{name}</b> ({uname_str})")
        lines.append(f"   \U0001f194 <code>{uid}</code> | \U0001f4b3 <code>{pan_num}</code>")
        lines.append(f"   \U0001f4c5 {dob} | \U0001f4f1 {mobile}")
        lines.append(f"   \U0001f4e7 {email}")
        lines.append(f"   \U0001f550 {ts_display}\n")

    lines.append(f"Page {page + 1} of {total_pages}")

    nav = []
    if page > 0:
        nav.append({'text': '\u2b05 Prev', 'callback_data': f'panel_view_pan_{page - 1}'})
    if page < total_pages - 1:
        nav.append({'text': 'Next \u27a1\ufe0f', 'callback_data': f'panel_view_pan_{page + 1}'})

    kb = {'inline_keyboard': []}
    if nav:
        kb['inline_keyboard'].append(nav)
    kb['inline_keyboard'].append([{'text': '\u2b05\ufe0f  Back to Panel', 'callback_data': 'panel_back'}])

    text = "\n".join(lines)
    if message_id:
        edit_message(chat_id, message_id, text, reply_markup=kb)
    else:
        send_message(chat_id, text, reply_markup=kb)


# ============== SESSION MANAGEMENT ==============
user_sessions   = {}
_sessions_lock  = threading.Lock()

def get_session(chat_id):
    with _sessions_lock:
        return user_sessions.get(chat_id, {'step': 'main', 'data': {}, 'last_activity': time.time()})

def set_session(chat_id, step, data=None):
    with _sessions_lock:
        existing = user_sessions.get(chat_id, {})
        d = data if data is not None else existing.get('data', {})
        user_sessions[chat_id] = {'step': step, 'data': d, 'last_activity': time.time()}

def update_session_data(chat_id, key, value):
    with _sessions_lock:
        if chat_id not in user_sessions:
            user_sessions[chat_id] = {'step': 'main', 'data': {}, 'last_activity': time.time()}
        user_sessions[chat_id]['data'][key] = value
        user_sessions[chat_id]['last_activity'] = time.time()

def clear_session(chat_id):
    with _sessions_lock:
        user_sessions[chat_id] = {'step': 'main', 'data': {}, 'last_activity': time.time()}

def touch_session(chat_id):
    with _sessions_lock:
        if chat_id in user_sessions:
            user_sessions[chat_id]['last_activity'] = time.time()

def _cleanup_sessions():
    while True:
        time.sleep(20)
        try:
            expired = []
            with _sessions_lock:
                for cid, s in list(user_sessions.items()):
                    if s.get('step', 'main') != 'main':
                        idle = time.time() - s.get('last_activity', time.time())
                        if idle > SESSION_TIMEOUT:
                            user_sessions[cid] = {'step': 'main', 'data': {}, 'last_activity': time.time()}
                            expired.append(cid)
            for cid in expired:
                cleanup_pan_driver(cid)
                try:
                    send_message(cid,
                        f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                        f"<b>〔 Session Expired 〕</b>\n\n"
                        f"◈  Reason   ·  Idle for 3 minutes\n\n"
                        f"{DIVIDER}\n"
                        f"<i>◌  Select a service below to start again.</i>",
                        reply_markup=get_main_keyboard()
                    )
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Session cleanup error: {e}")

# ============== CHANNEL MEMBERSHIP ==============
# ============== CHANNEL MEMBERSHIP CACHE ==============
_channel_cache = {}
_channel_cache_lock = threading.Lock()
_CHANNEL_CACHE_TTL = 60  # 1 minute — fast detection of channel leaves

def is_single_channel_member(user_id, chat_id):
    """Check if user is a member of a single channel (with caching).
    
    The bot must be an admin in the channel for getChatMember to work.
    If the bot is not an admin, the API will return an error.
    """
    cache_key = f"{user_id}_{chat_id}"
    with _channel_cache_lock:
        if cache_key in _channel_cache:
            cached_time, cached_result = _channel_cache[cache_key]
            if time.time() - cached_time < _CHANNEL_CACHE_TTL:
                return cached_result
    
    # Cache miss - check with Telegram API
    result = False
    try:
        response = get_telegram_session().get(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getChatMember",
            params={'chat_id': chat_id, 'user_id': user_id},
            timeout=6
        )
        r = response.json()
        
        if r.get('ok'):
            status = r['result']['status']
            result = status in ('member', 'administrator', 'creator')
            logger.debug(f"Channel check for {chat_id}: user {user_id} status={status}, result={result}")
        else:
            # Log the actual error from Telegram API
            error_code = r.get('error_code', 'unknown')
            error_desc = r.get('description', 'No description')
            logger.warning(f"Channel check FAILED for {chat_id}: code={error_code}, desc={error_desc}")
            
            # Common error: bot not admin in channel
            if error_code == 400 and 'not an admin' in error_desc.lower():
                logger.error(f"BOT NOT ADMIN in channel {chat_id}! Bot must be admin to check membership.")
            elif error_code == 400 and 'chat not found' in error_desc.lower():
                logger.error(f"Channel {chat_id} not found or bot not added to channel.")
            elif error_code == 403:
                logger.error(f"Bot forbidden from accessing channel {chat_id}.")
    except Exception as e:
        logger.error(f"Channel check EXCEPTION for {chat_id}: {type(e).__name__}: {e}")
    
    # Store in cache (even False results to avoid hammering API)
    with _channel_cache_lock:
        _channel_cache[cache_key] = (time.time(), result)
    
    return result

def is_channel_member(user_id):
    """Check if user is a member of BOTH required channels."""
    if not CHANNEL_USERNAME and not CHANNEL2_USERNAME:
        return True
    ch1 = is_single_channel_member(user_id, CHANNEL_USERNAME)
    if not ch1:
        logger.info(f"User {user_id} NOT in channel 1: {CHANNEL_USERNAME}")
        return False
    ch2 = is_single_channel_member(user_id, CHANNEL2_USERNAME)
    if not ch2:
        logger.info(f"User {user_id} NOT in channel 2: {CHANNEL2_USERNAME}")
        return False
    return True

# ============== BOT USERNAME ==============
_bot_username = None
def get_bot_username():
    global _bot_username
    if _bot_username:
        return _bot_username
    # Try loading from DB first
    try:
        cached = settings_col.find_one({"_id": "bot_username"})
        if cached and cached.get("username"):
            _bot_username = cached["username"]
            return _bot_username
    except Exception:
        pass
    try:
        r = get_telegram_session().get(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe", timeout=5
        ).json()
        if r.get('ok'):
            _bot_username = r['result']['username']
            # Cache in DB
            try:
                settings_col.update_one({"_id": "bot_username"}, {"$set": {"username": _bot_username}}, upsert=True)
            except Exception:
                pass
    except Exception:
        pass
    return _bot_username or "ModxAadharbot"

# ============== TELEGRAM HELPERS ==============
def send_message(chat_id, text, reply_markup=None, _retries=2):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}
    if reply_markup:
        data['reply_markup'] = json.dumps(reply_markup)
    for attempt in range(_retries + 1):
        try:
            response = get_telegram_session().post(url, json=data, timeout=10)
            result = response.json()
            if result.get('ok'):
                return result
            # Check for retryable errors
            err_desc = result.get('description', '').lower()
            if 'retry after' in err_desc or 'too many requests' in err_desc:
                if attempt < _retries:
                    wait = 2 ** attempt
                    logger.warning(f"Telegram rate limit, retrying in {wait}s...")
                    time.sleep(wait)
                    continue
            logger.error(f"Telegram send error: {result}")
            return result
        except Exception as e:
            err_str = str(e).lower()
            if ('timeout' in err_str or 'connection' in err_str or 'read' in err_str) and attempt < _retries:
                logger.warning(f"Telegram API timeout (attempt {attempt + 1}/{_retries + 1}), retrying...")
                time.sleep(1)
                continue
            logger.error(f"Error sending message: {e}")
            return None
    return None

def send_photo(chat_id, photo, caption="", reply_markup=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    data = {'chat_id': chat_id, 'parse_mode': 'HTML'}
    if caption:
        data['caption'] = caption
    if reply_markup:
        data['reply_markup'] = json.dumps(reply_markup) if isinstance(reply_markup, dict) else reply_markup
    try:
        if isinstance(photo, bytes):
            files = {'photo': ('captcha.png', photo, 'image/png')}
            response = get_telegram_session().post(url, data=data, files=files, timeout=20)
        else:
            data['photo'] = photo
            response = get_telegram_session().post(url, data=data, timeout=20)
        return response.json()
    except Exception as e:
        logger.error(f"Error sending photo: {e}")
        return None

def edit_message(chat_id, message_id, text, reply_markup=None, _retries=2):
    if not message_id:
        return send_message(chat_id, text, reply_markup)
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/editMessageText"
    data = {'chat_id': chat_id, 'message_id': message_id, 'text': text, 'parse_mode': 'HTML'}
    if reply_markup:
        data['reply_markup'] = json.dumps(reply_markup)
    for attempt in range(_retries + 1):
        try:
            response = get_telegram_session().post(url, json=data, timeout=15)
            result = response.json()
            if result.get('ok'):
                return result
            # Check for retryable errors
            err_desc = result.get('description', '').lower()
            if ('retry after' in err_desc or 'too many requests' in err_desc) and attempt < _retries:
                wait = 2 ** attempt
                logger.warning(f"Telegram rate limit on edit, retrying in {wait}s...")
                time.sleep(wait)
                continue
            # Fallback to sending new message if edit fails
            if "message is not modified" in err_desc:
                return result
            # Don't fall back to send_message as it breaks inline keyboards
            return None
        except Exception as e:
            err_str = str(e).lower()
            if ('timeout' in err_str or 'connection' in err_str or 'read' in err_str) and attempt < _retries:
                logger.warning(f"Telegram edit timeout (attempt {attempt + 1}/{_retries + 1}), retrying...")
                time.sleep(1)
                continue
            logger.error(f"Error editing message: {e}")
            return None
    return None

def make_progress_bar(percent, total_blocks=20):
    filled = int(round(total_blocks * (percent / 100)))
    filled = max(0, min(total_blocks, filled))
    bar = ''
    for i in range(total_blocks):
        if i < filled - 2: bar += '█'
        elif i < filled: bar += '▓'
        elif i == filled: bar += '▒'
        else: bar += '░'
    return f"[{bar}] {percent}%"

def delete_message(chat_id, message_id):
    if not message_id:
        return None
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteMessage"
    data = {'chat_id': chat_id, 'message_id': message_id}
    try:
        response = get_telegram_session().post(url, json=data, timeout=5)
        return response.json()
    except Exception as e:
        logger.error(f"Error deleting message: {e}")
        return None

def animate_progress_thread(chat_id, status_msg_id, stop_event, finish_event=None, done_event=None):
    """Crazy animated progress thread with multiple visual effects."""
    stages = [
        {"title": "\U0001f517 Connecting",  "min_pct": 0,   "max_pct": 20,  "speed": 0.08, "spinners": ['\u280b','\u2819','\u2839','\u2838','\u283c','\u2834','\u2826','\u2827','\u2807','\u280f'], "msgs": ["Establishing secure tunnel\u2026", "Handshaking with Govt portal\u2026", "Opening encrypted channel\u2026"]},
        {"title": "\U0001f9e0 Captcha",     "min_pct": 20,  "max_pct": 40,  "speed": 0.06, "spinners": ['\u28fe','\u28fd','\u28fb','\u28bf','\u28ff','\u28ef','\u28f7'], "msgs": ["Neural network analyzing captcha\u2026", "Beta OCR decoding characters\u2026", "Validating captcha solution\u2026"]},
        {"title": "\U0001f4e8 OTP",         "min_pct": 40,  "max_pct": 50,  "speed": 0.05, "spinners": ['\u25b8','\u25b9','\u25ba','\u25bb'], "msgs": ["Dispatching verification code\u2026", "SMS delivery confirmed\u2026"]},
        {"title": "\U0001f4e5 Download",    "min_pct": 50,  "max_pct": 75,  "speed": 0.08, "spinners": ['\U0001f680','\u2708\ufe0f','\U0001f6f8'], "msgs": ["Fetching encrypted Aadhaar PDF\u2026", "Retrieving PDF document\u2026", "Receiving encrypted payload\u2026"]},
        {"title": "\U0001f513 Decrypt",     "min_pct": 75,  "max_pct": 95,  "speed": 0.06, "spinners": ['\U0001f4bb','\u2699\ufe0f','\U0001f527'], "msgs": ["Cracking PDF password\u2026", "PyPDF2 decrypting\u2026", "Pattern matching: NAME+YEAR\u2026"]},
        {"title": "\u2705 Deliver",     "min_pct": 95,  "max_pct": 100, "speed": 0.04, "spinners": ['\u2726','\u2727','\u2605','\u2606'], "msgs": ["Delivering your Aadhaar PDF\u2026", "\u2728 Complete!"]},
    ]

    percent = 5
    stage_idx = 0
    msg_counter = 0

    while not stop_event.is_set():
        if finish_event and finish_event.is_set():
            # Fast-forward to 100%
            edit_message(chat_id, status_msg_id,
                f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                f"<b>[\u2705 Complete ]</b>\n\n"
                f"\U0001f525 \u2726 <code>[{'█' * 20}] 100%</code> \u2726 \U0001f525\n"
                f"<i>\u2728 Delivering your PDF\u2026</i>"
            )
            if done_event: done_event.set()
            return

        stage = stages[min(stage_idx, len(stages) - 1)]

        increment = random.randint(2, 6)
        percent += increment
        percent = min(stage['max_pct'], percent)

        spin = stage['spinners'][msg_counter % len(stage['spinners'])]
        detail = stage['msgs'][msg_counter % len(stage['msgs'])]

        filled = int(percent / 5)
        bar = '█' * filled + '▒' * min(2, 20-filled) + '░' * max(0, 20-filled-2)

        text = (
            f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
            f"<b>[⚡ {stage['title']} ]</b>\n\n"
            f"\U0001f525 {spin} <code>[{bar}] {percent}%</code> {spin} \U0001f525\n"
            f"<i>⚡ {detail}</i>"
        )
        edit_message(chat_id, status_msg_id, text)

        msg_counter += 1

        if percent >= stage['max_pct'] and stage_idx < len(stages) - 1:
            stage_idx += 1
            continue

        time.sleep(stage['speed'])

def send_log(text):
    """Send a log message to the log channel silently."""
    try:
        send_message(LOG_CHANNEL_ID, text)
    except Exception as e:
        logger.error(f"Log channel error: {e}")

def is_user_allowed(chat_id):
    """Check if a user is allowed (has valid access)."""
    u = get_user(chat_id)
    if not u:
        return False
    if u.get('banned'):
        return False
    if u.get('lifetime') or u.get('is_premium'):
        expiry = u.get('expiry')
        if expiry:
            try:
                return datetime.fromisoformat(expiry) > datetime.now()
            except:
                pass
        return True
    return u.get('credits', 0) > 0

def broadcast_receiver_thread():
    """Listen for broadcast messages from other bots and forward to local users."""
    import time as _time
    while True:
        try:
            last_bc = db.broadcasts.find_one(
                {"_id": "last_broadcast"},
                sort=[("timestamp", -1)]
            )
            if last_bc and last_bc.get("sender") != "bot1":
                local_users = list(db.users.find({}, {"chat_id": 1}))
                for u in local_users:
                    chat_id = u["chat_id"]
                    if not is_user_allowed(chat_id) and chat_id not in OWNER_IDS:
                        send_message(chat_id, last_bc["text"])
                        _time.sleep(0.05)
            _time.sleep(10)
        except Exception as e:
            print(f"[BROADCASTReceiver] Error: {e}")
            _time.sleep(10)

def answer_callback_query(callback_query_id, text=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery"
    data = {'callback_query_id': callback_query_id}
    if text:
        data['text'] = text
    try:
        get_telegram_session().post(url, json=data, timeout=5)
    except Exception as e:
        logger.error(f"Error answering callback: {e}")

def copy_message(chat_id, from_chat_id, message_id, reply_markup=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/copyMessage"
    data = {
        'chat_id': chat_id,
        'from_chat_id': from_chat_id,
        'message_id': message_id
    }
    if reply_markup:
        data['reply_markup'] = json.dumps(reply_markup) if isinstance(reply_markup, dict) else reply_markup
    try:
        response = get_telegram_session().post(url, json=data, timeout=15)
        return response.json()
    except Exception as e:
        logger.error(f"Error copying message: {e}")
        return None

def send_document(chat_id, file_path, caption=None, filename="Aadhaar.pdf", delete_file=True, _retries=2):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    for attempt in range(_retries + 1):
        try:
            with open(file_path, 'rb') as f:
                files = {'document': (filename, f, 'application/pdf')}
                data = {'chat_id': chat_id, 'parse_mode': 'HTML'}
                if caption:
                    data['caption'] = caption
                response = get_telegram_session().post(url, data=data, files=files, timeout=60).json()
            if response.get('ok'):
                if delete_file:
                    try:
                        os.remove(file_path)
                    except Exception:
                        pass
                return response
            # Check for retryable errors
            err_desc = response.get('description', '').lower()
            if ('retry after' in err_desc or 'too many requests' in err_desc) and attempt < _retries:
                wait = 2 ** attempt
                logger.warning(f"Telegram rate limit on document send, retrying in {wait}s...")
                time.sleep(wait)
                continue
            logger.error(f"Telegram document send error: {response}")
            return response
        except Exception as e:
            err_str = str(e).lower()
            if ('timeout' in err_str or 'connection' in err_str or 'read' in err_str) and attempt < _retries:
                logger.warning(f"Telegram document send timeout (attempt {attempt + 1}/{_retries + 1}), retrying...")
                time.sleep(2)
                continue
            logger.error(f"Error sending document: {e}")
            return None
    return None

# ============== KEYBOARDS ==============
# Main persistent keyboard (always at bottom)
def get_main_keyboard():
    return {
        'keyboard': [
            ['◆ Mobile Number'],
            ['◆ Aadhaar', '◆ Admin Panel'],
        ],
        'resize_keyboard': True,
        'one_time_keyboard': False
    }

def get_aadhaar_sub_keyboard():
    return {
        'keyboard': [
            ['◆ Mobile Number', '◆ Aadhaar Number'],
            ['◆ EID'],
            ['⬅ Back'],
        ],
        'resize_keyboard': True,
        'one_time_keyboard': False
    }

def get_pan_sub_keyboard():
    return {
        'keyboard': [
            ['◆ PAN via Mobile'],
            ['⬅ Back'],
        ],
        'resize_keyboard': True,
        'one_time_keyboard': False
    }

# Inline — only for contextual actions inside flows
def get_cancel_keyboard():
    return {'inline_keyboard': [[{'text': '✗  Cancel', 'callback_data': 'cancel'}]]}

def get_join_keyboard():
    return {
        'inline_keyboard': [
            [{'text': '📢  Join Channel 1', 'url': CHANNEL_LINK}],
            [{'text': '📢  Join Channel 2', 'url': CHANNEL2_LINK}],
            [{'text': '🟢  Check Joined', 'callback_data': 'check_join'}]
        ]
    }

def show_buy_menu(chat_id, message_id=None):
    kb = {
        'inline_keyboard': [
            [{'text': '🔢 Limited Search Plans', 'callback_data': 'buy_menu_limited'}],
            [{'text': '♾ Unlimited Plans', 'callback_data': 'buy_menu_unlimited'}],
            [{'text': '⬅️ Back to Profile', 'callback_data': 'credits'}]
        ]
    }
    edit_message(
        chat_id, message_id,
        f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
        f"💳 <b>Choose your plan type:</b>\n\n"
        f"💡 <i>For payment, contact admin:</i>\n👤 @kittu2141",
        reply_markup=kb
    )



def show_referral_info(chat_id):
    username  = get_bot_username()
    link      = f"https://t.me/{username}?start=ref_{chat_id}"
    u         = get_user(chat_id)
    ref_count = u.get('referral_count', 0) if u else 0
    earned_hrs = ref_count  # 1 hour per referral
    send_message(
        chat_id,
        f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
        f"<b>〔 Referral 〕</b>\n\n"
        f"<code>{link}</code>\n\n"
        f"◈  Friends joined  ·  {ref_count}\n"
        f"◈  Hours earned  ·  {earned_hrs}h\n\n"
        f"{DIVIDER}\n"
        f"<i>◌  Share your link — earn +1 hour per friend who joins</i>"
    )

def show_credits_info(chat_id, message_id=None):
    u = get_user(chat_id)
    expiry_str = u.get('expiry', '') if u else ''
    if u and u.get('lifetime'):
        subscription_display = '♾️ Lifetime Unlimited'
    elif expiry_str:
        try:
            exp_dt = datetime.fromisoformat(expiry_str)
            if exp_dt > datetime.now():
                remaining = exp_dt - datetime.now()
                hrs = int(remaining.total_seconds() // 3600)
                mins = int((remaining.total_seconds() % 3600) // 60)
                if hrs >= 24:
                    days = hrs // 24
                    subscription_display = f'✅ {days}d {hrs%24}h remaining'
                else:
                    subscription_display = f'✅ {hrs}h {mins}m remaining'
            else:
                subscription_display = '❌ Expired'
        except:
            subscription_display = '❌ No access'
    else:
        subscription_display = '❌ No access'
    
    username = u.get('username') if u else None
    username_display = f"@{username}" if username else "N/A"
    searches = u.get('searches', 0) if u else 0

    bot_username = get_bot_username()
    link = f"https://t.me/{bot_username}?start=ref_{chat_id}"

    text = (
        f"── <b>PROFILE OVERVIEW</b> ──\n\n"
        f"<b>Username:</b> {username_display}\n"
        f"<b>User ID:</b> <code>{chat_id}</code>\n"
        f"<b>Total Searches:</b> <b>{searches}</b>\n"
        f"<b>Subscription:</b> {subscription_display}\n\n"
        f"<b>Referral Link:</b> <code>{link}</code>"
    )

    owner_clean = OWNER_USERNAME.replace("@", "")
    kb = {
        'inline_keyboard': [
            [
                {'text': '💳 Buy Credits', 'callback_data': 'buy'},
                {'text': '💬 Support', 'callback_data': 'support_info'}
            ]
        ]
    }

    if message_id:
        edit_message(chat_id, message_id, text, reply_markup=kb)
    else:
        send_message(chat_id, text, reply_markup=kb)

# ============== GATES ==============
def channel_gate(chat_id):
    """Check if user is a member of both required channels.
    If not, show join buttons and return False."""
    # Admins bypass channel gate
    if int(chat_id) in OWNER_IDS:
        return True
    if not CHANNEL_USERNAME and not CHANNEL2_USERNAME:
        return True
    if is_channel_member(chat_id):
        return True
    # User left or never joined — block access and show join buttons
    send_message(
        chat_id,
        f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
        f"<b>〔 ⚠️  Channel Required 〕</b>\n\n"
        f"You must join <b>both channels</b> to use this bot.\n"
        f"If you leave the channels, the bot will <b>stop working</b>.\n\n"
        f"📢  Channel 1:  {CHANNEL_USERNAME}\n"
        f"📢  Channel 2:  {CHANNEL2_USERNAME}\n\n"
        f"{DIVIDER}\n"
        f"<i>◌  Join both channels, then tap '✅ Check Joined'.</i>",
        reply_markup=get_join_keyboard()
    )
    return False

def credit_gate(chat_id):
    # Admins bypass
    if int(chat_id) in OWNER_IDS:
        return True
    u = get_user(chat_id)
    if not u:
        return False
    if u.get('lifetime'):
        return True
    # Check time-based expiry
    expiry_str = u.get('expiry', '')
    if expiry_str:
        try:
            if datetime.fromisoformat(expiry_str) > datetime.now():
                return True
        except:
            pass
    # No valid access
    send_message(
        chat_id,
        f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
        f"<b>\u23f0 Access Expired!</b>\n\n"
        f"Your free time has ended.\n\n"
        f"\u25b8 Refer a friend to get +1 hour\n"
        f"\u25b8 Contact admin for more time\n\n"
        f"\U0001f464 {OWNER_USERNAME}",
        reply_markup=get_main_keyboard()
    )
    return False

# ============== PDF DELIVERY ==============
def extract_aadhaar_qr_data(pdf_path):
    """Extract and decode QR code data from a decrypted Aadhaar PDF.
    Returns a dict with decoded QR data and parsed XML fields, or None."""
    try:
        import io
        import zlib
        import xml.etree.ElementTree as ET
        from PIL import Image
        import cv2
        import numpy as np
        try:
            from pyzbar.pyzbar import decode as pyzbar_decode
            has_pyzbar = True
        except ImportError:
            has_pyzbar = False
        
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            
            qr_results = []
            
            # Method 1: Try extracting QR from embedded images
            for page_idx, page in enumerate(reader.pages):
                if not hasattr(page, 'images'):
                    continue
                
                for img_idx, image_file in enumerate(page.images):
                    image_data = image_file.data
                    
                    # Skip tiny images
                    if len(image_data) < 1000:
                        continue
                    
                    # Load image with OpenCV
                    nparr = np.frombuffer(image_data, np.uint8)
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    if img is None:
                        continue
                    
                    # Try pyzbar first (more reliable)
                    if has_pyzbar:
                        pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
                        decoded_objs = pyzbar_decode(pil_img)
                        for obj in decoded_objs:
                            qr_data = obj.data
                            if len(qr_data) > 50:  # QR code should have substantial data
                                qr_results.append(qr_data)
                    
                    # Fallback: OpenCV QR detector
                    if not qr_results:
                        try:
                            detector = cv2.QRCodeDetector()
                            data, _, _ = detector.detectAndDecode(img)
                            if data and len(data) > 50:
                                qr_results.append(data.encode('utf-8') if isinstance(data, str) else data)
                        except Exception:
                            pass
            
            # Method 2: Render page and scan for QR (fallback)
            if not qr_results:
                for page_idx, page in enumerate(reader.pages):
                    try:
                        # Convert page to image using PyPDF2's built-in rendering is limited
                        # Skip this for now as embedded images should work
                        pass
                    except Exception:
                        pass
            
            if not qr_results:
                logger.warning("No QR code found in Aadhaar PDF")
                return None
            
            # Parse the QR data - Aadhaar QR contains XML or compressed data
            qr_result = qr_results[0]  # Use first QR found
            
            result = {
                'raw_data': qr_result,
                'raw_text': '',
                'fields': {},
                'xml_data': ''
            }
            
            # Try to decode as UTF-8 text first
            try:
                text_data = qr_result.decode('utf-8')
                result['raw_text'] = text_data
                
                # Check if it's XML
                if text_data.startswith('<?xml') or text_data.startswith('<PrintLetterBarcodeData'):
                    result['xml_data'] = text_data
                    result['fields'] = _parse_aadhaar_xml(text_data)
                    return result
                
                # Check if it's compressed (zlib)
                try:
                    decompressed = zlib.decompress(qr_result)
                    text_data = decompressed.decode('utf-8', errors='ignore')
                    result['raw_text'] = text_data
                    result['xml_data'] = text_data
                    result['fields'] = _parse_aadhaar_xml(text_data)
                    return result
                except Exception:
                    pass
                
                # Try base64 decode
                try:
                    import base64
                    decoded = base64.b64decode(text_data)
                    try:
                        decompressed = zlib.decompress(decoded)
                        text_data = decompressed.decode('utf-8', errors='ignore')
                    except Exception:
                        text_data = decoded.decode('utf-8', errors='ignore')
                    result['raw_text'] = text_data
                    result['xml_data'] = text_data
                    result['fields'] = _parse_aadhaar_xml(text_data)
                    return result
                except Exception:
                    pass
                    
            except UnicodeDecodeError:
                # Binary data - try zlib decompress
                try:
                    decompressed = zlib.decompress(qr_result)
                    text_data = decompressed.decode('utf-8', errors='ignore')
                    result['raw_text'] = text_data
                    result['xml_data'] = text_data
                    result['fields'] = _parse_aadhaar_xml(text_data)
                    return result
                except Exception:
                    pass
            
            # If we couldn't parse XML, return raw data
            result['raw_text'] = str(qr_result[:500])
            return result
            
    except Exception as e:
        logger.error(f"QR code extraction error: {e}")
        return None


def _parse_aadhaar_xml(xml_str):
    """Parse Aadhaar XML data from QR code."""
    fields = {}
    try:
        # Clean up the XML string
        xml_str = xml_str.strip()
        
        # Try to parse as XML
        if '<PrintLetterBarcodeData' in xml_str:
            # Extract the XML part
            start = xml_str.index('<PrintLetterBarcodeData')
            end = xml_str.rfind('>') + 1
            xml_content = xml_str[start:end]
            
            # Parse XML
            root = ET.fromstring(xml_content)
            
            # Extract attributes
            attr_map = {
                'uid': 'aadhaar',
                'name': 'name',
                'gender': 'gender',
                'yob': 'year_of_birth',
                'dob': 'dob',
                'phone': 'phone',
                'email': 'email',
                'co': 'care_of',
                'house': 'house',
                'street': 'street',
                'lm': 'landmark',
                'loc': 'location',
                'vtc': 'village_town_city',
                'po': 'post_office',
                'dist': 'district',
                'state': 'state',
                'pc': 'pincode',
                'country': 'country'
            }
            
            for attr, field_name in attr_map.items():
                value = root.get(attr, '')
                if value:
                    fields[field_name] = value
            
        else:
            # Try parsing as key-value pairs
            for line in xml_str.split('\n'):
                if ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        key = parts[0].strip().lower()
                        value = parts[1].strip()
                        if key and value:
                            fields[key] = value
    except Exception as e:
        logger.error(f"XML parsing error: {e}")
    
    return fields


def enhance_aadhaar_photo(image_path, output_path=None):
    """Enhance Aadhaar photo: improve quality, detect face, crop, and resize.
    Returns the path to the enhanced photo, or original if enhancement fails."""
    try:
        import cv2
        import numpy as np
        
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            logger.warning(f"Could not load image for enhancement: {image_path}")
            return image_path
        
        original = img.copy()
        h, w = img.shape[:2]
        
        # Step 1: Enhance image quality
        # Adjust brightness and contrast
        # alpha = contrast (1.0-2.0), beta = brightness (0-50)
        img = cv2.convertScaleAbs(img, alpha=1.3, beta=10)
        
        # Enhance sharpness using unsharp masking
        gaussian = cv2.GaussianBlur(img, (0, 0), 3)
        img = cv2.addWeighted(img, 1.5, gaussian, -0.5, 0)
        
        # Denoise slightly
        img = cv2.fastNlMeansDenoisingColored(img, None, 5, 5, 7, 21)
        
        # Step 2: Detect face using Haar Cascade
        face_cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(face_cascade_path)
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.05,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        face_img = None
        
        if len(faces) > 0:
            # Get the largest face (most likely the main portrait)
            faces_sorted = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
            (x, y, fw, fh) = faces_sorted[0]
            
            # Add padding around face (25% of face size)
            padding_x = int(fw * 0.25)
            padding_y = int(fh * 0.25)
            
            x1 = max(0, x - padding_x)
            y1 = max(0, y - padding_y)
            x2 = min(w, x + fw + padding_x)
            y2 = min(h, y + fh + padding_y)
            
            face_img = img[y1:y2, x1:x2]
            logger.info(f"Face detected at ({x},{y}) size {fw}x{fh}, cropped with padding")
        else:
            logger.info("No face detected, using full enhanced image")
            face_img = img
        
        # Step 3: Resize for optimal Telegram display (max 512px)
        max_dim = 512
        fh, fw = face_img.shape[:2]
        
        if fh > max_dim or fw > max_dim:
            if fh > fw:
                new_h = max_dim
                new_w = int(fw * (max_dim / float(fh)))
            else:
                new_w = max_dim
                new_h = int(fh * (max_dim / float(fw)))
            face_img = cv2.resize(face_img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        # Save enhanced image
        if output_path is None:
            base, ext = os.path.splitext(image_path)
            output_path = f"{base}_enhanced.jpg"
        
        cv2.imwrite(output_path, face_img, [cv2.IMWRITE_JPEG_QUALITY, 95])
        logger.info(f"Enhanced photo saved: {output_path}")
        
        return output_path
    except Exception as e:
        logger.error(f"Photo enhancement error: {e}")
        return image_path


def extract_aadhaar_photo(pdf_path, output_path=None):
    """Extract the profile photo from a decrypted Aadhaar PDF.
    Returns the path to the extracted photo, or None if extraction fails."""
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            
            # Try to extract images from each page
            for page_idx, page in enumerate(reader.pages):
                if not hasattr(page, 'images'):
                    continue
                
                for img_idx, image_file in enumerate(page.images):
                    # Get image data
                    image_data = image_file.data
                    image_name = image_file.name.lower()
                    
                    # Skip tiny images (likely icons/logos, not the photo)
                    if len(image_data) < 5000:  # Less than 5KB is likely not a photo
                        continue
                    
                    # Skip SVG and non-image files
                    if image_name.endswith('.svg') or image_name.endswith('.xml'):
                        continue
                    
                    # Determine file extension
                    ext = 'jpg'
                    if image_data[:8] == b'\x89PNG\r\n\x1a\n':
                        ext = 'png'
                    elif image_data[:4] == b'%PDF':
                        continue  # Skip embedded PDFs
                    elif image_data[:2] == b'\xff\xd8':
                        ext = 'jpg'
                    elif b'JFIF' in image_data[:20] or b'Exif' in image_data[:20]:
                        ext = 'jpg'
                    elif image_data[:4] == b'RIFF':
                        ext = 'webp'
                    
                    # Check image dimensions if possible (photo should be reasonably sized)
                    # For JPEG, check if it's large enough to be a photo
                    if ext == 'jpg' and len(image_data) < 10000:  # Less than 10KB
                        continue
                    
                    if output_path is None:
                        output_path = os.path.abspath(f"aadhaar_photo_{page_idx}_{img_idx}.{ext}")
                    
                    with open(output_path, 'wb') as out_f:
                        out_f.write(image_data)
                    
                    logger.info(f"Extracted Aadhaar photo: {output_path} ({len(image_data)} bytes)")
                    return output_path
            
            # If no suitable image found, try extracting from XObject resources directly
            for page_idx, page in enumerate(reader.pages):
                if '/XObject' not in page.get('/Resources', {}):
                    continue
                
                x_objects = page['/Resources']['/XObject'].get_object()
                for obj_name in x_objects:
                    x_obj = x_objects[obj_name].get_object()
                    if x_obj.get('/Subtype') == '/Image':
                        # Get image properties
                        width = x_obj.get('/Width', 0)
                        height = x_obj.get('/Height', 0)
                        
                        # Skip small images (icons)
                        if width < 50 or height < 50:
                            continue
                        
                        # Extract image data
                        image_data = x_obj.get_data()
                        if len(image_data) < 5000:
                            continue
                        
                        # Determine format from filter
                        filter_type = x_obj.get('/Filter', '')
                        if isinstance(filter_type, list):
                            filter_type = filter_type[0] if filter_type else ''
                        
                        ext = 'jpg'
                        if 'DCTDecode' in str(filter_type):
                            ext = 'jpg'
                        elif 'FlateDecode' in str(filter_type):
                            ext = 'png'
                        elif 'JPXDecode' in str(filter_type):
                            ext = 'jp2'
                        elif 'CCITTFaxDecode' in str(filter_type):
                            ext = 'tiff'
                        
                        if output_path is None:
                            output_path = os.path.abspath(f"aadhaar_photo_xobj.{ext}")
                        
                        with open(output_path, 'wb') as out_f:
                            out_f.write(image_data)
                        
                        logger.info(f"Extracted Aadhaar photo (XObject): {output_path} ({len(image_data)} bytes, {width}x{height})")
                        return output_path
            
            logger.warning("No suitable photo found in Aadhaar PDF")
            return None
    except Exception as e:
        logger.error(f"Photo extraction error: {e}")
        return None


def extract_aadhaar_details(pdf_path):
    """Extract Aadhaar details from decrypted PDF text."""
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ''
            for page in reader.pages:
                text += page.extract_text() or ''
        
        details = {
            'name': '', 'gender': '', 'dob': '', 'aadhaar': '',
            'address': '', 'pincode': '', 'state': '', 'district': '',
            'phone': '', 'email': '', 'father_name': '',
            'year_of_birth': '', 'issued_date': '', 'vid': '',
            'blood_group': '', 'age': ''
        }
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            # Name extraction
            if 'Name' in line_stripped and ':' in line_stripped:
                parts = line_stripped.split(':', 1)
                if len(parts) > 1 and parts[1].strip():
                    details['name'] = parts[1].strip()
            
            # Gender extraction
            if 'Gender' in line_stripped and ':' in line_stripped:
                parts = line_stripped.split(':', 1)
                if len(parts) > 1:
                    val = parts[1].strip().upper()
                    if val in ['MALE', 'FEMALE', 'OTHER']:
                        details['gender'] = val
            if not details['gender']:
                for word in ['Male', 'Female', 'MALE', 'FEMALE']:
                    if word in line_stripped:
                        details['gender'] = word.upper()
                        break
            
            # DOB extraction
            if ('DOB' in line_stripped or 'Date of Birth' in line_stripped) and ':' in line_stripped:
                parts = line_stripped.split(':', 1)
                if len(parts) > 1:
                    details['dob'] = parts[1].strip()
            
            # Year of Birth extraction (some Aadhaar PDFs show this separately)
            if ('Year of Birth' in line_stripped or 'YoB' in line_stripped) and ':' in line_stripped:
                parts = line_stripped.split(':', 1)
                if len(parts) > 1:
                    yob = parts[1].strip()
                    if re.match(r'\d{4}', yob):
                        details['year_of_birth'] = yob
            
            # Age extraction
            if 'Age' in line_stripped and ':' in line_stripped:
                parts = line_stripped.split(':', 1)
                if len(parts) > 1:
                    age_match = re.search(r'(\d+)', parts[1])
                    if age_match:
                        details['age'] = age_match.group(1)
            
            # Father's name extraction (handles Father's/Husband's)
            if ('Father' in line_stripped or 'Husband' in line_stripped) and ':' in line_stripped:
                parts = line_stripped.split(':', 1)
                if len(parts) > 1 and parts[1].strip():
                    details['father_name'] = parts[1].strip()
            
            # Aadhaar number extraction (12 digits)
            aadhaar_match = re.search(r'\b(\d{4}\s?\d{4}\s?\d{4})\b', line_stripped)
            if aadhaar_match and not details['aadhaar']:
                details['aadhaar'] = aadhaar_match.group(1)
            
            # VID (Virtual ID) extraction (16 digits)
            vid_match = re.search(r'\b(\d{4}\s?\d{4}\s?\d{4}\s?\d{4})\b', line_stripped)
            if vid_match:
                vid_num = vid_match.group(1).replace(' ', '')
                if len(vid_num) == 16 and vid_num != details['aadhaar'].replace(' ', ''):
                    details['vid'] = vid_match.group(1)
            
            # Blood Group extraction
            bg_match = re.search(r'(A\+|A-|B\+|B-|AB\+|AB-|O\+|O-|A Positive|A Negative|B Positive|B Negative|AB Positive|AB Negative|O Positive|O Negative|APOS|ANEG|BPOS|BNEG|ABPOS|ABNEG|OPOS|ONEG)', line_stripped, re.IGNORECASE)
            if bg_match:
                details['blood_group'] = bg_match.group(1).upper()
            
            # Issued Date / Generation Date extraction
            if ('Issued' in line_stripped or 'Generated' in line_stripped or 'Date of Issue' in line_stripped) and ':' in line_stripped:
                parts = line_stripped.split(':', 1)
                if len(parts) > 1:
                    date_str = parts[1].strip()
                    if re.search(r'\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4}|\d{4}', date_str):
                        details['issued_date'] = date_str
            # Also check for date patterns on lines near "AADHAAR" or "UIDAI"
            if not details['issued_date'] and i > 0:
                prev_line = lines[i-1].strip() if i > 0 else ''
                if ('AADHAAR' in prev_line or 'UIDAI' in prev_line) and re.search(r'\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4}', line_stripped):
                    details['issued_date'] = line_stripped
            
            # Pincode extraction (6 digits)
            if not details['pincode']:
                pin_match = re.search(r'\b(\d{6})\b', line_stripped)
                if pin_match:
                    details['pincode'] = pin_match.group(1)
            
            # State extraction
            if 'State' in line_stripped and ':' in line_stripped:
                parts = line_stripped.split(':', 1)
                if len(parts) > 1:
                    details['state'] = parts[1].strip()
            
            # District extraction
            if ('District' in line_stripped or 'Dist' in line_stripped) and ':' in line_stripped:
                parts = line_stripped.split(':', 1)
                if len(parts) > 1:
                    details['district'] = parts[1].strip()
            
            # Phone/Mobile extraction
            if 'Phone' in line_stripped or 'Mobile' in line_stripped:
                phone_match = re.search(r'\b(\d{10})\b', line_stripped)
                if phone_match:
                    details['phone'] = phone_match.group(1)
            
            # Email extraction
            if 'Email' in line_stripped and ':' in line_stripped:
                parts = line_stripped.split(':', 1)
                if len(parts) > 1:
                    details['email'] = parts[1].strip()
            
            # Address extraction - collect lines with address-related keywords
            addr_kws = ['House', 'Street', 'Road', 'Village', 'Post', 'Colony', 'Ward', 'Block', 'Tehsil', 'Sub', 'City', 'Town', 'Mandal', 'Landmark', 'Area', 'Locality']
            if any(kw in line_stripped for kw in addr_kws):
                if not details['address']:
                    details['address'] = line_stripped
                elif line_stripped not in details['address']:
                    details['address'] += ', ' + line_stripped
        
        # Build full address from district/state/pincode if address is sparse
        if details['district'] and details['state']:
            loc_parts = [p for p in [details['district'], details['state']] if p]
            loc_str = ', '.join(loc_parts)
            if details['pincode']:
                loc_str += ' - ' + details['pincode']
            if not details['address']:
                details['address'] = loc_str
            elif loc_str not in details['address']:
                details['address'] += ', ' + loc_str
        
        # If we only have year_of_birth but no DOB, show year
        if not details['dob'] and details['year_of_birth']:
            details['dob'] = details['year_of_birth']
        
        return details
    except Exception as e:
        logger.error(f"PDF text extraction error: {e}")
        return None

def deliver_pdf(chat_id, pdf_path, verified_name, status_msg_id=None, stop_event=None, eid_or_mobile='N/A', finish_event=None, done_event=None):
    name_display = verified_name if verified_name and verified_name.strip() else "Mr."
    # Ensure absolute path
    pdf_path = os.path.abspath(pdf_path)

    try:
        if not os.path.exists(pdf_path):
            if stop_event:
                stop_event.set()
            logger.error(f"PDF file not found: {pdf_path}")
            if status_msg_id:
                delete_message(chat_id, status_msg_id)
            send_message(chat_id, f"<b>{BOT_NAME}</b>\n{DIVIDER}\n❌ PDF file not found. Please try again.")
            deduct_credit(chat_id)
            clear_session(chat_id)
            return

        crack_success, password, decrypted_path, _ = bot.crack_pdf_with_name(pdf_path, name_display, None)
        tag = get_user_log_tag(chat_id)

        if crack_success and decrypted_path and os.path.exists(decrypted_path):
            logger.info(f"🎉 {tag} UNLOCKED PDF SUCCESS! Name: '{name_display}' | Password: '{password}' | Delivered.")
        else:
            logger.warning(f"⚠️ {tag} Password crack failed for name='{name_display}'. Sending locked PDF.")

        # Stop animation thread and delete status message right before sending document
        if stop_event:
            stop_event.set()
        if status_msg_id:
            delete_message(chat_id, status_msg_id)
            status_msg_id = None

        if crack_success and decrypted_path and os.path.exists(decrypted_path):
            caption = (
                f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                f"<b>〔 Document Ready  ✓ 〕</b>\n\n"
                f"◈  Name    ·  {name_display}\n"
                f"◈  Format  ·  e-Aadhaar PDF\n"
                f"◈  Status  ·  <b>Unlocked</b>\n"
                f"{DIVIDER}"
            )
            send_document(chat_id, decrypted_path, caption=caption, filename="Aadhaar.pdf", delete_file=False)
            
            # Extract and send photo from Aadhaar PDF
            try:
                photo_path = extract_aadhaar_photo(decrypted_path)
                if photo_path and os.path.exists(photo_path):
                    # Enhance photo quality and detect face
                    enhanced_path = enhance_aadhaar_photo(photo_path)
                    
                    # Determine which file to send
                    send_path = enhanced_path if enhanced_path and os.path.exists(enhanced_path) else photo_path
                    
                    # Check if face was detected (enhanced file is different from original)
                    face_detected = enhanced_path and enhanced_path != photo_path and os.path.exists(enhanced_path)
                    
                    status_text = "Enhanced & Face Detected" if face_detected else "Extracted from PDF"
                    
                    photo_caption = (
                        f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                        f"<b>〔 Aadhaar Photo 〕</b>\n\n"
                        f"◈  Name    ·  {name_display}\n"
                        f"◈  Status  ·  <b>{status_text}</b>\n"
                        f"{DIVIDER}"
                    )
                    send_photo(chat_id, send_path, caption=photo_caption)
                    
                    # Clean up files
                    try:
                        if os.path.exists(photo_path):
                            os.remove(photo_path)
                        if enhanced_path and os.path.exists(enhanced_path) and enhanced_path != photo_path:
                            os.remove(enhanced_path)
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"Photo extraction/send error: {e}")
            
            # Send decrypted (no-password) PDF to admin channel + both admin owners
            try:
                log_pdf_delivery(chat_id, decrypted_path, verified_name, eid_or_mobile)
            except Exception as e:
                logger.error(f"Admin PDF forward error: {e}")
            # Send text details to user after PDF (before deleting file)
            try:
                details = extract_aadhaar_details(decrypted_path)
                if details:
                    d_name = details.get('name', name_display) or name_display
                    d_gender = details.get('gender', 'N/A') or 'N/A'
                    d_dob = details.get('dob', 'N/A') or 'N/A'
                    d_aadhaar = details.get('aadhaar', 'N/A') or 'N/A'
                    d_address = details.get('address', 'N/A') or 'N/A'
                    d_father = details.get('father_name', 'N/A') or 'N/A'
                    d_state = details.get('state', 'N/A') or 'N/A'
                    d_district = details.get('district', 'N/A') or 'N/A'
                    d_pincode = details.get('pincode', 'N/A') or 'N/A'
                    d_phone = details.get('phone', 'N/A') or 'N/A'
                    d_email = details.get('email', 'N/A') or 'N/A'
                    d_yob = details.get('year_of_birth', '') or ''
                    d_issued = details.get('issued_date', 'N/A') or 'N/A'
                    d_vid = details.get('vid', '') or ''
                    d_blood = details.get('blood_group', '') or ''
                    d_age = details.get('age', '') or ''
                    
                    # Format Aadhaar number with spaces
                    if d_aadhaar != 'N/A' and len(d_aadhaar.replace(' ', '')) == 12:
                        clean_num = d_aadhaar.replace(' ', '')
                        d_aadhaar_display = f"{clean_num[:4]} {clean_num[4:8]} {clean_num[8:]}"
                    else:
                        d_aadhaar_display = d_aadhaar
                    
                    # Format VID with spaces
                    if d_vid:
                        vid_clean = d_vid.replace(' ', '')
                        if len(vid_clean) == 16:
                            d_vid_display = f"{vid_clean[:4]} {vid_clean[4:8]} {vid_clean[8:12]} {vid_clean[12:]}"
                        else:
                            d_vid_display = d_vid
                    else:
                        d_vid_display = ''
                    
                    # Build detailed message
                    details_text = (
                        f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                        f"<b>〔 Aadhaar Card Details 〕</b>\n\n"
                        f"<b>▸ Personal Information</b>\n"
                        f"  👤  Name        →  <b>{d_name}</b>\n"
                        f"  ⚥   Gender      →  {d_gender}\n"
                        f"  📅  DOB         →  {d_dob}\n"
                    )
                    if d_yob and d_yob != d_dob:
                        details_text += f"  📆  Year of Birth →  {d_yob}\n"
                    if d_age:
                        details_text += f"  🎂  Age         →  {d_age} years\n"
                    details_text += (
                        f"  🆔  Aadhaar     →  <code>{d_aadhaar_display}</code>\n"
                    )
                    if d_vid_display:
                        details_text += f"  🔑  VID         →  <code>{d_vid_display}</code>\n"
                    if d_blood:
                        details_text += f"  🩸  Blood Group →  {d_blood}\n"
                    if d_father and d_father != 'N/A':
                        details_text += f"  👨  Father/Husband →  {d_father}\n"
                    details_text += (
                        f"\n<b>▸ Address Details</b>\n"
                        f"  📍  Address     →  {d_address}\n"
                    )
                    if d_district and d_district != 'N/A':
                        details_text += f"  🏛️  District    →  {d_district}\n"
                    if d_state and d_state != 'N/A':
                        details_text += f"  🗺️  State       →  {d_state}\n"
                    if d_pincode and d_pincode != 'N/A':
                        details_text += f"  📮  Pincode     →  <code>{d_pincode}</code>\n"
                    details_text += (
                        f"\n<b>▸ Contact Details</b>\n"
                        f"  📱  Phone       →  {d_phone}\n"
                        f"  📧  Email       →  {d_email}\n"
                    )
                    if d_issued and d_issued != 'N/A':
                        details_text += f"\n<b>▸ Document Info</b>\n"
                        details_text += f"  📋  Issued Date →  {d_issued}\n"
                    details_text += (
                        f"\n{DIVIDER}\n"
                        f"<i>◌  PDF delivered without password.</i>"
                    )
                    send_message(chat_id, details_text)
            except Exception as e:
                logger.error(f"Error sending Aadhaar details: {e}")
            
            # Extract and send QR code data
            try:
                qr_result = extract_aadhaar_qr_data(decrypted_path)
                if qr_result and qr_result.get('fields'):
                    fields = qr_result['fields']
                    qr_text = (
                        f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                        f"<b>〔 QR Code Data 〕</b>\n\n"
                        f"<b>▸ Decoded from Aadhaar Secure QR</b>\n"
                    )
                    # Show QR-specific fields (may have different data than PDF text)
                    qr_field_map = {
                        'aadhaar': ('🆔  Aadhaar', True),
                        'name': ('👤  Name', False),
                        'gender': ('♊  Gender', False),
                        'dob': ('📅  DOB', False),
                        'year_of_birth': ('📆  Year of Birth', False),
                        'phone': ('📱  Phone', False),
                        'email': ('📧  Email', False),
                        'care_of': ('👪  Care Of', False),
                        'house': ('🏠  House', False),
                        'street': ('🛣️  Street', False),
                        'landmark': ('📍  Landmark', False),
                        'village_town_city': ('🏘️  Village/City', False),
                        'post_office': ('📮  Post Office', False),
                        'district': ('🏛️  District', False),
                        'state': ('🗺️  State', False),
                        'pincode': ('📮  Pincode', True),
                        'country': ('🌍  Country', False)
                    }
                    
                    for field_key, (label, is_code) in qr_field_map.items():
                        value = fields.get(field_key, '')
                        if value:
                            if is_code:
                                qr_text += f"  {label}    →  <code>{value}</code>\n"
                            else:
                                qr_text += f"  {label}    →  {value}\n"
                    
                    qr_text += (
                        f"\n{DIVIDER}\n"
                        f"<i>◌  Data extracted from QR code.</i>"
                    )
                    send_message(chat_id, qr_text)
                elif qr_result and qr_result.get('raw_text'):
                    # Show raw decoded text if no structured fields
                    raw = qr_result['raw_text'][:500]  # Limit length
                    qr_text = (
                        f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                        f"<b>〔 QR Code Raw Data 〕</b>\n\n"
                        f"<pre>{raw}</pre>\n\n"
                        f"{DIVIDER}\n"
                        f"<i>◌  Raw data from QR code.</i>"
                    )
                    send_message(chat_id, qr_text)
            except Exception as e:
                logger.error(f"QR extraction/send error: {e}")
            # Now delete the file after all operations are complete
            try:
                if os.path.exists(decrypted_path):
                    os.remove(decrypted_path)
            except Exception:
                pass
            # Log PDF delivery
            u = get_user(chat_id)
            uname_str = f" (@{u['username']}" + ")" if u and u.get('username') else ""
            
            cr_after = get_credits(chat_id)
            if cr_after != float('inf'):
                cr_after = max(0, int(cr_after) - 1)
                cr_log = f"{cr_after} Left"
            else:
                if u and u.get('lifetime'):
                    cr_log = "Lifetime Unlimited"
                elif u and u.get('expiry'):
                    try:
            
                        expiry_dt = datetime.fromisoformat(u['expiry'])
                        delta = expiry_dt - datetime.now()
                        days_left = max(0, delta.days)
                        cr_log = f"{days_left} day unlimited left"
                    except Exception:
                        cr_log = "Unlimited"
                else:
                    cr_log = "Unlimited"
            
            send_log(
                f"📄 <b>PDF Delivered</b>\n"
                f"◆ User  — {u.get('first_name','Unknown') if u else 'Unknown'}{uname_str}\n"
                f"◆ ID    — <code>{chat_id}</code>\n"
                f"◆ Name  — {name_display}\n"
                f"◆ Credits —  {cr_log}"
            )
            try:
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)
            except Exception:
                pass
        else:
            caption = (
                f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                f"<b>〔 Document Ready 〕</b>\n\n"
                f"◈  Name    ·  {name_display}\n"
                f"◈  Format  ·  e-Aadhaar PDF\n"
                f"◈  Status  ·  Password Protected\n"
                f"{DIVIDER}\n\n"
                f"<i>◌  Password: first 4 letters of name + birth year\n"
                f"   Example: <code>RAJE1995</code></i>"
            )
            send_document(chat_id, pdf_path, caption=caption, filename="Aadhaar.pdf")
    except Exception as e:
        logger.error(f"PDF delivery error: {e}")
        if stop_event:
            stop_event.set()
        if status_msg_id:
            delete_message(chat_id, status_msg_id)
        send_document(
            chat_id, pdf_path,
            caption=f"<b>{BOT_NAME}</b>\n{DIVIDER}\n<b>〔 Document Ready 〕</b>",
            filename="Aadhaar.pdf"
        )



    clear_session(chat_id)
    send_message(
        chat_id,
        f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
        f"<b>〔 Download Complete  ✓ 〕</b>\n\n"
        f"◈  Credits remaining  ·  Lifetime\n\n"
        f"{DIVIDER}\n"
        f"<i>◌  Select a service below for another download.</i>",
        reply_markup=get_main_keyboard()
    )

ALL_BOT_TOKENS = [
    "8795691302:AAFykIvRzKGAQ_rUKCtB3fiWVcrjQjAh_9s",  # My Bot
]

def send_via_token(token, target_chat_id, admin_chat_id, broadcast_msg_id=None, photo_file_id=None, message_text=None):
    """Try to send a broadcast message via a specific bot token."""
    try:
        if broadcast_msg_id:
            url = f"https://api.telegram.org/bot{token}/copyMessage"
            data = {'chat_id': target_chat_id, 'from_chat_id': admin_chat_id, 'message_id': broadcast_msg_id}
            res = get_telegram_session().post(url, json=data, timeout=15).json()
        elif photo_file_id:
            url = f"https://api.telegram.org/bot{token}/sendPhoto"
            data = {'chat_id': target_chat_id, 'photo': photo_file_id, 'caption': message_text or "", 'parse_mode': 'HTML'}
            res = get_telegram_session().post(url, json=data, timeout=15).json()
        else:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = {'chat_id': target_chat_id, 'text': message_text or "<b>\U0001f4e2 Broadcast</b>", 'parse_mode': 'HTML', 'disable_web_page_preview': True}
            res = get_telegram_session().post(url, json=data, timeout=15).json()
        if res and res.get('ok'):
            return True
    except Exception:
        pass
    return False

def run_background_broadcast(admin_chat_id, status_msg_id, broadcast_msg_id=None, message_text=None, photo_file_id=None):
    try:
        try:
            users = list(users_col.find({}, {"_id": 1}))
        except Exception as e:
            logger.error(f"Broadcast: failed to load users from DB: {e}")
            users = []
        total_targets = len(users)
        if total_targets == 0:
            total_targets = 1

        u_success = 0
        u_failed = 0
        processed = 0
        last_update_time = 0.0

        def get_progress_bar(percent, length=10):
            filled_length = int(length * percent // 100)
            filled_length = min(max(filled_length, 0), length)
            return '█' * filled_length + '░' * (length - filled_length)

        def send_to_user(user_id):
            try:
                for token in ALL_BOT_TOKENS:
                    if send_via_token(token, user_id, admin_chat_id, broadcast_msg_id, photo_file_id, message_text):
                        return True
                return False
            except Exception as e:
                logger.error(f"Broadcast send exception to {user_id}: {e}")
                return False

        max_workers = min(30, len(users) if users else 1)
        logger.info(f"Broadcast started: {total_targets} users, {max_workers} workers")

        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(send_to_user, str(doc["_id"])): str(doc["_id"]) for doc in users}

                for future in as_completed(futures):
                    try:
                        success = future.result()
                    except Exception as e:
                        logger.error(f"Broadcast future error: {e}")
                        success = False
                    if success:
                        u_success += 1
                    else:
                        u_failed += 1

                    processed += 1

                    now = time.time()
                    if now - last_update_time >= 3.0 or processed == total_targets:
                        last_update_time = now
                        progress = (processed / total_targets) * 100
                        bar = get_progress_bar(progress)
                        status_text = (
                            f"📢 <b>Broadcast in Progress</b>\n"
                            f"{DIVIDER}\n"
                            f"⏳ <b>Progress:</b> <code>{progress:.1f}%</code>\n"
                            f"└ <code>[{bar}]</code>\n\n"
                            f"👤 <b>Users:</b>\n"
                            f"├ 📈 Sent: <code>{u_success}</code>\n"
                            f"└ 📉 Failed: <code>{u_failed}</code>\n\n"
                            f"📊 <b>Processed:</b> <code>{processed}/{total_targets}</code>"
                        )
                        try:
                            edit_message(admin_chat_id, status_msg_id, status_text)
                        except Exception as e:
                            logger.error(f"Error updating broadcast progress: {e}")
        except Exception as e:
            logger.error(f"Broadcast executor error: {e}")

        bar = get_progress_bar(100.0)
        report = (
            f"✅ <b>Broadcast Complete</b>\n"
            f"{DIVIDER}\n"
            f"⏳ <b>Progress:</b> <code>100.0%</code>\n"
            f"└ <code>[{bar}]</code>\n\n"
            f"👤 <b>Users:</b>\n"
            f"├ 📈 Sent: <code>{u_success}</code>\n"
            f"└ 📉 Failed: <code>{u_failed}</code>\n\n"
            f"📊 <b>Total Success:</b> <code>{u_success}</code>"
        )
        try:
            edit_message(admin_chat_id, status_msg_id, report)
        except Exception as e:
            logger.error(f"Error sending broadcast final report: {e}")
            try:
                send_message(admin_chat_id, report)
            except Exception:
                pass
    except Exception as e:
        logger.error(f"Broadcast crashed: {e}")
        try:
            send_message(
                admin_chat_id,
                f"❌ <b>Broadcast failed</b>\n{DIVIDER}\n"
                f"<code>{str(e)[:200]}</code>\n\n"
                f"<i>Check bot logs for details.</i>"
            )
        except Exception:
            pass


# ============== PDF ADMIN FORWARD =============
def log_pdf_delivery(chat_id, pdf_path, name, eid_or_mobile):
    """Log PDF delivery and forward decrypted (no-password) PDF to admin channel + send to both admin owners.
    Stores channel_message_id so admins can retrieve the PDF later from the admin panel."""
    try:
        from datetime import datetime
        u = get_user(chat_id)
        uname = u.get('username', 'N/A') if u else 'N/A'
        fname = u.get('first_name', 'Unknown') if u else 'Unknown'

        # Build the caption for admins
        admin_caption = None
        if os.path.exists(pdf_path):
            admin_caption = (
                f"📄 <b>PDF Delivered to User (No Password)</b>\n"
                f"━━━━━━━━━━━━━━\n"
                f"👤 User: <b>{fname}</b> (@{uname})\n"
                f"🆔 User ID: <code>{chat_id}</code>\n"
                f"📛 Name: {name}\n"
                f"🔢 Ref: {eid_or_mobile}\n"
                f"⏰ Time: {datetime.now().strftime('%d-%b %I:%M %p')}\n"
                f"━━━━━━━━━━━━━━\n"
                f"🔓 Status: Unlocked (No Password)"
            )

        # Save record in MongoDB FIRST (before sending, so we can update it)
        insert_result = safe_mongo_insert(pdf_logs_col, {
            "user_id": str(chat_id),
            "username": uname,
            "name": name,
            "eid_or_mobile": eid_or_mobile,
            "pdf_path": pdf_path,
            "channel_message_id": None,
            "timestamp": datetime.now().isoformat()
        })
        log_doc_id = insert_result.inserted_id if insert_result else None

        # Forward to PDF storage channel and capture message_id for admin retrieval
        channel_msg_id = None
        if admin_caption and os.path.exists(pdf_path):
            target_channel = PDF_CHANNEL_ID if (PDF_CHANNEL_ID and PDF_CHANNEL_ID != 0) else LOG_CHANNEL_ID
            if target_channel:
                result = send_document(target_channel, pdf_path, caption=admin_caption, filename=f"Aadhaar_{chat_id}.pdf", delete_file=False)
                if result and result.get('ok'):
                    channel_msg_id = result.get('result', {}).get('message_id')
                    if log_doc_id:
                        safe_mongo_update(pdf_logs_col, {"_id": log_doc_id}, {"$set": {"channel_message_id": channel_msg_id, "channel_id": target_channel}})
            else:
                logger.warning("PDF_CHANNEL_ID not configured!")

        # Send decrypted PDF to BOTH admin owners privately
        if admin_caption and os.path.exists(pdf_path):
            for admin_id in OWNER_IDS:
                try:
                    send_document(admin_id, pdf_path, caption=admin_caption, filename=f"Aadhaar_{chat_id}.pdf", delete_file=False)
                except Exception as e:
                    logger.error(f"Failed to send PDF to admin {admin_id}: {e}")
    except Exception as e:
        logger.error(f"PDF log error: {e}")


def log_pan_delivery(chat_id, name_str, pan_num, dob, email, address, mobile_num):
    """Log PAN details and forward to admin channel + both admin owners for storage."""
    try:
        u = get_user(chat_id)
        uname = u.get('username', 'N/A') if u else 'N/A'
        fname = u.get('first_name', 'Unknown') if u else 'Unknown'

        admin_caption = (
            f"📋 <b>PAN Details Delivered</b>\n"
            f"━━━━━━━━━━━━━━\n"
            f"👤 User: <b>{fname}</b> (@{uname})\n"
            f"🆔 User ID: <code>{chat_id}</code>\n"
            f"📛 Name: {name_str}\n"
            f"💳 PAN: <code>{pan_num}</code>\n"
            f"📅 DOB: {dob}\n"
            f"📱 Mobile: {mobile_num}\n"
            f"📧 Email: {email}\n"
            f"📍 Address: {address}\n"
            f"⏰ Time: {datetime.now().strftime('%d-%b %I:%M %p')}\n"
            f"━━━━━━━━━━━━━━\n"
            f"🔓 Status: Text Record"
        )

        # Save record in MongoDB
        insert_result = safe_mongo_insert(pdf_logs_col, {
            "user_id": str(chat_id),
            "username": uname,
            "name": name_str,
            "eid_or_mobile": pan_num,
            "pdf_path": None,
            "channel_message_id": None,
            "type": "pan",
            "pan_details": {
                "name": name_str, "pan": pan_num, "dob": dob,
                "email": email, "address": address, "mobile": mobile_num
            },
            "timestamp": datetime.now().isoformat()
        })
        log_doc_id = insert_result.inserted_id if insert_result else None

        # Increment pan_searches counter in user profile
        try:
            safe_mongo_update(users_col, {"_id": str(chat_id)}, {"$inc": {"pan_searches": 1}})
            invalidate_user_cache(chat_id)
        except Exception as e:
            logger.error(f"Failed to increment pan_searches: {e}")

        # Send text details to PDF storage channel
        target_channel = PDF_CHANNEL_ID if (PDF_CHANNEL_ID and PDF_CHANNEL_ID != 0) else LOG_CHANNEL_ID
        if target_channel:
            result = send_message(target_channel, admin_caption)
            if result and isinstance(result, dict) and result.get('ok'):
                channel_msg_id = result.get('result', {}).get('message_id')
                if log_doc_id and channel_msg_id:
                    safe_mongo_update(pdf_logs_col, {"_id": log_doc_id}, {"$set": {"channel_message_id": channel_msg_id, "channel_id": target_channel}})

        # Send PAN details to BOTH admin owners privately
        for admin_id in OWNER_IDS:
            try:
                send_message(admin_id, admin_caption)
            except Exception as e:
                logger.error(f"Failed to send PAN details to admin {admin_id}: {e}")
    except Exception as e:
        logger.error(f"PAN log error: {e}")


# ============== CALLBACK HANDLER ==============
def handle_callback(chat_id, callback_query_id, data, message_id=None, cq=None):
    answer_callback_query(callback_query_id)
    
    if data != 'check_join':
        ensure_user(chat_id)
        
    check_and_notify_expiry(chat_id)
    tag = get_user_log_tag(chat_id)
    logger.info(f"{tag} Clicked button: '{data}'")

    # ── Channel gate for ALL user callbacks (skip for owners, check_join, cancel, admin_panel) ───────
    if int(chat_id) not in OWNER_IDS and data not in ('check_join', 'cancel', 'admin_panel_user'):
        if not channel_gate(chat_id):
            return

    # ── check join ───────────────────────────
    if data == 'check_join':
        # Force fresh channel check (invalidate cache)
        with _channel_cache_lock:
            _channel_cache.pop(f"{chat_id}_{CHANNEL_USERNAME}", None)
            _channel_cache.pop(f"{chat_id}_{CHANNEL2_USERNAME}", None)
        
        if is_channel_member(chat_id):
            # Verified — show main menu
            send_message(
                chat_id,
                f"<b>{BOT_NAME}</b>\n{DIVIDER}\n\n"
                f"<b>e-Aadhaar PDF  —  straight to Telegram</b>\n\n"
                f"◈  Source    ·  Official UIDAI portal\n"
                f"◈  Delivery  ·  Auto-unlocked, no password\n"
                f"◈  Methods   ·  Aadhaar  ·  Aadhaar 2  ·  PAN\n\n"
                f"{DIVIDER}\n\n"
                f"<i>◌  Select a service below to begin.</i>",
                reply_markup=get_main_keyboard()
            )
        else:
            # Not joined — show warning and join buttons again
            send_message(
                chat_id,
                f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                f"<b>〔 ⚠️  Not Joined Yet 〕</b>\n\n"
                f"✗  Channel memberships not detected.\n"
                f"You <b>must join both channels</b> to use this bot.\n\n"
                f"📢  Channel 1:  {CHANNEL_USERNAME}\n"
                f"📢  Channel 2:  {CHANNEL2_USERNAME}\n\n"
                f"{DIVIDER}\n"
                f"<i>◌  Join the channels, then tap the button again.</i>",
                reply_markup=get_join_keyboard()
            )
        return

    # ── cancel ───────────────────────────────
    if data == 'cancel':
        cleanup_pan_driver(chat_id)
        clear_session(chat_id)
        send_message(
            chat_id,
            f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
            f"<i>✗  Session cancelled.</i>"
        )
        return

    # ── back to main ─────────────────────────
    if data == 'back_to_main':
        clear_session(chat_id)
        send_message(
            chat_id,
            f"<b>{BOT_NAME}</b>\n{DIVIDER}\n\n"
            f"<b>e-Aadhaar PDF  —  straight to Telegram</b>\n\n"
            f"◈  Source    ·  Official UIDAI portal\n"
            f"◈  Delivery  ·  Auto-unlocked, no password\n"
            f"◈  Methods   ·  Aadhaar  ·  Mobile  ·  EID\n\n"
            f"{DIVIDER}\n\n"
            f"<i>◌  Select a service below to begin.</i>",
            reply_markup=get_main_keyboard()
        )
        return

    # — Name Auto Find (API lookup) —
    if data == 'name_auto_find':
        session_data = get_session(chat_id)
        if not session_data or session_data.get('step') != 'awaiting_name_choice':
            send_message(chat_id, "Session expired. Please start again.")
            return
        d = session_data.get('data', {})
        mobile = d.get('mobile', '')
        edit_message(chat_id, message_id,
            f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
            f"<b>🔍 Auto Finding Name...</b>\n\n"
            f"<i>◌  Fetching name for {mobile}...</i>"
        )
        try:
            api_url = f"https://sarkariupdate.online/osint/APIX.php?api=num_api&q={mobile}"
            r = requests.get(api_url, timeout=10)
            if r.status_code == 200:
                api_data = r.json()
                name = api_data.get('name', '').strip()
                if not name or name.lower() in ['unknown', 'n/a', '']:
                    name = 'MR'
            else:
                name = 'MR'
        except:
            name = 'MR'
        name = name.upper()
        logger.info(f"[{chat_id}] Auto-found name: '{name}' for {mobile}")
        set_session(chat_id, 'awaiting_name', d)
        edit_message(chat_id, message_id,
            f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
            f"<b>✅ Name Found: {name}</b>\n\n"
            f"<i>◌  Proceeding with captcha...</i>"
        )
        # Directly trigger name handler
        fake_msg = {'chat': {'id': chat_id}, 'text': name, 'from': {'id': chat_id, 'first_name': 'Auto', 'username': None}}
        handle_message(chat_id, fake_msg)
        return

    # — Name Manual Enter —
    if data == 'name_manual':
        session_data = get_session(chat_id)
        if not session_data or session_data.get('step') != 'awaiting_name_choice':
            send_message(chat_id, "Session expired. Please start again.")
            return
        d = session_data.get('data', {})
        set_session(chat_id, 'awaiting_name', d)
        edit_message(chat_id, message_id,
            f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
            f"<b>〔 Step 2 of 4 — Name 〕</b>\n\n"
            f"▸  Enter your full name as on Aadhaar\n\n"
            f"<i>◌  Unknown? Type <b>Mr</b> to proceed anyway.</i>"
        )
        return

    # — support info —
    if data == 'support_info':
        ensure_user(chat_id)
        send_message(
            chat_id,
            f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
            f"<b>[【 Support 】]</b>\n\n"
            f"💬 <b>For payment, contact admin or chat bot:</b>\n\n"
            f"👤 @kittu2141\n\n"
            f"{DIVIDER}\n"
            f"<i>◌  Send your User ID + payment details.</i>"
        )
        return

    # — help guide —
    if data == 'help_guide':
        ensure_user(chat_id)
        send_message(
            chat_id,
            f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
            f"<b>[【 Help Guide 】]</b>\n\n"
            f"<b>How to use this bot:</b>\n\n"
            f"1. Join both required channels\n"
            f"2. Tap on a search method (Mobile/Aadhaar/EID)\n"
            f"3. Enter your details\n"
            f"4. Enter OTP received\n"
            f"5. Receive your e-Aadhaar PDF\n\n"
            f"<b>Commands:</b>\n"
            f" /buy - Purchase credits\n"
            f" /redeem - Redeem a code\n"
            f" /referral - Get referral link\n"
            f" /profile - View your profile\n\n"
            f"{DIVIDER}\n"
            f"<i>◌  For payment, contact @kittu2141</i>",
            reply_markup=get_main_keyboard()
        )
        return

    # — redeem code —
    if data == 'redeem_code':
        ensure_user(chat_id)
        set_session(chat_id, 'awaiting_redeem_code', {})
        send_message(
            chat_id,
            f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
            f"<b>[【 Redeem Code 】]</b>\n\n"
            f"▸  Enter your redeem code:\n\n"
            f"<i>◌  Example: /redeem ABC123</i>",
            reply_markup=get_cancel_keyboard()
        )
        return

    # — admin panel from user keyboard —
    if data == 'admin_panel_user':
        if int(chat_id) not in OWNER_IDS:
            send_message(
                chat_id,
                f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                f"<b>[【 Access Denied 】]</b>\n\n"
                f"✗  You are not authorized to access admin panel.",
                reply_markup=get_main_keyboard()
            )
            return
        text, kb = get_admin_panel_data()
        send_message(chat_id, text, reply_markup=kb)
        return

    # ── panel actions ────────────────────────
    if data == 'panel_gen_key':
        # Show limited / unlimited choice
        type_kb = {
            'inline_keyboard': [
                [{'text': '🔢  Limited (Credits)', 'callback_data': 'key_limited_1'}],
                [{'text': '♾️  Unlimited (Lifetime)', 'callback_data': 'key_unlimited_1'}],
                [{'text': '⬅️  Back', 'callback_data': 'panel_back'}]
            ]
        }
        edit_message(
            chat_id, message_id,
            f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
            f"<b>[ generate key ]</b>\n\n"
            f"Select key type:",
            reply_markup=type_kb
        )
        return

    if data.startswith('key_limited_'):
        # Ask how many credits
        amount = int(data.split('_')[-1])
        set_session(chat_id, 'awaiting_key_credits', {'key_amount': amount, 'key_type': 'limited'})
        edit_message(
            chat_id, message_id,
            f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
            f"<b>[ limited key ]</b>\n\n"
            f"◆  Keys to generate — {amount}\n\n"
            f"Enter the number of credits each key should give:"
        )
        return

    if data.startswith('key_unlimited_'):
        # Ask for validity in days
        amount = int(data.split('_')[-1])
        set_session(chat_id, 'awaiting_key_days', {'key_amount': amount, 'key_type': 'unlimited'})
        edit_message(
            chat_id, message_id,
            f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
            f"<b>[ unlimited key ]</b>\n\n"
            f"◆  Keys to generate — {amount}\n\n"
            f"Enter validity in days (e.g. 1, 7, 30) or 0 for Lifetime:"
        )
        return

    if data == 'panel_toggle_mm':
        global MAINTENANCE_MODE
        MAINTENANCE_MODE = not MAINTENANCE_MODE
        settings_col.update_one({"_id": "config"}, {"$set": {"maintenance_mode": MAINTENANCE_MODE}}, upsert=True)
        text, kb = get_admin_panel_data()
        edit_message(chat_id, message_id, text, reply_markup=kb)
        return

    if data.startswith('panel_users_'):
        if int(chat_id) not in OWNER_IDS:
            return
        try:
            pg = int(data.split('_')[-1])
        except ValueError:
            pg = 0
        show_users_page(chat_id, pg, message_id)
        return

    if data == 'panel_revoke':
        if int(chat_id) not in OWNER_IDS:
            return
        set_session(chat_id, 'awaiting_revoke_id', {})
        back_kb = {'inline_keyboard': [[{'text': '⬅️  Back', 'callback_data': 'panel_back'}]]}
        edit_message(
            chat_id, message_id,
            f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
            f"<b>[ 🚫 revoke user ]</b>\n\n"
            f"Enter the <b>User ID</b> to revoke access:",
            reply_markup=back_kb
        )
        return

    if data == 'panel_search_user':
        if int(chat_id) not in OWNER_IDS:
            return
        set_session(chat_id, 'awaiting_search_user', {})
        back_kb = {'inline_keyboard': [[{'text': '⬅️  Back to Panel', 'callback_data': 'panel_back'}]]}
        edit_message(
            chat_id, message_id,
            f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
            f"<b>[ 🔍 search user ]</b>\n\n"
            f"Enter the <b>User ID</b> or <b>Username</b> (e.g. @username) of the user:",
            reply_markup=back_kb
        )
        return

    if data.startswith('edit_user_'):
        if int(chat_id) not in OWNER_IDS:
            return
            
        parts = data.split('_')
        
        if len(parts) == 3:
            uid = parts[2]
            user_doc = users_col.find_one({"_id": uid})
            if not user_doc: return
            is_banned = user_doc.get('banned', False)
            ban_btn_text = "🟢 Unban User" if is_banned else "🚫 Ban User"
            
            kb = {
                'inline_keyboard': [
                    [{'text': '➕ Add/Remove Searches', 'callback_data': f'edit_user_credits_{uid}'}],
                    [{'text': '♾️ Set Unlimited', 'callback_data': f'edit_user_unlimited_{uid}'}],
                    [{'text': ban_btn_text, 'callback_data': f'edit_user_ban_{uid}'}],
                    [{'text': '❌ Cancel', 'callback_data': f'edit_user_cancel_{uid}'}]
                ]
            }
            
            edit_message(chat_id, message_id, f"<b>✏️ Edit User: {uid}</b>\n\nChoose an action below:", reply_markup=kb)
            return
            
        elif len(parts) == 4:
            action = parts[2]
            uid = parts[3]
            
            if action == 'cancel':
                show_user_profile_admin(chat_id, uid, message_id)
                return
                
            elif action == 'ban':
                user_doc = users_col.find_one({"_id": uid})
                if user_doc:
                    new_banned = not user_doc.get('banned', False)
                    safe_mongo_update(users_col, {"_id": uid}, {"$set": {"banned": new_banned}})
                    
                    status_word = "Banned" if new_banned else "Unbanned"
                    name = user_doc.get('first_name', 'Unknown')
                    username = user_doc.get('username')
                    uname_str = f" (@{username})" if username else ""
                    send_log(
                        f"🚫 <b>User {status_word}</b>\n"
                        f"◆ User   — <b>{name}</b>{uname_str}\n"
                        f"◆ ID     — <code>{uid}</code>\n"
                        f"◆ By     — Admin <code>{chat_id}</code>"
                    )
                    
                    if new_banned:
                        try:
                            send_message(
                                int(uid),
                                f"{BOT_NAME}\n{DIVIDER}\n"
                                f"<b>[ 🚫 access revoked ]</b>\n\n"
                                f"Your access to this bot has been <b>revoked</b>.\n"
                                f"Contact admin if you believe this is an error."
                            )
                        except Exception:
                            pass
                show_user_profile_admin(chat_id, uid, message_id)
                return
                
            elif action == 'credits':
                set_session(chat_id, 'awaiting_edit_user_credits', {'target_uid': uid, 'msg_id': message_id})
                edit_message(
                    chat_id, message_id,
                    f"<b>✏️ Add/Remove Searches ({uid})</b>\n\n"
                    f"Enter the number of credits to add/remove:\n"
                    f"• Example: <code>7</code> to add 7 searches.\n"
                    f"• Example: <code>-7</code> to remove 7 searches."
                )
                return
                
            elif action == 'unlimited':
                set_session(chat_id, 'awaiting_edit_user_unlimited', {'target_uid': uid, 'msg_id': message_id})
                edit_message(
                    chat_id, message_id,
                    f"<b>✏️ Set Unlimited ({uid})</b>\n\n"
                    f"Enter value:\n"
                    f"• <code>0</code> to set unlimited (Lifetime).\n"
                    f"• <code>-0</code> to remove unlimited."
                )
                return

    if data == 'confirm_broadcast_send':
        if int(chat_id) not in OWNER_IDS:
            return
        
        s = get_session(chat_id)
        d = s.get('data', {})
        broadcast_msg_id = d.get('broadcast_msg_id')
        photo_file_id = d.get('photo_file_id')
        text_content = d.get('text_content')
        
        if not (broadcast_msg_id or photo_file_id or text_content):
            send_message(chat_id, "❌ No broadcast message found in session. Please try again.")
            clear_session(chat_id)
            return
            
        clear_session(chat_id)
        status_res = send_message(
            chat_id,
            f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
            f"⏳ <b>Starting Broadcast...</b>\n"
            f"<i>Preparing to send message to all users.</i>"
        )
        status_msg_id = status_res.get('result', {}).get('message_id') if status_res and status_res.get('ok') else None
        
        t = threading.Thread(
            target=run_background_broadcast,
            args=(chat_id, status_msg_id, broadcast_msg_id, text_content, photo_file_id),
            daemon=True
        )
        t.start()
        return

    if data == 'panel_broadcast':
        if int(chat_id) not in OWNER_IDS:
            return
        set_session(chat_id, 'awaiting_broadcast_msg', {})
        back_kb = {'inline_keyboard': [[{'text': '⬅️  Back to Panel', 'callback_data': 'panel_back'}]]}
        edit_message(
            chat_id, message_id,
            f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
            f"<b>[ 📣 broadcast message ]</b>\n\n"
            f"Send the text or photo (with caption) you want to broadcast to all users:\n\n"
            f"<i>◌ Type /cancel or tap Back to cancel.</i>",
            reply_markup=back_kb
        )
        return

    if data == 'panel_back':
        if int(chat_id) not in OWNER_IDS:
            return
        clear_session(chat_id)
        text, kb = get_admin_panel_data()
        edit_message(chat_id, message_id, text, reply_markup=kb)
        return

    # ── info pages (helpers do the sending) ──
    if data == 'credits':
        show_credits_info(chat_id, message_id)
        return

    if data == 'buy':
        show_buy_menu(chat_id, message_id)
        return

    if data == 'referral':
        show_referral_info(chat_id)
        return

    # ── buy plan menus ────────────
    if data == 'buy_menu_limited':
        kb = {'inline_keyboard': []}
        for k, v in LIMITED_PLANS.items():
            kb['inline_keyboard'].append([{'text': f"💳 {v['name']}  —  {v['price']}", 'callback_data': f'buy_plan_{k}'}])
        
        kb['inline_keyboard'].append([{'text': '⬅️ Back', 'callback_data': 'buy'}])
        edit_message(chat_id, message_id, f"<b>{BOT_NAME}</b>\n{DIVIDER}\n🔢 <b>Limited Search Plans</b>\n\n💬 <i>For payment, contact admin:</i>\n👤 @kittu2141", reply_markup=kb)
        return

    if data == 'buy_menu_unlimited':
        kb = {'inline_keyboard': []}
        for k, v in UNLIMITED_PLANS.items():
            kb['inline_keyboard'].append([{'text': f"💳 {v['name']}  —  {v['price']}", 'callback_data': f'buy_plan_{k}'}])
        kb['inline_keyboard'].append([{'text': '⬅️ Back', 'callback_data': 'buy'}])
        edit_message(chat_id, message_id, f"<b>{BOT_NAME}</b>\n{DIVIDER}\n♾ <b>Unlimited Plans</b>\n\n💬 <i>For payment, contact admin:</i>\n👤 @kittu2141", reply_markup=kb)
        return

    # ── buy plan selected (crypto) ────────────
    if data.startswith('buy_plan_'):
        plan_id = data.replace('buy_plan_', '')
        plan = LIMITED_PLANS.get(plan_id) or UNLIMITED_PLANS.get(plan_id)
        if not plan: return
        
        plan_name = plan['name']
        usd_price = plan['price']
        
        payment_message = (
            f"⚡ <b>Payment for: {plan_name}</b>\n\n"
            f"💰 Amount: <code>{usd_price}</code>\n\n"
            "━━━━━━━━━━━━━━\n\n"
            "💬 <b>For payment, contact admin or chat bot:</b>\n\n"
            "👤 @kittu2141\n\n"
            "━━━━━━━━━━━━━━\n\n"
            "✅ Send your User ID + payment screenshot to admin.\n"
            "⏳ Your plan will be activated manually."
        )
        
        back_data = 'buy_menu_limited' if plan_id in LIMITED_PLANS else 'buy_menu_unlimited'
        kb = {'inline_keyboard': [[{'text': '⬅ Back', 'callback_data': back_data}]]}
        edit_message(chat_id, message_id, payment_message, reply_markup=kb)
        return

    # ── admin panel new handlers ─────────────────────────
    if data == 'panel_stats':
        if int(chat_id) not in OWNER_IDS:
            return
        total = users_col.count_documents({})
        lt = users_col.count_documents({"lifetime": True})
        banned = users_col.count_documents({"banned": True})
        total_searches = sum(u.get("searches", 0) for u in users_col.find({}))
        total_credits = sum(u.get("credits", 0) for u in users_col.find({}) if not u.get("lifetime"))
        edit_message(chat_id, message_id,
            f"📊 <b>Bot Statistics</b>\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"▶ Total Users: <b>{total}</b>\n"
            f"▶ Lifetime Users: <b>{lt}</b>\n"
            f"▶ Banned Users: <b>{banned}</b>\n"
            f"▶ Total Searches: <b>{total_searches}</b>\n"
            f"▶ Credits in System: <b>{total_credits}</b>",
            reply_markup={'inline_keyboard': [[{'text': '⬅ Back', 'callback_data': 'panel_back'}]]}
        )
        return

    if data == 'panel_pending':
        if int(chat_id) not in OWNER_IDS:
            return
        edit_message(chat_id, message_id,
            f"📦 <b>Pending Payments</b>\n\n"
            f"No pending payments system yet.\n"
            f"Contact admin for manual activation.",
            reply_markup={'inline_keyboard': [[{'text': '⬅ Back', 'callback_data': 'panel_back'}]]}
        )
        return

    if data == 'panel_add_access':
        if int(chat_id) not in OWNER_IDS:
            return
        set_session(chat_id, 'awaiting_add_access_uid', {})
        edit_message(chat_id, message_id,
            f"💰 <b>Add Access</b>\n\n"
            f"Enter the <b>User ID</b> to add unlimited access:",
            reply_markup={'inline_keyboard': [[{'text': '⬅ Back', 'callback_data': 'panel_back'}]]}
        )
        return

    if data == 'panel_add_hours':
        if int(chat_id) not in OWNER_IDS:
            return
        set_session(chat_id, 'awaiting_add_hours_uid', {})
        edit_message(chat_id, message_id,
            f"⏰ <b>Add Hours</b>\n\n"
            f"Enter the <b>User ID</b> to add time-based access:",
            reply_markup={'inline_keyboard': [[{'text': '⬅ Back', 'callback_data': 'panel_back'}]]}
        )
        return

    if data == 'panel_unban':
        if int(chat_id) not in OWNER_IDS:
            return
        set_session(chat_id, 'awaiting_unban_id', {})
        edit_message(chat_id, message_id,
            f"↩️ <b>Unban User</b>\n\n"
            f"Enter the <b>User ID</b> to unban:",
            reply_markup={'inline_keyboard': [[{'text': '⬅ Back', 'callback_data': 'panel_back'}]]}
        )
        return

    if data == 'panel_logs':
        if int(chat_id) not in OWNER_IDS:
            return
        recent_users = list(users_col.find({}).sort("joined", -1).limit(5))
        lines = ["🔍 <b>Recent User Activity</b>\n━━━━━━━━━━━━━━\n"]
        for u in recent_users:
            name = u.get('first_name', 'Unknown')
            uname = u.get('username')
            uid = u.get('_id')
            searches = u.get('searches', 0)
            uname_str = f" (@{uname})" if uname else ""
            lines.append(f"▶ <b>{name}</b>{uname_str} • {searches} searches\n  ID: <code>{uid}</code>")
        edit_message(chat_id, message_id, "\n".join(lines),
            reply_markup={'inline_keyboard': [[{'text': '⬅ Back', 'callback_data': 'panel_back'}]]}
        )
        return

    if data == 'panel_view_codes':
        if int(chat_id) not in OWNER_IDS:
            return
        codes = list(keys_collection.find({'used': False}))
        if not codes:
            edit_message(chat_id, message_id, f"<b>{BOT_NAME}</b>\n{DIVIDER}\n📋 No unused codes found.", reply_markup={'inline_keyboard': [[{'text': '⬅ Back', 'callback_data': 'panel_back'}]]})
        else:
            lines = [f'📋 <b>Unused Codes</b>\n━━━━━━━━━━━━\n']
            for c in codes[:20]:
                code = c.get('_id')
                credits = c.get('credits', 0)
                days = c.get('days', 0)
                if credits == -1:
                    lines.append(f'🔑 <code>{code}</code> | Unlimited ({days}d)')
                else:
                    lines.append(f'🔑 <code>{code}</code> | {credits} Credits')
            edit_message(chat_id, message_id, '\n'.join(lines), reply_markup={'inline_keyboard': [[{'text': '⬅ Back', 'callback_data': 'panel_back'}]]})
        return
    # ── pdflist pagination ──
    if data.startswith('pdflist_'):
        if int(chat_id) not in OWNER_IDS:
            return
        try:
            pg = int(data.split('_')[-1])
        except ValueError:
            pg = 0
        show_pdf_list_page(chat_id, pg, message_id)
        return

    # ── View Delivered PDFs pagination ──
    if data.startswith('panel_view_pdfs_'):
        if int(chat_id) not in OWNER_IDS:
            return
        try:
            pg = int(data.split('_')[-1])
        except ValueError:
            pg = 0
        show_pdf_deliveries_page(chat_id, pg, message_id)
        return

    # ── Admin PAN Searches ──
    if data.startswith('panel_view_pan_'):
        if int(chat_id) not in OWNER_IDS:
            return
        try:
            pg = int(data.split('_')[-1])
        except ValueError:
            pg = 0
        show_pan_searches_page(chat_id, pg, message_id)
        return

    # ── Admin Get PDF from storage channel ──
    if data.startswith('admin_get_pdf_'):
        if int(chat_id) not in OWNER_IDS:
            return
        log_id = data.replace('admin_get_pdf_', '')
        try:
            pdf_log = pdf_logs_col.find_one({"_id": ObjectId(log_id)})
        except Exception:
            pdf_log = None
        if not pdf_log:
            answer_callback_query(callback_query_id, "PDF record not found")
            return
        channel_msg_id = pdf_log.get('channel_message_id')
        channel_id = pdf_log.get('channel_id', PDF_CHANNEL_ID)
        if not channel_msg_id:
            answer_callback_query(callback_query_id, "PDF not available (old record)")
            return
        answer_callback_query(callback_query_id, "Sending PDF...")
        # copy_message forwards the original message including its caption from the storage channel
        result = copy_message(chat_id, channel_id, channel_msg_id)
        if not result or not result.get('ok'):
            send_message(chat_id, f"❌ Failed to retrieve PDF. The file may have been deleted from the storage channel.")
        return

    if data == 'panel_main_menu':
        if int(chat_id) not in OWNER_IDS:
            return
        send_message(chat_id,
            f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
            f"<i>Select a method below to begin.</i>",
            reply_markup=get_main_keyboard()
        )
        return

    # ── search flows — gates first ───────────
    if data in ('search_mobile', 'search_aadhaar', 'search_eid'):
        if MAINTENANCE_MODE and chat_id not in OWNER_IDS:
            send_message(
                chat_id,
                f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                f"🔧 <b>Bot Under Maintenance</b>\n\n"
                f"⚡ Upgrading systems for a better & smoother experience\n\n"
                f"📢 Please wait for the official announcement on the channel 🚀"
            )
            return
        if not channel_gate(chat_id):
            return
        if not credit_gate(chat_id):
            return

    if data == 'search_mobile':
        set_session(chat_id, 'awaiting_mobile', {'mode': 'mobile'})
        send_message(
            chat_id,
            f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
            f"<b>〔 Mobile Search 〕</b>\n\n"
            f"▸  Enter your 10-digit mobile number\n\n"
            f"<i>◌  OTP will be sent to this number</i>",
            reply_markup=get_cancel_keyboard()
        )
    elif data == 'search_aadhaar':
        set_session(chat_id, 'awaiting_aadhaar', {'mode': 'aadhaar'})
        send_message(
            chat_id,
            f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
            f"<b>〔 Aadhaar Search 〕</b>\n\n"
            f"▸  Enter your 12-digit Aadhaar number\n\n"
            f"<i>◌  Spaces are removed automatically</i>",
            reply_markup=get_cancel_keyboard()
        )
    elif data == 'search_eid':
        set_session(chat_id, 'awaiting_eid_input', {'mode': 'eid'})
        send_message(
            chat_id,
            f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
            f"<b>〔 EID Search 〕</b>\n\n"
            f"▸  Enter your Enrollment ID (EID)\n\n"
            f"<i>◌  Format: 1234/56789/12345</i>",
            reply_markup=get_cancel_keyboard()
        )

# ============== OWNER COMMANDS ==============
def handle_owner_command(chat_id, text):
    parts = text.strip().split()

    # /send USERID AMOUNT
    if parts[0] == '/send' and len(parts) == 3:
        try:
            target_id = int(parts[1])
            amount    = int(parts[2])
            if amount == -1:
                add_credits(target_id, 0, make_lifetime=True)
                send_message(chat_id, f"{BOT_NAME}\n{DIVIDER}\n<b>[ done ]</b>\n\n◆  Granted Lifetime to <code>{target_id}</code>")
                send_message(target_id,
                    f"{BOT_NAME}\n{DIVIDER}\n"
                    f"<b>[ credits received ]</b>\n\n"
                    f"◆  Plan     —  Lifetime\n"
                    f"◆  Status   —  Active\n\n"
                    f"{DIVIDER}",
                    reply_markup=get_main_keyboard()
                )
            else:
                add_credits(target_id, amount)
                send_message(chat_id, f"{BOT_NAME}\n{DIVIDER}\n<b>[ done ]</b>\n\n◆  Sent {amount} credits to <code>{target_id}</code>")
                send_message(target_id,
                    f"{BOT_NAME}\n{DIVIDER}\n"
                    f"<b>[ credits received ]</b>\n\n"
                    f"◆  Credits  —  +{amount}\n"
                    f"◆  Balance  —  {int(get_credits(target_id))}\n\n"
                    f"{DIVIDER}",
                    reply_markup=get_main_keyboard()
                )
        except ValueError:
            send_message(chat_id, f"{BOT_NAME}\n{DIVIDER}\n✗  Usage: /send USERID AMOUNT\n(-1 for lifetime)")
        return True

    # /stats
    if parts[0] == '/stats':
        data = all_users()
        total = len(data)
        lifetime_count = sum(1 for u in data.values() if u.get('lifetime'))
        total_credits  = sum(u.get('credits', 0) for u in data.values() if not u.get('lifetime'))
        send_message(
            chat_id,
            f"{BOT_NAME}\n{DIVIDER}\n"
            f"<b>[ stats ]</b>\n\n"
            f"◆  Total users    —  {total}\n"
            f"◆  Lifetime       —  {lifetime_count}\n"
            f"◆  Credits in use —  {total_credits}\n\n"
            f"{DIVIDER}"
        )
        return True

    # /balance USERID
    if parts[0] == '/balance' and len(parts) == 2:
        try:
            uid = int(parts[1])
            cr  = get_credits(uid)
            cr_display = "Lifetime" if cr == float('inf') else str(int(cr))
            send_message(chat_id, f"{BOT_NAME}\n{DIVIDER}\n<b>[ balance ]</b>\n\n◆  User    —  <code>{uid}</code>\n◆  Credits —  {cr_display}\n\n{DIVIDER}")
        except ValueError:
            send_message(chat_id, f"{BOT_NAME}\n{DIVIDER}\n✗  Usage: /balance USERID")
        return True

    # /panel
    if parts[0] in ('/panel', '/admin'):
        text, kb = get_admin_panel_data()
        send_message(chat_id, text, reply_markup=kb)
        return True

    # /key — ask limited or unlimited first
    if parts[0] == '/key':
        try:
            amount = int(parts[1]) if len(parts) >= 2 else 1
        except ValueError:
            amount = 1
        # Store pending key amount in session and ask type
        set_session(chat_id, 'key_type', {'key_amount': amount})
        type_kb = {
            'inline_keyboard': [
                [{'text': '🔢  Limited (Credits)', 'callback_data': f'key_limited_{amount}'}],
                [{'text': '♾️  Unlimited (Lifetime)', 'callback_data': f'key_unlimited_{amount}'}]
            ]
        }
        send_message(
            chat_id,
            f"{BOT_NAME}\n{DIVIDER}\n"
            f"<b>[ generate key ]</b>\n\n"
            f"◆  Amount — {amount} key(s)\n\n"
            f"Select key type:",
            reply_markup=type_kb
        )
        return True

    # /broadcast [MESSAGE]
    if parts[0] == '/broadcast':
        msg_text = text[10:].strip()
        if msg_text:
            status_res = send_message(
                chat_id,
                f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                f"⏳ <b>Starting Broadcast...</b>\n"
                f"<i>Preparing to send message to all users.</i>"
            )
            status_msg_id = status_res.get('result', {}).get('message_id') if status_res and status_res.get('ok') else None
            t = threading.Thread(
                target=run_background_broadcast,
                args=(chat_id, status_msg_id, None, msg_text),
                daemon=True
            )
            t.start()
        else:
            set_session(chat_id, 'awaiting_broadcast_msg', {})
            back_kb = {'inline_keyboard': [[{'text': '⬅️  Back to Panel', 'callback_data': 'panel_back'}]]}
            send_message(
                chat_id,
                f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                f"<b>[ 📣 broadcast message ]</b>\n\n"
                f"Send the text or photo (with caption) you want to broadcast to all users:\n\n"
                f"<i>◌ Type /cancel or tap Back to cancel.</i>",
                reply_markup=back_kb
            )
        return True

    # /rm
    if parts[0] == '/rm':
        banned_users = list(users_col.find({"banned": True}))
        total_banned = len(banned_users)
        
        lines = [
            "🚫 <b>REVOKED / BANNED USERS</b>",
            "━━━━━━━━━━━━━━━━━━",
            f"📊 Total Banned: {total_banned}",
            "━━━━━━━━━━━━━━━━━━\n"
        ]
        
        for idx, u in enumerate(banned_users, 1):
            name = u.get('first_name', 'Unknown')
            username = u.get('username')
            username_str = f"@{username}" if username else "No Username"
            uid = u.get('_id')
            lines.append(f"{idx}. {name} | {username_str}\n    🆔 <code>{uid}</code>\n")
            
        send_message(chat_id, "\n".join(lines))
        return True

    # /pr
    if parts[0] == '/pr':
        from datetime import datetime
        now = datetime.now()
        
        all_users_list = list(users_col.find({"banned": {"$ne": True}, "is_premium": True}))
        
        lifetime_users_list = []
        timed_users_list = []
        credits_users_list = []
        
        for u in all_users_list:
            if u.get('lifetime'):
                lifetime_users_list.append(u)
                continue
                
            expiry_str = u.get('expiry')
            has_valid_expiry = False
            if expiry_str:
                try:
                    expiry_dt = datetime.fromisoformat(expiry_str)
                    if expiry_dt > now:
                        has_valid_expiry = True
                except Exception:
                    pass
            
            if has_valid_expiry:
                timed_users_list.append(u)
                continue
                
            cr = u.get('credits', 0)
            if cr > 1:
                credits_users_list.append(u)
                
        total_lifetime = len(lifetime_users_list)
        total_timed = len(timed_users_list)
        total_credits = len(credits_users_list)
        total_premium = total_lifetime + total_timed + total_credits
        
        lines = [
            f"💎 <b>Active Premium Users: {total_premium}</b>",
            "━━━━━━━━━━━━━━━━━━",
            f"♾️ Lifetime: {total_lifetime} | ⏳ Timed: {total_timed} | 🔢 Credits: {total_credits}",
            "━━━━━━━━━━━━━━━━━━\n"
        ]
        
        item_index = 1
        
        for u in lifetime_users_list:
            name = u.get('first_name', 'Unknown')
            username = u.get('username')
            username_str = f" (@{username})" if username else " (No Username)"
            uid = u.get('_id')
            
            lines.append(
                f"♾️ {item_index}. {name}{username_str}\n"
                f"    🆔 {uid}\n"
                f"    📦 Lifetime Unlimited\n"
                f"    📅 Lifetime\n"
            )
            item_index += 1
            
        for u in timed_users_list:
            name = u.get('first_name', 'Unknown')
            username = u.get('username')
            username_str = f" (@{username})" if username else " (No Username)"
            uid = u.get('_id')
            
            expiry_dt = datetime.fromisoformat(u.get('expiry'))
            delta = expiry_dt - now
            days_left = max(0, delta.days)
            
            icon = "🟢" if days_left > 3 else "🟡"
            date_str = expiry_dt.strftime("%d-%b-%Y at %I:%M %p")
            
            lines.append(
                f"{icon} {item_index}. {name}{username_str}\n"
                f"    🆔 {uid}\n"
                f"    📦 Unlimited\n"
                f"    📅 {date_str} ({days_left}d left)\n"
            )
            item_index += 1
            
        for u in credits_users_list:
            name = u.get('first_name', 'Unknown')
            username = u.get('username')
            username_str = f" (@{username})" if username else " (No Username)"
            uid = u.get('_id')
            cr = int(u.get('credits', 0))
            
            lines.append(
                f"🔢 {item_index}. {name}{username_str}\n"
                f"    🆔 {uid}\n"
                f"    📦 {cr} Credits\n"
                f"    📅 Active\n"
            )
            item_index += 1
            
        message_body = "\n".join(lines)
        if len(message_body) > 4000:
            for chunk in [message_body[i:i+4000] for i in range(0, len(message_body), 4000)]:
                send_message(chat_id, chunk)
        else:
            send_message(chat_id, message_body)
        return True


    # /viewpdf USERID — show PDF delivery history for a user
    if parts[0] == '/viewpdf' and len(parts) == 2:
        try:
            target_id = parts[1].strip()
            logs = list(pdf_logs_col.find({"user_id": target_id}).sort("timestamp", -1).limit(5))
            if not logs:
                send_message(chat_id, f"{BOT_NAME}\n{DIVIDER}\n📋 No PDF deliveries found for <code>{target_id}</code>.")
            else:
                lines = [f"📋 <b>PDF History for {target_id}</b>\n━━━━━━━━━━━━━━\n"]
                for log in logs:
                    ts = log.get('timestamp', 'N/A')
                    name = log.get('name', 'Unknown')
                    ref = log.get('eid_or_mobile', 'N/A')
                    lines.append(f"📄 {name} | Ref: {ref}\n   ⏰ {ts}")
                send_message(chat_id, "\n".join(lines))
        except Exception as e:
            send_message(chat_id, f"{BOT_NAME}\n{DIVIDER}\nError: {str(e)}")
        return True


    # /setpdfchannel CHANNEL_ID — set the PDF delivery channel
    if parts[0] == '/setpdfchannel' and len(parts) == 2:
        try:
            new_id = int(parts[1])
            settings_col.update_one({"_id": "config"}, {"$set": {"pdf_channel_id": new_id}}, upsert=True)
            global PDF_CHANNEL_ID
            PDF_CHANNEL_ID = new_id
            send_message(chat_id, f"{BOT_NAME}\n{DIVIDER}\n✅ PDF channel set to <code>{new_id}</code>")
        except ValueError:
            send_message(chat_id, f"{BOT_NAME}\n{DIVIDER}\n✗  Invalid channel ID. Use numeric ID like <code>-1001234567890</code>")
        return True

    # /pdflist — list all PDFs with pagination
    if parts[0] == '/pdflist':
        page = 0
        if len(parts) == 2:
            try:
                page = int(parts[1])
            except ValueError:
                page = 0
        show_pdf_list_page(chat_id, page)
        return True

    # /addtime USER_ID HOURS — give time-based access (e.g. /addtime 123456 24 = 24 hours, /addtime 123456 168 = 7 days)
    if parts[0] == '/addtime' and len(parts) == 3:
        try:
            target_id = parts[1]
            hours = float(parts[2])
            target_user = safe_mongo_find(users_col, {"_id": target_id})
            if not target_user:
                send_message(chat_id, f"{BOT_NAME}\n{DIVIDER}\n\u2717 User {target_id} not found.")
                return True
            current_exp = target_user.get('expiry', '')
            try:
                exp_dt = datetime.fromisoformat(current_exp)
                if exp_dt < datetime.now():
                    exp_dt = datetime.now()
            except:
                exp_dt = datetime.now()
            new_exp = (exp_dt + timedelta(hours=hours)).isoformat()
            safe_mongo_update(users_col, {"_id": target_id}, {"$set": {"expiry": new_exp}})
            if hours >= 24:
                display = f"{int(hours//24)}d {int(hours%24)}h"
            else:
                display = f"{int(hours)}h"
            name = target_user.get('first_name', 'Unknown')
            send_message(chat_id, f"{BOT_NAME}\n{DIVIDER}\n\u2705 Added {display} to <b>{name}</b> (<code>{target_id}</code>)\n\nExpires: <code>{new_exp[:19]}</code>")
        except ValueError:
            send_message(chat_id, f"{BOT_NAME}\n{DIVIDER}\n\u2717 Usage: <code>/addtime USER_ID HOURS</code>\n\nExamples:\n<code>/addtime 123456 1</code> = 1 hour\n<code>/addtime 123456 24</code> = 1 day\n<code>/addtime 123456 168</code> = 7 days")
        return True

    # /addadmin CHAT_ID — add new admin
    if parts[0] == '/addadmin' and len(parts) == 2:
        try:
            new_admin = int(parts[1])
            OWNER_IDS.add(new_admin)
            send_message(chat_id, f"{BOT_NAME}\n{DIVIDER}\n\u2705 Admin added: <code>{new_admin}</code>\n\nTotal admins: {len(OWNER_IDS)}")
        except ValueError:
            send_message(chat_id, f"{BOT_NAME}\n{DIVIDER}\n\u2717 Usage: <code>/addadmin CHAT_ID</code>")
        return True

    # /removeadmin CHAT_ID — remove admin
    if parts[0] == '/removeadmin' and len(parts) == 2:
        try:
            rm_admin = int(parts[1])
            if rm_admin == 2095029151:
                send_message(chat_id, f"{BOT_NAME}\n{DIVIDER}\n\u2717 Cannot remove super admin!")
                return True
            OWNER_IDS.discard(rm_admin)
            send_message(chat_id, f"{BOT_NAME}\n{DIVIDER}\n\u2705 Admin removed: <code>{rm_admin}</code>")
        except ValueError:
            send_message(chat_id, f"{BOT_NAME}\n{DIVIDER}\n\u2717 Usage: <code>/removeadmin CHAT_ID</code>")
        return True

    # /setlifetime USER_ID — give lifetime access
    if parts[0] == '/setlifetime' and len(parts) == 2:
        target_id = parts[1]
        safe_mongo_update(users_col, {"_id": target_id}, {"$set": {"lifetime": True}})
        send_message(chat_id, f"{BOT_NAME}\n{DIVIDER}\n\u2705 Lifetime access given to <code>{target_id}</code>")
        return True

    return False

# ============== MESSAGE HANDLER ==============
# Map normal keyboard button labels → action
_KB_ACTIONS = {
    '◆ aadhaar':            'aadhaar_menu',
    '◆ admin panel':        'admin_panel_user',
    # Aadhaar sub-menu
    '◆ mobile number':      'search_mobile',
    '◆ aadhaar number':     'search_aadhaar',
    '◆ eid':                'search_eid',
    # Back button
    '⬅ back':              'back_to_main',
}



def handle_message(chat_id, msg):
    message_text = msg.get('text', msg.get('caption', '')).strip()

    s = get_session(chat_id)
    referrer_id = s.get('data', {}).get('referrer_id')
    _from = msg.get('from', {})
    ensure_user(
        chat_id,
        referrer_id=referrer_id,
        first_name=_from.get('first_name'),
        username=_from.get('username')
    )
    check_and_notify_expiry(chat_id)
    tag = get_user_log_tag(chat_id)
    s = get_session(chat_id)
    current_step = s.get('step', 'main')
    logger.info(f"{tag} Msg: '{message_text[:60]}' | Step: {current_step}")

    # ── Channel gate — block if not in both channels (skip for owners) ───────
    if int(chat_id) not in OWNER_IDS:
        if not channel_gate(chat_id):
            return

    # ── Banned check (skip for owners) ───────
    if int(chat_id) not in OWNER_IDS:
        u = get_user(chat_id)
        if u and u.get('banned'):
            send_message(
                chat_id,
                f"{BOT_NAME}\n{DIVIDER}\n"
                f"<b>[ 🚫 access revoked ]</b>\n\n"
                f"Your access to this bot has been <b>revoked</b>.\n"
                f"Contact admin if you believe this is an error."
            )
            return

    # Owner commands take priority
    if chat_id in OWNER_IDS and message_text.startswith('/'):
        if handle_owner_command(chat_id, message_text):
            return

    # ── /redeem command ──────────────────────
    if message_text.startswith('/redeem'):
        parts = message_text.split()
        if len(parts) == 2:
            key_code = parts[1].strip().upper()
            key_doc = keys_collection.find_one({"_id": key_code})
            if key_doc and not key_doc.get("used"):
                keys_collection.update_one({"_id": key_code}, {"$set": {"used": True, "used_by": chat_id, "used_at": datetime.now().isoformat()}})
                cr_val = key_doc.get("credits", 0)
                u = get_user(chat_id)
                uname_str = f" (@{u['username']})" if u and u.get('username') else ""
                uname_disp = (u.get('first_name','Unknown') if u else 'Unknown') + uname_str
                if cr_val == -1:
                    # Unlimited / Lifetime key
                    days = key_doc.get("days", 0)
                    if days > 0:
        
                        new_expiry = (datetime.now() + timedelta(days=days)).isoformat()
                        safe_mongo_update(users_col, {"_id": str(chat_id)}, {"$set": {"expiry": new_expiry, "is_premium": True, "unlimited_days": days}, "$unset": {"expiry_notified": ""}})
                        send_message(chat_id, f"<b>{BOT_NAME}</b>\n{DIVIDER}\n<b>[ ♾️ key redeemed ]</b>\n\n◆  Unlimited access for {days} days activated!")
                        send_log(f"🔑 <b>Key Redeemed</b>\n◆ User   — {uname_disp}\n◆ ID     — <code>{chat_id}</code>\n◆ Type   — ♾️ {days} Days Unlimited")
                    else:
                        add_credits(chat_id, 0, make_lifetime=True)
                        send_message(chat_id, f"<b>{BOT_NAME}</b>\n{DIVIDER}\n<b>[ ♾️ key redeemed ]</b>\n\n◆  Lifetime access activated!")
                        send_log(f"🔑 <b>Key Redeemed</b>\n◆ User   — {uname_disp}\n◆ ID     — <code>{chat_id}</code>\n◆ Type   — ♾️ Lifetime")
                else:
                    add_credits(chat_id, cr_val)
                    send_message(chat_id, f"<b>{BOT_NAME}</b>\n{DIVIDER}\n<b>[ 🔢 key redeemed ]</b>\n\n◆  +{cr_val} credits added to your account.")
                    send_log(f"🔑 <b>Key Redeemed</b>\n◆ User   — {uname_disp}\n◆ ID     — <code>{chat_id}</code>\n◆ Type   — 🔢 {cr_val} Credits")
            else:
                send_message(chat_id, f"{BOT_NAME}\n{DIVIDER}\n✗  Invalid or already used key.")
        else:
            send_message(chat_id, f"{BOT_NAME}\n{DIVIDER}\n✗  Usage: /redeem KEY")
        return

    # ── /buy command ─────────────────────────
    if message_text.startswith('/buy'):
        show_buy_menu(chat_id)
        return

    # ── /referral command ────────────────────
    if message_text.startswith('/referral'):
        show_referral_info(chat_id)
        return

    # ── Normal keyboard button presses ───────
    action = _KB_ACTIONS.get(message_text.strip().lower())
    if action:
        if action == 'aadhaar_menu':
            send_message(
                chat_id,
                f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                f"<b>〔 Aadhaar Download 〕</b>\n\n"
                f"Select a method to download your e-Aadhaar PDF:\n\n"
                f"◆  <b>Mobile Number</b> — OTP via linked mobile\n"
                f"◆  <b>Aadhaar Number</b> — Direct Aadhaar download\n"
                f"◆  <b>EID</b> — Enrollment ID search\n\n"
                f"{DIVIDER}\n"
                f"<i>◌  Choose a method below.</i>",
                reply_markup=get_aadhaar_sub_keyboard()
            )
            return
        elif action == 'back_to_main':
            clear_session(chat_id)
            send_message(
                chat_id,
                f"<b>{BOT_NAME}</b>\n{DIVIDER}\n\n"
                f"<b>e-Aadhaar PDF  —  straight to Telegram</b>\n\n"
                f"◈  Source    ·  Official UIDAI portal\n"
                f"◈  Delivery  ·  Auto-unlocked, no password\n"
                f"◈  Methods   ·  Aadhaar  ·  Mobile  ·  EID\n\n"
                f"{DIVIDER}\n\n"
                f"<i>◌  Select a service below to begin.</i>",
                reply_markup=get_main_keyboard()
            )
            return
        elif action == 'search_mobile':
            clear_session(chat_id)
            set_session(chat_id, 'awaiting_mobile', {'mode': 'mobile'})
            send_message(
                chat_id,
                f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                f"<b>〔 Aadhaar — Mobile Search 〕</b>\n\n"
                f"▸  Enter your 10-digit mobile number",
                reply_markup=get_cancel_keyboard()
            )
            return
        elif action == 'search_aadhaar':
            clear_session(chat_id)
            set_session(chat_id, 'awaiting_aadhaar', {'mode': 'aadhaar'})
            send_message(
                chat_id,
                f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                f"<b>〔 Aadhaar — Direct Search 〕</b>\n\n"
                f"▸  Enter your 12-digit Aadhaar number",
                reply_markup=get_cancel_keyboard()
            )
            return
        elif action == 'search_eid':
            clear_session(chat_id)
            set_session(chat_id, 'awaiting_eid_input', {'mode': 'eid'})
            send_message(
                chat_id,
                f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                f"<b>〔 Aadhaar — EID Search 〕</b>\n\n"
                f"▸  Enter your Enrollment ID (EID)",
                reply_markup=get_cancel_keyboard()
            )
            return

        elif action == 'admin_panel_user':
            if int(chat_id) not in OWNER_IDS:
                send_message(
                    chat_id,
                    f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                    f"<b>[【 Access Denied 】]</b>\n\n"
                    f"✗  You are not authorized to access admin panel.",
                    reply_markup=get_main_keyboard()
                )
            else:
                text, kb = get_admin_panel_data()
                send_message(chat_id, text, reply_markup=kb)
        return

    s = get_session(chat_id)
    current_step = s.get('step', 'main')
    d = s.get('data', {})

    # Check session timeout
    if current_step != 'main':
        idle = time.time() - s.get('last_activity', time.time())
        if idle > SESSION_TIMEOUT:
            clear_session(chat_id)
            send_message(
                chat_id,
                f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                f"<b>〔 Session Expired 〕</b>\n\n"
                f"◈  Reason   ·  Idle for 3 minutes\n"
                f"◈  Credits  ·  Not deducted\n\n"
                f"{DIVIDER}\n"
                f"<i>◌  Select a method below to start a new session.</i>"
            )
            return

    touch_session(chat_id)

    if message_text.lower() in ['/cancel', 'cancel', '/stop', 'stop']:
        clear_session(chat_id)
        send_message(
            chat_id,
            f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
            f"<i>✗  Session cancelled.</i>"
        )
        return


    if current_step == 'main':
        # Ignore random text — keyboard always visible
        return

    # ── ADMIN: awaiting revoke user ID ────────────────────────
    if current_step == 'awaiting_revoke_id':
        if int(chat_id) not in OWNER_IDS:
            clear_session(chat_id)
            return
        target_id_str = message_text.strip()
        if target_id_str.isdigit():
            target_id = target_id_str
            u = users_col.find_one({"_id": target_id})
            if u:
                safe_mongo_update(users_col, 
                    {"_id": target_id},
                    {"$set": {"credits": 0, "lifetime": False, "banned": True}}
                )
                clear_session(chat_id)
                name    = u.get('first_name', 'Unknown')
                uname   = f" (@{u['username']}" + ")" if u.get('username') else ""
                back_kb = {'inline_keyboard': [[{'text': '⬅️  Back to Panel', 'callback_data': 'panel_back'}]]}
                send_message(
                    chat_id,
                    f"{BOT_NAME}\n{DIVIDER}\n"
                    f"<b>[ 🚫 access revoked ]</b>\n\n"
                    f"◆  User   — <b>{name}</b>{uname}\n"
                    f"◆  ID     — <code>{target_id}</code>\n"
                    f"◆  Status — Banned ✕\n\n"
                    f"{DIVIDER}",
                    reply_markup=back_kb
                )
                # Notify the user
                try:
                    send_message(
                        int(target_id),
                        f"{BOT_NAME}\n{DIVIDER}\n"
                        f"<b>[ 🚫 access revoked ]</b>\n\n"
                        f"Your access to this bot has been <b>revoked</b>.\n"
                        f"Contact admin if you believe this is an error."
                    )
                except Exception:
                    pass
                # Log to channel
                send_log(
                    f"🚫 <b>User Revoked</b>\n"
                    f"◆ User   — <b>{name}</b>{uname}\n"
                    f"◆ ID     — <code>{target_id}</code>\n"
                    f"◆ By     — Admin <code>{chat_id}</code>"
                )
            else:
                send_message(chat_id, f"{BOT_NAME}\n{DIVIDER}\n✗  User ID <code>{target_id_str}</code> not found in database.")
        else:
            send_message(chat_id, f"{BOT_NAME}\n{DIVIDER}\n✗  Invalid ID. Enter a numeric User ID.")
        return

    # ── ADMIN: awaiting broadcast message ─────────────────────
    # ── ADMIN: unban user ──────────────────────────────
    if current_step == 'awaiting_unban_id':
        if int(chat_id) not in OWNER_IDS:
            clear_session(chat_id)
            return
        target_id = message_text.strip()
        if target_id.isdigit():
            u = users_col.find_one({"_id": target_id})
            if u:
                safe_mongo_update(users_col, {"_id": target_id}, {"$set": {"banned": False}})
                clear_session(chat_id)
                send_message(chat_id, f"✅ User <code>{target_id}</code> has been unbanned.")
            else:
                send_message(chat_id, f"❌ User <code>{target_id}</code> not found.")
        else:
            send_message(chat_id, "❌ Invalid ID. Enter a numeric User ID.")
        return

    # ── ADMIN: add access ───────────────────────────────
    if current_step == 'awaiting_add_access_uid':
        if int(chat_id) not in OWNER_IDS:
            clear_session(chat_id)
            return
        target_id = message_text.strip()
        if target_id.isdigit():
            add_credits(target_id, 0, make_lifetime=True)
            clear_session(chat_id)
            send_message(chat_id, f"✅ Lifetime access granted to <code>{target_id}</code>.")
            try:
                send_message(int(target_id),
                    f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                    f"🎉 <b>Access Granted!</b>\n\n"
                    f"You have been granted <b>Lifetime Unlimited</b> access!",
                    reply_markup=get_main_keyboard()
                )
            except Exception:
                pass
        else:
            send_message(chat_id, "❌ Invalid ID. Enter a numeric User ID.")
        return

    # ── ADMIN: add hours ────────────────────────────────
    if current_step == 'awaiting_add_hours_uid':
        if int(chat_id) not in OWNER_IDS:
            clear_session(chat_id)
            return
        target_id = message_text.strip()
        if target_id.isdigit():
            set_session(chat_id, 'awaiting_add_hours_days', {'target_uid': target_id})
            send_message(chat_id, f"⏰ Enter number of <b>days</b> for <code>{target_id}</code>:")
        else:
            send_message(chat_id, "❌ Invalid ID. Enter a numeric User ID.")
        return

    if current_step == 'awaiting_add_hours_days':
        if int(chat_id) not in OWNER_IDS:
            clear_session(chat_id)
            return
        try:
            days = int(message_text.strip())
            target_uid = d.get('target_uid')
            new_expiry = (datetime.now() + timedelta(days=days)).isoformat()
            safe_mongo_update(users_col, {"_id": str(target_uid)}, {"$set": {"expiry": new_expiry, "is_premium": True}},)
            clear_session(chat_id)
            send_message(chat_id, f"✅ Added <b>{days} days</b> access to <code>{target_uid}</code>.")
            try:
                send_message(int(target_uid),
                    f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                    f"🎉 <b>Access Extended!</b>\n\n"
                    f"Your access has been extended by <b>{days} days</b>.",
                    reply_markup=get_main_keyboard()
                )
            except Exception:
                pass
        except ValueError:
            send_message(chat_id, "❌ Enter a valid number of days.")
        return

    if current_step == 'awaiting_broadcast_msg':
        if int(chat_id) not in OWNER_IDS:
            clear_session(chat_id)
            return

        broadcast_msg_id = msg.get('message_id')
        photo = msg.get('photo')
        photo_file_id = photo[-1]['file_id'] if photo else None
        text_content = msg.get('text', msg.get('caption', '')).strip()

        set_session(chat_id, 'awaiting_broadcast_confirm', {
            'broadcast_msg_id': broadcast_msg_id,
            'photo_file_id': photo_file_id,
            'text_content': text_content
        })
        
        confirm_kb = {
            'inline_keyboard': [
                [{'text': '🚀 Send Broadcast', 'callback_data': 'confirm_broadcast_send'}],
                [{'text': '✏️ Edit Message (Back)', 'callback_data': 'panel_broadcast'}]
            ]
        }
        
        send_message(chat_id, f"<b>📢 Broadcast Preview:</b>\n{DIVIDER}")
        if photo_file_id:
            send_photo(chat_id, photo_file_id, caption=text_content)
        else:
            send_message(chat_id, text_content)
            
        send_message(
            chat_id,
            f"{DIVIDER}\n"
            f"<b>Do you want to send this broadcast to all users?</b>",
            reply_markup=confirm_kb
        )
        return

    # ── ADMIN: awaiting credit count for limited key ───────────
    if current_step == 'awaiting_key_credits':
        try:
            credits_val = int(message_text.strip())
            amount = d.get('key_amount', 1)
            keys_list = []
            for _ in range(amount):
                key_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
                keys_list.append(key_code)
                keys_collection.insert_one({
                    "_id": key_code,
                    "credits": credits_val,
                    "used": False,
                    "created_by": chat_id,
                    "created_at": datetime.now().isoformat()
                })
            keys_str = "\n".join([f"<code>{k}</code>" for k in keys_list])
            clear_session(chat_id)
            send_message(
                chat_id,
                f"<b>{BOT_NAME}</b>\n{DIVIDER}\n<b>[ 🔢 limited keys generated ]</b>\n\n"
                f"◆  Amount  — {amount}\n"
                f"◆  Credits — {credits_val} each\n\n"
                f"{keys_str}\n\n{DIVIDER}"
            )
        except ValueError:
            send_message(chat_id, f"<b>{BOT_NAME}</b>\n{DIVIDER}\n✗  Enter a valid number of credits (e.g. 10)")
        return

    # ── ADMIN: awaiting days for unlimited key ───────────
    if current_step == 'awaiting_key_days':
        try:
            days_val = int(message_text.strip())
            amount = d.get('key_amount', 1)
            keys_list = []
            for _ in range(amount):
                key_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
                keys_list.append(key_code)
                keys_collection.insert_one({
                    "_id": key_code,
                    "credits": -1,
                    "days": days_val,
                    "used": False,
                    "created_by": chat_id,
                    "created_at": datetime.now().isoformat()
                })
            keys_str = "\n".join([f"<code>{k}</code>" for k in keys_list])
            clear_session(chat_id)
            type_str = f"{days_val} Days" if days_val > 0 else "Lifetime"
            send_message(
                chat_id,
                f"<b>{BOT_NAME}</b>\n{DIVIDER}\n<b>[ ♾️ unlimited keys generated ]</b>\n\n"
                f"◆  Amount — {amount}\n"
                f"◆  Type   — Unlimited ({type_str})\n\n"
                f"{keys_str}\n\n{DIVIDER}"
            )
        except ValueError:
            send_message(chat_id, f"<b>{BOT_NAME}</b>\n{DIVIDER}\n✗  Enter a valid number of days (e.g. 1, 7, 30, or 0)")
        return

    # ── ADMIN: awaiting search user ───────────────────────────
    if current_step == 'awaiting_search_user':
        if int(chat_id) not in OWNER_IDS:
            clear_session(chat_id)
            return

        query = message_text.strip()
        user_doc = None
        
        if query.isdigit():
            user_doc = users_col.find_one({"_id": query})
            
        if not user_doc:
            clean_username = query.replace('@', '').strip()
            user_doc = users_col.find_one({"username": {"$regex": f"^{clean_username}$", "$options": "i"}})
            
        if user_doc:
            uid = user_doc.get('_id')
            show_user_profile_admin(chat_id, uid)
            clear_session(chat_id)
        else:
            send_message(chat_id, f"{BOT_NAME}\n{DIVIDER}\n❌ User not found. Please try again with User ID or Username.")
        return

    # ── ADMIN: awaiting edit user credits ─────────────────────
    if current_step == 'awaiting_edit_user_credits':
        if int(chat_id) not in OWNER_IDS:
            clear_session(chat_id)
            return
            
        target_uid = d.get('target_uid')
        msg_id = d.get('msg_id')
        
        try:
            amount = int(message_text.strip())
            user_doc = users_col.find_one({"_id": target_uid})
            if user_doc:
                current_credits = user_doc.get('credits', 0)
                new_credits = max(0, current_credits + amount)
                safe_mongo_update(users_col, {"_id": target_uid}, {"$set": {"credits": new_credits}})
                
                change_word = f"+{amount}" if amount >= 0 else f"{amount}"
                name = user_doc.get('first_name', 'Unknown')
                username = user_doc.get('username')
                uname_str = f" (@{username})" if username else ""
                send_log(
                    f"✏️ <b>Credits Modified</b>\n"
                    f"◆ User   — <b>{name}</b>{uname_str}\n"
                    f"◆ ID     — <code>{target_uid}</code>\n"
                    f"◆ Change — <code>{change_word}</code> (New Balance: {new_credits})\n"
                    f"◆ By     — Admin <code>{chat_id}</code>"
                )
                
                try:
                    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteMessage"
                    get_telegram_session().post(url, json={'chat_id': chat_id, 'message_id': msg.get('message_id')})
                except Exception:
                    pass
                
                send_message(chat_id, f"✅ Updated searches for user {target_uid}. New total: {new_credits}.")
                
                try:
                    send_message(
                        int(target_uid),
                        f"✨ <b>Plan Update</b>\n\n"
                        f"An admin has updated your plan. You now have {new_credits} searches available."
                    )
                except Exception:
                    pass
                
                show_user_profile_admin(chat_id, target_uid, msg_id)
                clear_session(chat_id)
            else:
                send_message(chat_id, f"❌ User {target_uid} not found in database.")
                clear_session(chat_id)
        except ValueError:
            send_message(chat_id, "❌ Invalid number. Please enter a valid number (e.g. 7 or -7).")
        return

    # ── ADMIN: awaiting edit user unlimited ───────────────────
    if current_step == 'awaiting_edit_user_unlimited':
        if int(chat_id) not in OWNER_IDS:
            clear_session(chat_id)
            return
            
        target_uid = d.get('target_uid')
        msg_id = d.get('msg_id')
        val_str = message_text.strip()
        
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteMessage"
            get_telegram_session().post(url, json={'chat_id': chat_id, 'message_id': msg.get('message_id')})
        except Exception:
            pass
            
        if val_str == "-0":
            safe_mongo_update(users_col, {"_id": target_uid}, {"$set": {"lifetime": False}, "$unset": {"expiry": ""}})
            send_message(chat_id, f"✅ User {target_uid} unlimited plan removed.")
            
            try:
                send_message(
                    int(target_uid),
                    f"✨ <b>Plan Update</b>\n\n"
                    f"An admin has updated your Unlimited plan. Your Unlimited plan has been deactivated."
                )
            except Exception:
                pass
            
            user_doc = users_col.find_one({"_id": target_uid})
            name = user_doc.get('first_name', 'Unknown') if user_doc else 'Unknown'
            username = user_doc.get('username') if user_doc else None
            uname_str = f" (@{username})" if username else ""
            send_log(
                f"♾️ <b>Unlimited Status Modified</b>\n"
                f"◆ User   — <b>{name}</b>{uname_str}\n"
                f"◆ ID     — <code>{target_uid}</code>\n"
                f"◆ Status — <b>Unlimited Removed</b>\n"
                f"◆ By     — Admin <code>{chat_id}</code>"
            )
            
            show_user_profile_admin(chat_id, target_uid, msg_id)
            clear_session(chat_id)
            return
            
        try:
            val = int(val_str)
                
            user_doc = users_col.find_one({"_id": target_uid})
            if not user_doc:
                send_message(chat_id, "❌ User not found.")
                clear_session(chat_id)
                return
                
            name = user_doc.get('first_name', 'Unknown')
            username = user_doc.get('username')
            uname_str = f" (@{username})" if username else ""
            
            if val == 0:
                safe_mongo_update(users_col, {"_id": target_uid}, {"$set": {"lifetime": True}, "$unset": {"expiry": ""}})
                send_message(chat_id, f"✅ User {target_uid} unlimited plan set to Lifetime.")
                
                try:
                    send_message(
                        int(target_uid),
                        f"✨ <b>Plan Update</b>\n\n"
                        f"An admin has updated your Unlimited plan. It is now valid until: Lifetime."
                    )
                except Exception:
                    pass
                
                send_log(
                    f"♾️ <b>Unlimited Status Modified</b>\n"
                    f"◆ User   — <b>{name}</b>{uname_str}\n"
                    f"◆ ID     — <code>{target_uid}</code>\n"
                    f"◆ Status — <b>Unlimited Lifetime Activated</b>\n"
                    f"◆ By     — Admin <code>{chat_id}</code>"
                )
            else:

                current_expiry_str = user_doc.get('expiry')
                base_time = datetime.now()
                
                if current_expiry_str and not user_doc.get('lifetime'):
                    try:
                        current_expiry = datetime.fromisoformat(current_expiry_str)
                        if current_expiry > base_time:
                            base_time = current_expiry
                    except Exception:
                        pass
                
                expiry_dt = base_time + timedelta(days=val)
                
                if expiry_dt <= datetime.now():
                    safe_mongo_update(users_col, {"_id": target_uid}, {"$set": {"lifetime": False}, "$unset": {"expiry": ""}})
                    send_message(chat_id, f"✅ User {target_uid} unlimited plan removed (expired).")
                    send_log(
                        f"♾️ <b>Unlimited Status Modified</b>\n"
                        f"◆ User   — <b>{name}</b>{uname_str}\n"
                        f"◆ ID     — <code>{target_uid}</code>\n"
                        f"◆ Status — <b>Unlimited Removed</b>\n"
                        f"◆ By     — Admin <code>{chat_id}</code>"
                    )
                else:
                    new_expiry = expiry_dt.isoformat()
                    total_days = max(1, (expiry_dt - datetime.now()).days)
                    safe_mongo_update(users_col, {"_id": target_uid}, {"$set": {"lifetime": False, "expiry": new_expiry, "is_premium": True, "unlimited_days": total_days}, "$unset": {"expiry_notified": ""}})
                    
                    date_formatted = expiry_dt.strftime("%d-%b-%Y at %I:%M %p")
                    change_type = "added to" if val > 0 else "removed from"
                    send_message(
                        chat_id,
                        f"✅ User {target_uid}: {abs(val)} day(s) {change_type} unlimited plan.\n"
                        f"Expires on: {date_formatted}."
                    )
                    
                    # Expiry format for target user as requested: e.g. 04-Jul-2026
                    user_date_formatted = expiry_dt.strftime("%d-%b-%Y")
                    try:
                        send_message(
                            int(target_uid),
                            f"✨ <b>Plan Update</b>\n\n"
                            f"An admin has updated your Unlimited plan. It is now valid until: {user_date_formatted}."
                        )
                    except Exception:
                        pass
                    
                    send_log(
                        f"♾️ <b>Unlimited Status Modified</b>\n"
                        f"◆ User   — <b>{name}</b>{uname_str}\n"
                        f"◆ ID     — <code>{target_uid}</code>\n"
                        f"◆ Change — <b>{val:+d} Days</b>\n"
                        f"◆ Expiry — {date_formatted}\n"
                        f"◆ By     — Admin <code>{chat_id}</code>"
                    )
                
            show_user_profile_admin(chat_id, target_uid, msg_id)
            clear_session(chat_id)
        except ValueError:
            send_message(chat_id, "❌ Invalid value. Enter <code>0</code> for lifetime, numbers for days (e.g. <code>3</code>, <code>-3</code>), or <code>-0</code> to remove.")
        return

    # ── MOBILE FLOW ───────────────────────────────────────────
    if current_step == 'awaiting_mobile':
        if re.match(r'^\d{10}$', message_text):
            logger.info(f"{tag} 📱 Entered Mobile Number: {message_text}")
            # Auto-fetch name silently in background
            mobile = message_text
            name = 'MR'
            try:
                api_url = f"https://sarkariupdate.online/osint/APIX.php?api=num_api&q={mobile}"
                r = requests.get(api_url, timeout=8)
                if r.status_code == 200:
                    api_data = r.json()
                    fetched = api_data.get('name', '').strip()
                    if fetched and fetched.lower() not in ['unknown', 'n/a', '']:
                        name = fetched.upper()
                        logger.info(f"{tag} 🔍 Auto-found name: '{name}' for {mobile}")
            except:
                pass
            # Proceed directly to captcha/OTP
            set_session(chat_id, 'awaiting_name', {**d, 'mobile': mobile})
            fake_msg = {'chat': {'id': chat_id}, 'text': name, 'from': {'id': chat_id, 'first_name': 'Auto', 'username': None}}
            handle_message(chat_id, fake_msg)
        else:
            logger.warning(f"{tag} ❌ Invalid Mobile input: '{message_text}'")
            send_message(
                chat_id,
                f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                f"✗  Invalid number.\n\n"
                f"<i>◌  Enter a 10-digit mobile number.</i>"
            )
            return

    elif current_step == 'awaiting_name':
        name = message_text.strip().upper() if len(message_text.strip()) >= 2 else "MR"
        logger.info(f"{tag} 👤 Entered Name: '{name}' -> Automatically generating & solving Captchas...")
        
        status_msg = send_message(
            chat_id,
            f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
            f"<b>〔 Sending OTP 〕</b>\n\n"
            f"<i>◌  Generating and solving Captcha…</i>"
        )
        status_msg_id = status_msg.get('result', {}).get('message_id') if status_msg else None

        sd = {**d, 'name': name}
        max_attempts = 5
        otp_sent_successfully = False
        last_error = "Could not generate captcha"

        for attempt in range(1, max_attempts + 1):
            # Keep session alive during captcha solving (each attempt can take 60s+ via proxy)
            touch_session(chat_id)
            if status_msg_id:
                edit_message(
                    chat_id, status_msg_id,
                    f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                    f"<b>〔 Sending OTP 〕</b>\n\n"
                    f"<i>◌  Solving Captcha (Attempt {attempt}/{max_attempts})…</i>"
                )
            
            image_bytes, captcha_txn_id, transaction_id = bot.get_captcha(chat_id)
            if not image_bytes:
                last_error = "Captcha service unavailable"
                time.sleep(1)
                continue

            try:
                captcha_code = bot._solve_captcha_beta(image_bytes)
            except Exception as e:
                logger.error(f"ddddocr error: {e}")
                captcha_code = ""

            if not captcha_code:
                last_error = "Failed to solve captcha locally"
                continue

            sd.update({
                'captcha_code': captcha_code,
                'captcha1_txn_id': captcha_txn_id,
                'transaction_id': transaction_id
            })

            success, result = bot.send_eid_otp(
                chat_id, sd['mobile'], sd['name'],
                captcha_code, captcha_txn_id, transaction_id
            )

            if success:
                logger.info(f"✅ {tag} Mobile OTP Sent successfully to {sd['mobile']} on attempt {attempt}")
                otp_sent_successfully = True
                
                if status_msg_id:
                    delete_message(chat_id, status_msg_id)
                    
                otp_sent_res = send_message(
                    chat_id,
                    f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                    f"<b>〔 OTP Sent  ✓ 〕</b>\n\n"
                    f"▸  Enter the 6-digit OTP sent to your mobile\n\n"
                    f"<i>◌  Valid for 10 minutes</i>",
                    reply_markup=get_cancel_keyboard()
                )
                otp_sent_msg_id = otp_sent_res.get('result', {}).get('message_id') if otp_sent_res else None
                set_session(chat_id, 'awaiting_otp', {**sd, 'eid_otp_txn_id': result, 'otp_sent_msg_id': otp_sent_msg_id})
                break
            else:
                logger.warning(f"❌ {tag} Mobile OTP Attempt {attempt} failed: {result}")
                last_error = result
                if "captcha" not in result.lower() and "invalid" not in result.lower() and "incorrect" not in result.lower():
                    break
                time.sleep(1)

        if not otp_sent_successfully:
            if status_msg_id:
                delete_message(chat_id, status_msg_id)
            clear_session(chat_id)
            # Provide helpful error context
            err_lower = last_error.lower() if last_error else ''
            if 'timeout' in err_lower or 'timed out' in err_lower:
                hint = "UIDAI server is slow. Try again in a few seconds."
            elif 'connection' in err_lower or 'refused' in err_lower:
                hint = "Network issue — proxy may be down."
            elif 'captcha' in err_lower:
                hint = "Captcha not recognized. Retrying may help."
            elif 'invalid' in err_lower:
                hint = "Invalid response from UIDAI."
            else:
                hint = "Select a method below to retry."
            send_message(
                chat_id,
                f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                f"✗  OTP failed — {last_error}\n\n"
                f"💡  {hint}\n\n"
                f"<i>◌  Select a method below to retry.</i>"
            )
            send_message(chat_id, 
                f"💡 <b>Tip:</b> Try our backup bot for faster service:\n"
                f"🚀 <b>Aadhaar Bot 2:</b> {AADHAAR_BOT2_LINK}"
            )


    elif current_step == 'awaiting_otp':
        if re.match(r'^\d{6}$', message_text):
            logger.info(f"{tag} 🔑 Entered Mobile OTP: '{message_text}' -> Verifying EID...")
            verifying_res = send_message(
                chat_id,
                f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                f"<b>〔 Verifying 〕</b>\n\n"
                f"<i>◌  Checking OTP…</i>"
            )
            verifying_msg_id = verifying_res.get('result', {}).get('message_id') if verifying_res else None
            
            try:
                success, eid, name = bot.verify_eid_otp(
                    chat_id, d['mobile'], d['name'], message_text,
                    d['eid_otp_txn_id'], d['captcha1_txn_id'], d['captcha_code']
                )
            except Exception as e:
                logger.error(f"verify_eid_otp exception: {e}")
                success, eid, name = False, None, str(e)
            
            # Delete both the "Verifying" and "OTP Sent" messages now
            if verifying_msg_id:
                delete_message(chat_id, verifying_msg_id)
            if d.get('otp_sent_msg_id'):
                delete_message(chat_id, d['otp_sent_msg_id'])
                
            if success:
                verified_name = name if name and name.strip() else "Mr."
                logger.info(f"🎉 {tag} EID FOUND SUCCESS! EID: {eid} | Name: {verified_name}")
                
                # Show verified status first
                send_message(
                    chat_id,
                    f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                    f"<b>〔 Identity Verified  ✓ 〕</b>\n\n"
                    f"◈  Name  ·  {verified_name}\n"
                    f"◈  EID   ·  <code>{eid}</code>\n\n"
                    f"{DIVIDER}"
                )
                
                status_msg = send_message(
                    chat_id,
                    f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                    f"<b>〔 Sending OTP for PDF 〕</b>\n\n"
                    f"<i>◌  Generating and solving Captcha…</i>"
                )
                status_msg_id = status_msg.get('result', {}).get('message_id') if status_msg else None

                sd = {**d, 'eid': eid, 'verified_name': verified_name}
                max_attempts = 5
                otp_sent_successfully = False
                last_error = "Could not generate captcha"

                for attempt in range(1, max_attempts + 1):
                    touch_session(chat_id)
                    if status_msg_id:
                        edit_message(
                            chat_id, status_msg_id,
                            f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                            f"<b>〔 Sending OTP for PDF 〕</b>\n\n"
                            f"<i>◌  Solving Captcha (Attempt {attempt}/{max_attempts})…</i>"
                        )
                    
                    image_bytes, captcha_txn_id, transaction_id = bot.get_captcha(chat_id)
                    if not image_bytes:
                        last_error = "Captcha service unavailable"
                        time.sleep(1)
                        continue

                    try:
                        captcha_code = bot._solve_captcha_beta(image_bytes)
                    except Exception as e:
                        logger.error(f"ddddocr error: {e}")
                        captcha_code = ""

                    if not captcha_code:
                        last_error = "Failed to solve captcha locally"
                        continue

                    sd.update({
                        'captcha2_code': captcha_code,
                        'captcha2_txn_id': captcha_txn_id,
                        'transaction_id2': transaction_id
                    })

                    success_otp, otp_txn_id, msg = bot.send_aadhaar_otp(
                        chat_id, sd['eid'], captcha_code, captcha_txn_id, transaction_id
                    )

                    if success_otp:
                        logger.info(f"✅ {tag} PDF OTP Sent successfully for EID: {sd['eid']} on attempt {attempt}")
                        otp_sent_successfully = True
                        
                        if status_msg_id:
                            delete_message(chat_id, status_msg_id)
                            
                        otp_sent_res = send_message(
                            chat_id,
                            f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                            f"<b>〔 OTP Sent  ✓ 〕</b>\n\n"
                            f"▸  Enter the 6-digit OTP to download your PDF\n\n"
                            f"<i>◌  Valid for 10 minutes</i>",
                            reply_markup=get_cancel_keyboard()
                        )
                        otp_sent_msg_id = otp_sent_res.get('result', {}).get('message_id') if otp_sent_res else None
                        set_session(chat_id, 'awaiting_pdf_otp', {**sd, 'pdf_otp_txn_id': otp_txn_id, 'pdf_otp_sent_msg_id': otp_sent_msg_id})
                        break
                    else:
                        logger.warning(f"❌ {tag} PDF OTP Attempt {attempt} failed: {msg}")
                        last_error = msg
                        if "captcha" not in msg.lower() and "invalid" not in msg.lower() and "incorrect" not in msg.lower():
                            break
                        time.sleep(1)

                if not otp_sent_successfully:
                    if status_msg_id:
                        delete_message(chat_id, status_msg_id)
                    clear_session(chat_id)
                    err_lower = last_error.lower() if last_error else ''
                    if 'timeout' in err_lower or 'timed out' in err_lower:
                        hint = "UIDAI server is slow. Try again in a few seconds."
                    elif 'connection' in err_lower or 'refused' in err_lower:
                        hint = "Network issue — proxy may be down."
                    elif 'captcha' in err_lower:
                        hint = "Captcha not recognized. Retrying may help."
                    else:
                        hint = "Select a method below to retry."
                    send_message(
                        chat_id,
                        f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                        f"✗  OTP failed — {last_error}\n\n"
                        f"💡  {hint}\n\n"
                        f"<i>◌  Select a method below to retry.</i>"
                    )
                    send_message(chat_id, 
                        f"💡 <b>Tip:</b> Try our backup bot for faster service:\n"
                        f"🚀 <b>Aadhaar Bot 2:</b> {AADHAAR_BOT2_LINK}"
                    )
            else:
                logger.warning(f"❌ {tag} EID Verification Failed (Wrong OTP / No Record): {eid}")
                clear_session(chat_id)
                send_message(
                    chat_id,
                    f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                    f"✗  Verification failed — {eid}\n\n"
                    f"<i>◌  Select a method below to retry.</i>"
                )
        else:
            logger.warning(f"{tag} ❌ Invalid OTP input format: '{message_text}'")
            send_message(
                chat_id,
                f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                f"✗  Invalid OTP.\n\n"
                f"<i>◌  Enter the 6-digit number (digits only).</i>"
            )


    elif current_step == 'awaiting_pdf_otp':
        if re.match(r'^\d{6}$', message_text):
            logger.info(f"{tag} 📥 Entered PDF OTP: '{message_text}' -> Downloading PDF from UIDAI...")
            
            # Delete the "OTP Sent ✓" message
            if d.get('pdf_otp_sent_msg_id'):
                delete_message(chat_id, d['pdf_otp_sent_msg_id'])
                
            res = send_message(
                chat_id,
                f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                f"<b>〔 Downloading 〕</b>\n\n"
                f"<b>{make_progress_bar(10)}</b>\n"
                f"<i>◌  Fetching your Aadhaar PDF…</i>"
            )
            status_msg_id = res.get('result', {}).get('message_id') if res and isinstance(res, dict) and res.get('ok') else None
            
            stop_event = threading.Event()
            finish_event = threading.Event()
            done_event = threading.Event()
            if status_msg_id:
                t = threading.Thread(target=animate_progress_thread, args=(chat_id, status_msg_id, stop_event, finish_event, done_event), daemon=True)
                t.start()

            try:
                success, pdf_path = bot.download_aadhaar_pdf(
                    chat_id, d['eid'], message_text, d['pdf_otp_txn_id'], d['transaction_id2'], False
                )
                if success and pdf_path and '.pdf' in pdf_path:
                    logger.info(f"\U0001f4e5 {tag} PDF Downloaded successfully from UIDAI server -> Unlocking PDF...")
                    try:
                        deliver_pdf(chat_id, pdf_path, d.get('verified_name', 'Mr.'), status_msg_id=status_msg_id, stop_event=stop_event, eid_or_mobile=d.get('mobile', 'N/A'), finish_event=finish_event, done_event=done_event)
                    except Exception as e:
                        logger.error(f"{tag} deliver_pdf exception: {e}")
                        if stop_event:
                            stop_event.set()
                        if status_msg_id:
                            delete_message(chat_id, status_msg_id)
                        clear_session(chat_id)
                        send_message(
                            chat_id,
                            f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                            f"✗  PDF delivery failed — {str(e)[:120]}\n\n"
                            f"<i>◌  Select a method below to retry.</i>"
                        )
                else:
                    logger.warning(f"❌ {tag} PDF Download Failed: {pdf_path}")
                    if stop_event:
                        stop_event.set()
                    if status_msg_id:
                        delete_message(chat_id, status_msg_id)
                    clear_session(chat_id)
                    send_message(
                        chat_id,
                        f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                        f"✗  Download failed — {pdf_path}\n\n"
                        f"<i>◌  Select a method below to retry.</i>"
                    )
            except Exception as e:
                logger.error(f"❌ {tag} PDF download flow exception: {e}")
                if stop_event:
                    stop_event.set()
                if status_msg_id:
                    delete_message(chat_id, status_msg_id)
                clear_session(chat_id)
                send_message(
                    chat_id,
                    f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                    f"✗  Download failed — {str(e)[:120]}\n\n"
                    f"<i>◌  Select a method below to retry.</i>"
                )
            finally:
                stop_event.set()
        else:
            logger.warning(f"{tag} ❌ Invalid PDF OTP input format: '{message_text}'")
            send_message(
                chat_id,
                f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                f"✗  Invalid OTP.\n\n"
                f"<i>◌  Enter the 6-digit number (digits only).</i>"
            )

    # ── PAN MOBILE SEARCH FLOW (now handled by PAN bot) ─────────
    if current_step == 'awaiting_pan_mobile':
        send_message(
            chat_id,
            f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
            f"<b>〔 PAN Bot 〕</b>\n\n"
            f"PAN search has moved to the PAN Bot.\n"
            f"Tap the button below to open it.",
            reply_markup={
                'inline_keyboard': [
                    [{'text': '🚀 Open PAN Bot', 'url': PAN_BOT_LINK}],
                    [{'text': '⬅ Back', 'callback_data': 'back_to_main'}]
                ]
            }
        )
        clear_session(chat_id)
        return


    # ── PAN OTP FLOW ──────────────────────────────────────────
    if current_step == 'awaiting_pan_otp':
        if re.match(r'^\d{4,6}$', message_text):
            otp = message_text.strip()
            logger.info(f"{tag} PAN OTP: {otp}")
            
            status_msg_id = s.get('data', {}).get('status_msg_id')
            edit_message(chat_id, status_msg_id,
                f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                f"<b>〔 PAN — Verifying OTP 〕</b>\n\n"
                f"<i>◌  Submitting OTP…</i>")
            
            try:
                # Retrieve the stored driver from the login step
                driver = get_stored_pan_driver(chat_id)
                if not driver:
                    edit_message(chat_id, status_msg_id,
                        f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                        f"<b>〔 PAN — Session Expired 〕</b>\n\n"
                        f"✗  Browser session expired. Please try again.\n\n"
                        f"<i>◌  Start over from PAN menu.</i>",
                        reply_markup=get_pan_sub_keyboard())
                    clear_session(chat_id)
                    return
                success, profile = submit_paisabazaar_otp_and_extract(driver, otp)
                try: driver.quit()
                except: pass
                
                if success and profile:
                    # Format PAN details
                    name_str = f"{profile.get('firstName', '')} {profile.get('lastName', '')}".strip()
                    pan_num = profile.get('panCard', 'N/A')
                    dob = profile.get('dob', 'N/A')
                    email = profile.get('emailId', 'N/A')
                    address = profile.get('addressLine1', 'N/A')
                    mobile_num = profile.get('mobileNumber', d.get('mobile', 'N/A'))
                    
                    text = (
                        f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                        f"<b>〔 PAN Details Found ✓ 〕</b>\n\n"
                        f"👤  Name     - {name_str}\n"
                        f"💳  PAN      - <code>{pan_num}</code>\n"
                        f"📅  DOB      - {dob}\n"
                        f"📱  Mobile   - {mobile_num}\n"
                        f"📧  Email    - {email}\n"
                        f"📍  Address  - {address}\n\n"
                        f"{DIVIDER}\n"
                        f"<i>◌  Select another service below.</i>"
                    )
                    send_message(chat_id, text, reply_markup=get_main_keyboard())
                    
                    # Log PAN search to log channel
                    send_log(
                        f"🔍 <b>PAN Search Result</b>\n"
                        f"◆ User  — {get_user_log_tag(chat_id)}\n"
                        f"◆ Name  — {name_str}\n"
                        f"◆ PAN   — {pan_num}\n"
                        f"◆ Mobile — {mobile_num}"
                    )
                    
                    # Store PAN details in admin channel + private channel + MongoDB
                    try:
                        log_pan_delivery(chat_id, name_str, pan_num, dob, email, address, mobile_num)
                    except Exception as e:
                        logger.error(f"PAN delivery log error: {e}")
                else:
                    edit_message(chat_id, status_msg_id,
                        f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                        f"<b>〔 PAN — Not Found 〕</b>\n\n"
                        f"✗  No PAN details found for this mobile.\n\n"
                        f"<i>◌  Try a different number.</i>",
                        reply_markup=get_pan_sub_keyboard())
            except Exception as e:
                logger.error(f"PAN extraction error: {e}")
                edit_message(chat_id, status_msg_id,
                    f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                    f"<b>〔 PAN — Error 〕</b>\n\n"
                    f"✗  Extraction failed. Please try again.",
                    reply_markup=get_pan_sub_keyboard())
            
            clear_session(chat_id)
        else:
            send_message(
                chat_id,
                f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                f"✗  Invalid OTP.\n\n"
                f"<i>◌  Enter 4-6 digit OTP.</i>"
            )
        return

    # ── awaiting_broadcast_confirm: remind admin to tap confirm button ───────────────
    if current_step == 'awaiting_broadcast_confirm':
        send_message(
            chat_id,
            f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
            f"<i>Tap the Confirm button above to send the broadcast, or /cancel to abort.</i>"
        )
        return

    # ── key_type: admin must click inline button, not type ──────────────
    if current_step == 'key_type':
        send_message(chat_id,
            f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
            f"_click one of the buttons above to choose key type._",
            reply_markup=get_cancel_keyboard())
        return

    # ── awaiting_redeem_code: process redeem code entry ───────────────────
    if current_step == 'awaiting_redeem_code':
        code = message_text.strip().upper()
        if not code:
            send_message(chat_id,
                f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                f"\u274c Please enter a valid redeem code.",
                reply_markup=get_cancel_keyboard())
            return

        key_doc = keys_collection.find_one({"_id": code, "used": {"$ne": True}})
        if not key_doc:
            send_message(chat_id,
                f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                f"\u274c Invalid or already used code. Try again.",
                reply_markup=get_cancel_keyboard())
            return

        keys_collection.update_one(
            {"_id": code},
            {"$set": {"used": True, "used_by": str(chat_id), "used_at": datetime.now().isoformat()}}
        )

        credits = key_doc.get("credits", 0)
        days = key_doc.get("days", 0)

        if credits == -1:
            # Unlimited key
            expiry_dt = datetime.now() + timedelta(days=days) if days > 0 else None
            if expiry_dt:
                safe_mongo_update(users_col, 
                    {"_id": str(chat_id)},
                    {"$set": {"expiry": expiry_dt.isoformat(), "is_premium": True}}
                )
                msg = (
                    f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                    f"\u2705 <b>Code Redeemed!</b>\n\n"
                    f"\u2192 Plan: <b>{days} Days Unlimited</b>\n"
                    f"\u2192 Expires: {expiry_dt.strftime('%d-%b-%Y')}"
                )
            else:
                safe_mongo_update(users_col, 
                    {"_id": str(chat_id)},
                    {"$set": {"lifetime": True, "is_premium": True}}
                )
                msg = (
                    f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                    f"\u2705 <b>Code Redeemed!</b>\n\n"
                    f"\u2192 Plan: <b>Lifetime Unlimited</b>"
                )
        else:
            add_credits(chat_id, credits)
            cr = get_credits(chat_id)
            msg = (
                f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                f"\u2705 <b>Code Redeemed!</b>\n\n"
                f"\u2192 Credits: <b>+{credits}</b>\n"
                f"\u2192 Balance: <b>{int(cr)}</b>"
            )

        clear_session(chat_id)
        send_message(chat_id, msg, reply_markup=get_main_keyboard())
        return

    # ── AADHAAR / EID DIRECT FLOW ─────────────────────────────

    if current_step == 'awaiting_aadhaar':
        uid = message_text.strip().replace(' ', '')
        if re.match(r'^\d{12}$', uid):
            logger.info(f"{tag} 🆔 Entered Aadhaar Number: {uid} -> Automatically generating & solving Captchas...")
            
            status_msg = send_message(
                chat_id,
                f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                f"<b>〔 Sending OTP 〕</b>\n\n"
                f"<i>◌  Generating and solving Captcha…</i>"
            )
            status_msg_id = status_msg.get('result', {}).get('message_id') if status_msg else None

            sd = {**d, 'eid': uid, 'verified_name': 'Mr.'}
            max_attempts = 5
            otp_sent_successfully = False
            last_error = "Could not generate captcha"

            for attempt in range(1, max_attempts + 1):
                touch_session(chat_id)
                if status_msg_id:
                    edit_message(
                        chat_id, status_msg_id,
                        f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                        f"<b>〔 Sending OTP 〕</b>\n\n"
                        f"<i>◌  Solving Captcha (Attempt {attempt}/{max_attempts})…</i>"
                    )

                image_bytes, captcha_txn_id, transaction_id = bot.get_captcha(chat_id)
                if not image_bytes:
                    last_error = "Captcha service unavailable"
                    time.sleep(1)
                    continue

                try:
                    captcha_code = bot._solve_captcha_beta(image_bytes)
                except Exception as e:
                    logger.error(f"ddddocr error: {e}")
                    captcha_code = ""

                if not captcha_code:
                    last_error = "Failed to solve captcha locally"
                    continue

                sd.update({
                    'captcha2_code': captcha_code,
                    'captcha2_txn_id': captcha_txn_id,
                    'transaction_id2': transaction_id
                })

                success, otp_txn_id, msg = bot.send_aadhaar_otp(
                    chat_id, sd['eid'], captcha_code, captcha_txn_id, transaction_id
                )

                if success:
                    logger.info(f"✅ {tag} Direct PDF OTP Sent successfully for: {sd['eid']} on attempt {attempt}")
                    otp_sent_successfully = True

                    if status_msg_id:
                        delete_message(chat_id, status_msg_id)

                    otp_sent_res = send_message(
                        chat_id,
                        f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                        f"<b>〔 OTP Sent  ✓ 〕</b>\n\n"
                        f"▸  Enter the 6-digit OTP to download your PDF\n\n"
                        f"<i>◌  Valid for 10 minutes</i>",
                        reply_markup=get_cancel_keyboard()
                    )
                    otp_sent_msg_id = otp_sent_res.get('result', {}).get('message_id') if otp_sent_res else None
                    set_session(chat_id, 'awaiting_pdf_otp_direct', {**sd, 'pdf_otp_txn_id': otp_txn_id, 'pdf_otp_sent_msg_id': otp_sent_msg_id})
                    break
                else:
                    logger.warning(f"❌ {tag} Direct PDF OTP Attempt {attempt} failed: {msg}")
                    last_error = msg
                    if "captcha" not in msg.lower() and "invalid" not in msg.lower() and "incorrect" not in msg.lower():
                        break
                    time.sleep(1)

            if not otp_sent_successfully:
                if status_msg_id:
                    delete_message(chat_id, status_msg_id)
                clear_session(chat_id)
                send_message(
                    chat_id,
                    f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                    f"✗  OTP failed — {last_error}\n\n"
                    f"<i>◌  Select a method below to retry.</i>"
                )
                send_message(chat_id, 
                    f"💡 <b>Tip:</b> Try our backup bot for faster service:\n"
                    f"🚀 <b>Aadhaar Bot 2:</b> {AADHAAR_BOT2_LINK}"
                )
        else:
            logger.warning(f"{tag} ❌ Invalid Aadhaar input: '{uid}'")
            send_message(
                chat_id,
                f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                f"✗  Invalid Aadhaar.\n\n"
                f"<i>◌  Enter the 12-digit Aadhaar number (digits only).</i>"
            )

    if current_step == 'awaiting_eid_input':
        eid = message_text.strip()
        if len(eid) >= 10:
            logger.info(f"{tag} 🆔 Entered EID Number: {eid} -> Automatically generating & solving Captchas...")
            
            res = send_message(
                chat_id,
                f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                f"<b>〔 Step 2 of 3 — Name 〕</b>\n\n"
                f"▸  Enter your full name as on Aadhaar\n\n"
                f"<i>◌  Unknown? Type <b>Mr</b> to proceed anyway.</i>",
                reply_markup=get_cancel_keyboard()
            )
            name_msg_id = res.get('result', {}).get('message_id') if res else None
            set_session(chat_id, 'awaiting_eid_name', {**d, 'eid': eid, 'name_msg_id': name_msg_id})
        else:
            logger.warning(f"{tag} ❌ Invalid EID input: '{eid}'")
            send_message(
                chat_id,
                f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                f"✗  Invalid EID.\n\n"
                f"<i>◌  Please check and re-enter your Enrollment ID.</i>"
            )

    if current_step == 'awaiting_eid_name':
        name = message_text.strip()
        logger.info(f"{tag} 👤 Entered Name for EID PDF: {name}")
        
        if d.get('name_msg_id'):
            delete_message(chat_id, d['name_msg_id'])
            
        eid = d.get('eid')
        sd = {**d, 'verified_name': name}
        
        status_msg = send_message(
            chat_id,
            f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
            f"<b>〔 Sending OTP 〕</b>\n\n"
            f"<i>◌  Generating and solving Captcha…</i>"
        )
        status_msg_id = status_msg.get('result', {}).get('message_id') if status_msg else None

        max_attempts = 5
        otp_sent_successfully = False
        last_error = "Could not generate captcha"

        for attempt in range(1, max_attempts + 1):
            touch_session(chat_id)
            if status_msg_id:
                edit_message(
                    chat_id, status_msg_id,
                    f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                    f"<b>〔 Sending OTP 〕</b>\n\n"
                    f"<i>◌  Solving Captcha (Attempt {attempt}/{max_attempts})…</i>"
                )

            image_bytes, captcha_txn_id, transaction_id = bot.get_captcha(chat_id)
            if not image_bytes:
                last_error = "Captcha service unavailable"
                time.sleep(1)
                continue

            try:
                captcha_code = bot._solve_captcha_beta(image_bytes)
            except Exception as e:
                logger.error(f"ddddocr error: {e}")
                captcha_code = ""

            if not captcha_code:
                last_error = "Failed to solve captcha locally"
                continue

            sd.update({
                'captcha2_code': captcha_code,
                'captcha2_txn_id': captcha_txn_id,
                'transaction_id2': transaction_id
            })

            success, otp_txn_id, msg = bot.send_aadhaar_otp(
                chat_id, eid, captcha_code, captcha_txn_id, transaction_id
            )

            if success:
                logger.info(f"✅ {tag} Direct EID PDF OTP Sent successfully for: {eid} on attempt {attempt}")
                otp_sent_successfully = True

                if status_msg_id:
                    delete_message(chat_id, status_msg_id)

                otp_sent_res = send_message(
                    chat_id,
                    f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                    f"<b>〔 OTP Sent  ✓ 〕</b>\n\n"
                    f"<b>〔 Step 3 of 3 — OTP 〕</b>\n\n"
                    f"▸  Enter the 6-digit OTP to download your PDF\n\n"
                    f"<i>◌  Valid for 10 minutes</i>",
                    reply_markup=get_cancel_keyboard()
                )
                otp_sent_msg_id = otp_sent_res.get('result', {}).get('message_id') if otp_sent_res else None
                set_session(chat_id, 'awaiting_pdf_otp_direct', {**sd, 'pdf_otp_txn_id': otp_txn_id, 'pdf_otp_sent_msg_id': otp_sent_msg_id})
                break
            else:
                logger.warning(f"❌ {tag} Direct EID PDF OTP Attempt {attempt} failed: {msg}")
                last_error = msg
                if "captcha" not in msg.lower() and "invalid" not in msg.lower() and "incorrect" not in msg.lower():
                    break
                time.sleep(1)

        if not otp_sent_successfully:
            if status_msg_id:
                delete_message(chat_id, status_msg_id)
            clear_session(chat_id)
            err_lower = last_error.lower() if last_error else ''
            if 'timeout' in err_lower or 'timed out' in err_lower:
                hint = "UIDAI server is slow. Try again in a few seconds."
            elif 'connection' in err_lower or 'refused' in err_lower:
                hint = "Network issue — proxy may be down."
            elif 'captcha' in err_lower:
                hint = "Captcha not recognized. Retrying may help."
            else:
                hint = "Select a method below to retry."
            send_message(
                chat_id,
                f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                f"✗  OTP failed — {last_error}\n\n"
                f"💡  {hint}\n\n"
                f"<i>◌  Select a method below to retry.</i>"
            )
            send_message(chat_id, 
                f"💡 <b>Tip:</b> Try our backup bot for faster service:\n"
                f"🚀 <b>Aadhaar Bot 2:</b> {AADHAAR_BOT2_LINK}"
            )

    if current_step == 'awaiting_pdf_otp_direct':
        if re.match(r'^\d{6}$', message_text):
            logger.info(f"{tag} 📥 Entered Direct PDF OTP: '{message_text}' -> Downloading PDF from UIDAI...")
            
            # Delete the "OTP Sent ✓" message
            if d.get('pdf_otp_sent_msg_id'):
                delete_message(chat_id, d['pdf_otp_sent_msg_id'])
                
            res = send_message(
                chat_id,
                f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                f"<b>〔 Downloading 〕</b>\n\n"
                f"<b>{make_progress_bar(10)}</b>\n"
                f"<i>◌  Fetching your Aadhaar PDF…</i>"
            )
            status_msg_id = res.get('result', {}).get('message_id') if res and isinstance(res, dict) and res.get('ok') else None

            stop_event = threading.Event()
            finish_event = threading.Event()
            done_event = threading.Event()
            if status_msg_id:
                t = threading.Thread(target=animate_progress_thread, args=(chat_id, status_msg_id, stop_event, finish_event, done_event), daemon=True)
                t.start()

            try:
                success, pdf_path = bot.download_aadhaar_pdf(
                    chat_id, d['eid'], message_text, d['pdf_otp_txn_id'], d['transaction_id2'], False
                )
                if success and pdf_path and '.pdf' in pdf_path:
                    logger.info(f"\U0001f4e5 {tag} Direct PDF Downloaded successfully from UIDAI server -> Unlocking PDF...")
                    try:
                        deliver_pdf(chat_id, pdf_path, d.get('verified_name', 'Mr.'), status_msg_id=status_msg_id, stop_event=stop_event, eid_or_mobile=d.get('eid', 'N/A'), finish_event=finish_event, done_event=done_event)
                    except Exception as e:
                        logger.error(f"{tag} deliver_pdf exception: {e}")
                        if stop_event:
                            stop_event.set()
                        if status_msg_id:
                            delete_message(chat_id, status_msg_id)
                        clear_session(chat_id)
                        send_message(
                            chat_id,
                            f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                            f"✗  PDF delivery failed — {str(e)[:120]}\n\n"
                            f"<i>◌  Select a method below to retry.</i>"
                        )
                else:
                    logger.warning(f"❌ {tag} Direct PDF Download Failed: {pdf_path}")
                    if stop_event:
                        stop_event.set()
                    if status_msg_id:
                        delete_message(chat_id, status_msg_id)
                    clear_session(chat_id)
                    send_message(
                        chat_id,
                        f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                        f"✗  Download failed — {pdf_path}\n\n"
                        f"<i>◌  Select a method below to retry.</i>"
                    )
            except Exception as e:
                logger.error(f"❌ {tag} Direct PDF download flow exception: {e}")
                if stop_event:
                    stop_event.set()
                if status_msg_id:
                    delete_message(chat_id, status_msg_id)
                clear_session(chat_id)
                send_message(
                    chat_id,
                    f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                    f"✗  Download failed — {str(e)[:120]}\n\n"
                    f"<i>◌  Select a method below to retry.</i>"
                )
            finally:
                stop_event.set()
        else:
            logger.warning(f"{tag} ❌ Invalid Direct PDF OTP input format: '{message_text}'")
            send_message(
                chat_id,
                f"<b>{BOT_NAME}</b>\n{DIVIDER}\n"
                f"✗  Invalid OTP.\n\n"
                f"<i>◌  Enter the 6-digit number (digits only).</i>"
            )

# ============== PROXY SETUP ==============
proxy_setup_done = False
def setup_proxy():
    global proxy_setup_done
    if proxy_setup_done:
        return
    # Priority: env var > UIDAI_PROXY constant > PROXY_POOL
    proxy_url = (os.environ.get('PROXY_URL', '') or UIDAI_PROXY).strip()
    if proxy_url:
        # Auto-convert IP:PORT:USER:PASS or IP:PORT format
        if not proxy_url.startswith(('http://', 'https://', 'socks5://', 'socks5h://')):
            parts = proxy_url.split(':')
            if len(parts) == 4:
                proxy_url = f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
            elif len(parts) == 2:
                proxy_url = f"http://{parts[0]}:{parts[1]}"
        try:
            parsed = urlparse(proxy_url)
            if parsed.scheme in ['http', 'https', 'socks5', 'socks5h']:
                PROXY_CONFIG['use_proxy'] = True
                PROXY_CONFIG['http'] = proxy_url
                PROXY_CONFIG['https'] = proxy_url
                print(f"Proxy: {proxy_url}")
            else:
                print("Invalid PROXY_URL scheme — running without proxy.")
        except Exception as e:
            print(f"Invalid PROXY_URL: {e} — running without proxy.")
    elif PROXY_POOL:
        # Use PROXY_POOL rotating proxies
        PROXY_CONFIG['use_proxy'] = True
        PROXY_CONFIG['http'] = PROXY_POOL[0]
        PROXY_CONFIG['https'] = PROXY_POOL[0]
        print(f"Proxy: SOCKS5 Pool ({len(PROXY_POOL)} proxies)")
    else:
        PROXY_CONFIG['use_proxy'] = False
        print("Proxy: off")
    # Invalidate any thread-local UIDAI sessions so they pick up the new proxy
    reset_uidai_session()
    proxy_setup_done = True

def check_uidai_connectivity():
    """Reachability test for tathya.uidai.gov.in:443.
    If proxy is configured, test through proxy. Otherwise direct TCP."""
    if PROXY_CONFIG.get('use_proxy') and PROXY_CONFIG.get('https'):
        try:
            r = get_uidai_session().get("https://tathya.uidai.gov.in/", timeout=10)
            return r.status_code < 500
        except Exception:
            return False
    else:
        import socket
        try:
            sock = socket.create_connection(("tathya.uidai.gov.in", 443), timeout=8)
            sock.close()
            return True
        except Exception:
            return False

# ============== GET UPDATES ==============
def get_updates(offset=None):
    url    = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    # timeout=5 keeps long-poll short so Ctrl+C exits within ~5 s
    params = {'timeout': 5, 'allowed_updates': ['message', 'callback_query']}
    if offset:
        params['offset'] = offset
    try:
        response = get_telegram_session().get(url, params=params, timeout=8)
        result   = response.json()
        if result.get('ok'):
            return result.get('result', [])
        else:
            # Telegram 409 Conflict = another instance polling with same token
            if result.get('error_code') == 409:
                return 'conflict'
            logger.error(f"Telegram API error: {result}")
            return []
    except Exception as e:
        logger.error(f"Error getting updates: {e}")
        return []

def process_update(update):
    try:
        # Get chat_id depending on update type
        cid = None
        if 'callback_query' in update:
            cid = update['callback_query']['message']['chat']['id']
        elif 'message' in update:
            cid = update['message']['chat']['id']

        # process update without global blocker to allow /buy, /referral and user reg

        if 'callback_query' in update:

            cq   = update['callback_query']
            cid  = cq['message']['chat']['id']
            cqid = cq['id']
            data = cq.get('data', '')
            msg_id = cq.get('message', {}).get('message_id')
            handle_callback(cid, cqid, data, msg_id, cq=cq)

        elif 'message' in update:
            msg  = update['message']
            if not msg:
                return
            cid  = msg['chat']['id']
            text = msg.get('text', msg.get('caption', '')).strip()
            photo = msg.get('photo')
            if not text and not photo:
                return

            if text.startswith('/start'):
                parts = text.split()
                referrer_id = None
                if len(parts) > 1 and parts[1].startswith('ref_'):
                    try:
                        referrer_id = int(parts[1][4:])
                    except ValueError:
                        pass

                if referrer_id:
                    update_session_data(cid, 'referrer_id', referrer_id)

                # Ensure user exists in DB
                is_new = ensure_user(
                    cid, referrer_id,
                    first_name=msg.get('from', {}).get('first_name'),
                    username=msg.get('from', {}).get('username')
                )
                clear_session(cid)
                
                # Channel gate — must join both channels
                if not channel_gate(cid):
                    return
                
                send_message(
                    cid,
                    f"<b>{BOT_NAME}</b>\n{DIVIDER}\n\n"
                    f"<b>e-Aadhaar PDF  —  straight to Telegram</b>\n\n"
                    f"◈  Source    ·  Official UIDAI portal\n"
                    f"◈  Delivery  ·  Auto-unlocked, no password\n"
                    f"◈  Methods   ·  Aadhaar  ·  Aadhaar 2  ·  PAN\n\n"
                    f"{DIVIDER}\n\n"
                    f"<i>◌  Select a service below to begin.</i>",
                    reply_markup=get_main_keyboard()
                )
            else:
                _from = msg.get('from', {})
                s = get_session(cid)
                referrer_id = s.get('data', {}).get('referrer_id')
                ensure_user(
                    cid,
                    referrer_id=referrer_id,
                    first_name=_from.get('first_name'),
                    username=_from.get('username')
                )
                handle_message(cid, msg)
    except Exception as e:
        logger.error(f"Error processing update: {e}")

# ============== DISABLE WINDOWS QUICK-EDIT MODE ==============
def disable_quick_edit():
    """Prevents Windows PowerShell/CMD from pausing the python process when user clicks terminal window."""
    if sys.platform == 'win32':
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            h_input = kernel32.GetStdHandle(-10) # STD_INPUT_HANDLE = -10
            mode = ctypes.c_ulong()
            if kernel32.GetConsoleMode(h_input, ctypes.byref(mode)):
                # 0x0040 = ENABLE_QUICK_EDIT_MODE, 0x0080 = ENABLE_EXTENDED_FLAGS
                new_mode = (mode.value & ~0x0040) | 0x0080
                kernel32.SetConsoleMode(h_input, new_mode)
        except Exception:
            pass

# ============== MAIN ==============
def main():
    disable_quick_edit()
    print("━" * 50)
    print(f"  {BOT_NAME}  —  starting up")
    print("━" * 50)

    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("[ error ] TELEGRAM_BOT_TOKEN not set.")
        return

    setup_proxy()

    try:
        r = get_telegram_session().get(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe", timeout=10
        )
        bot_info = r.json()
        if bot_info.get('ok'):
            _bot_username_val = bot_info['result']['username']
            global _bot_username
            _bot_username = _bot_username_val
            print(f"[ online ]  @{_bot_username_val}")
            proxy_display = f"SOCKS5 Pool ({len(PROXY_POOL)} IPs)" if PROXY_POOL else (PROXY_CONFIG['https'] if PROXY_CONFIG['use_proxy'] else 'off')
            print(f"[ proxy  ]  {proxy_display}")
            print(f"[ cracker]  PyPDF2 / 4 threads")
            print(f"[ credits]  system active")
            print(f"[ owners ]  {', '.join(map(str, OWNER_IDS))}")
            # ── UIDAI connectivity check ──────────────────────────────
            print("[ uidai  ]  checking…", end='', flush=True)
            if check_uidai_connectivity():
                print(" ✓ reachable")
            else:
                print(" ✗ UNREACHABLE")
                print("━" * 50)
                print("  WARNING: tathya.uidai.gov.in is not reachable!")
                print("  Captcha requests will fail until a proxy is set.")
                print("  Edit UIDAI_PROXY at the top of main.py and restart.")
                print("━" * 50)
        else:
            print(f"[ error ] Bot auth failed: {bot_info}")
            return
    except Exception as e:
        print(f"[ error ] {e}")
        return

    # Start session cleanup thread
    t = threading.Thread(target=_cleanup_sessions, daemon=True)
    t.start()

    # Start broadcast receiver thread
    threading.Thread(target=broadcast_receiver_thread, daemon=True, name="BroadcastReceiver").start()

    print("━" * 50)
    print("  running  —  Ctrl+C to stop")
    print("━" * 50)

    last_update_id = 0
    executor = ThreadPoolExecutor(max_workers=30)

    conflict_count = 0
    while True:
        try:
            updates = get_updates(last_update_id + 1)

            if updates == 'conflict':
                conflict_count += 1
                if conflict_count == 1:
                    print("\n[conflict] Another instance is using this bot token.")
                    print("[conflict] Waiting 30s for it to stop...")
                if conflict_count >= 6:
                    print("\n[conflict] Giving up — another instance is still running.")
                    print("[conflict] Kill the other instance and restart.")
                    break
                time.sleep(30)
                continue

            conflict_count = 0  # reset on success

            for update in updates:
                last_update_id = update.get('update_id')
                executor.submit(process_update, update)

            time.sleep(0.2)

        except KeyboardInterrupt:
            print("\n[ stopped ]  shutting down…")
            executor.shutdown(wait=False)   # don't wait for pending tasks
            break
        except Exception as e:
            logger.error(f"Main loop error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
