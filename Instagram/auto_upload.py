import json
import os
import requests
import re
import asyncio
from pymongo import MongoClient
from instagrapi import Client

# === Load unified config ===
def load_config(config_path="Instagram/config.json"):
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)

# === Load session ===
def load_session_data(path):
    with open(path, encoding="utf-8") as f:
        session_data = json.load(f)
    sessionid = session_data["authorization_data"]["sessionid"]
    user_agent = session_data.get("user_agent", "Mozilla/5.0")
    return session_data, sessionid, user_agent

# === Trích FBID từ HTML ===
def fetch_fbid_using_session(sessionid, user_agent):
    url = "https://www.instagram.com/"
    headers = {
        "cookie": f"sessionid={sessionid};",
        "user-agent": user_agent,
        "referer": "https://www.instagram.com/",
        "x-ig-app-id": "936619743392459",
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9"
    }

    response = requests.get(url, headers=headers)
    if response.ok:
        match = re.search(r'"fbid":"(\d+)"', response.text)
        if match:
            return match.group(1)
    return None

# === Ghi FBID vào session file ===
def save_session_with_fbid(session_path, session_data, fbid):
    session_data["authorization_data"]["fbid"] = fbid
    with open(session_path, "w", encoding="utf-8") as f:
        json.dump(session_data, f, ensure_ascii=False, indent=2)

# === Thiết lập proxy cho client ===
def set_proxy_for_client(cl, raw_proxy):
    try:
        if raw_proxy.startswith("http://") or raw_proxy.startswith("socks5://"):
            cl.set_proxy(raw_proxy)
        else:
            parts = raw_proxy.replace("http://", "").replace("socks5://", "").split(":")
            if len(parts) == 4:
                user, password, ip, port = parts
                proxy_url = f"http://{user}:{password}@{ip}:{port}"
                cl.set_proxy(proxy_url)
            elif len(parts) == 2:
                ip, port = parts
                proxy_url = f"http://{ip}:{port}"
                cl.set_proxy(proxy_url)
            else:
                print(f"❌ Proxy không hợp lệ: {raw_proxy}")
                return
        print(f"✅ Proxy đã gán: {raw_proxy}")
    except Exception as e:
        print(f"❌ Gán proxy lỗi: {e}")

# === Đăng bài từ MongoDB ===
async def post_from_db(account_name, session_path, session_data, db_link, idpost, delay_seconds, fbid, proxy=None):
    mongo_client = MongoClient(db_link)
    db = mongo_client.myVirtualDatabase
    reddit_collection = db.reddit_posts

    cl = Client()

    # Gán proxy nếu có
    if proxy:
        set_proxy_for_client(cl, proxy)

    cl.load_settings(session_path)

    posts = reddit_collection.find({"subreddit": idpost, "status": 0})
    for post in posts:
        title = post.get("Title", "").strip()
        content = post.get("content", "").strip()
        image_path = post.get("img", "").strip()
        if title.lower() == content.lower():
            content = ""
        caption = f"{title}\n\n{content}" if content else title

        try:
            if image_path and os.path.exists(image_path):
                cl.photo_upload(
                    path=image_path,
                    caption=caption,
                    extra_data={
                        "share_to_threads": True,
                        "share_to_threads_destination_id": fbid
                    }
                )
                print(f"✅ [{account_name}] Đăng bài thành công")
            else:
                print(f"❌ [{account_name}] Thiếu ảnh, bỏ qua")
            reddit_collection.update_one({"_id": post["_id"]}, {"$set": {"status": 1}})
            for remaining in range(delay_seconds, 0, -1):
                print(f"[{account_name}] ⏳ Chờ {remaining}s...", end="\r")
                await asyncio.sleep(1)
        except Exception as e:
            print(f"[❌] [{account_name}] Lỗi khi đăng: {e}")

# === Main chạy nhiều tài khoản ===
async def run_all_accounts():
    config = load_config()
    db_link = config["DB"]
    accounts_config = config["accounts"]

    print("📋 Danh sách tài khoản sẽ xử lý:\n")
    for acc, data in accounts_config.items():
        if data.get("ENABLE_UPLOAD", 0) == 1:
            print(f"🟢 {acc} | Delay: {data.get('TIME_DELAY', 300)}s | IDPOST: {data.get('IDPOST')} | Session: {data.get('SESSION_PATH')}| PROXY: {data.get('PROXY')}")
        else:
            print(f"🔴 {acc} (BỎ QUA - ENABLE_UPLOAD: 0)")

    confirm = input("\n❓ Bạn có muốn bắt đầu đăng theo cấu hình trên? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ Đã hủy lệnh đăng.")
        return

    tasks = []
    for account_name, account_data in accounts_config.items():
        if account_data.get("ENABLE_UPLOAD", 0) != 1:
            continue

        session_path = account_data.get("SESSION_PATH")
        if not session_path or not os.path.exists(session_path):
            print(f"❌ Không tìm thấy session cho {account_name} tại {session_path}")
            continue

        session_data, sessionid, user_agent = load_session_data(session_path)
        fbid = session_data["authorization_data"].get("fbid")

        if not fbid:
            print(f"⚠️ Chưa có FBID cho {account_name}, đang trích...")
            fbid = fetch_fbid_using_session(sessionid, user_agent)
            if fbid:
                save_session_with_fbid(session_path, session_data, fbid)
            else:
                print(f"❌ Không lấy được FBID cho {account_name}")
                continue

        idpost = account_data.get("IDPOST", "")
        delay = int(account_data.get("TIME_DELAY", 300))
        proxy = account_data.get("PROXY", None)
        tasks.append(post_from_db(account_name, session_path, session_data, db_link, idpost, delay, fbid, proxy))

    await asyncio.gather(*tasks)

# === Chạy ===
asyncio.run(run_all_accounts())
