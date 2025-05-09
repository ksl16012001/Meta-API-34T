import os
import json
import asyncio
from pymongo import MongoClient
import requests
from instagrapi import Client
from instagrapi.types import Location  # nếu bạn muốn thêm location
def get_otp_token_from_code(code: str) -> str:
    """
    Lấy OTP token từ mã 2FA (có thể chứa khoảng trắng) thông qua 2fa.live API.

    Args:
        code (str): Mã 2FA gồm 32 ký tự (có thể có khoảng trắng)

    Returns:
        str: Mã OTP nếu thành công, None nếu lỗi
    """
    clean_code = code.replace(" ", "")
    url = f"https://2fa.live/tok/{clean_code}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("token")
    except Exception as e:
        print(f"❌ Lỗi khi lấy token cho mã {code}: {e}")
        return None
# Load config
with open("Instagram/config.json", encoding="utf-8") as f:
    config = json.load(f)

SUB_NAME = config["IDPOST"]
DB = config["DB"]
mongo_client = MongoClient(DB)
db = mongo_client.myVirtualDatabase
reddit_collection = db.reddit_posts

# Khởi tạo và đăng nhập vào Instagram
cl = Client()
cl.load_settings("Instagram/session.json")

# === Posting flow ===
async def post_from_db_instagram(delay_seconds: int):
    posts = reddit_collection.find({"subreddit": SUB_NAME, "status": 0})

    for post in posts:
        title = post.get("Title", "").strip()
        content = post.get("content", "").strip()
        image_path = post.get("img", "").strip()

        if title.lower() == content.lower():
            content = ""

        caption = f"{title}\n\n{content}" if content else title

        try:
            if image_path and os.path.exists(image_path):
                media = cl.photo_upload(
                    path=image_path,
                    caption=caption,
                    extra_data = {
                        "share_to_threads": True,
                        "share_to_threads_destination_id": "17841465657779645",
                    }
                )
                print("✅ Đăng bài Instagram thành công!")
                print("🧪 Đã thử chia sẻ lên Threads (nếu Instagram hỗ trợ).")

            else:
                print("❌ Bỏ qua bài không có ảnh hoặc ảnh không tồn tại.")

            reddit_collection.update_one({"_id": post["_id"]}, {"$set": {"status": 1}})

            for remaining in range(delay_seconds, 0, -1):
                print(f"⏳ Chờ {remaining} giây trước bài tiếp theo...", end="\r")
                await asyncio.sleep(1)

        except Exception as e:
            print(f"[❌] Lỗi khi đăng Instagram: {e}")
            continue

asyncio.run(post_from_db_instagram(300))
