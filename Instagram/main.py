import os
import json
import asyncio
from pymongo import MongoClient
from instagrapi import Client

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
cl.load_settings("sessionjohndoe121212a.json")

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
                cl.photo_upload(image_path, caption)
                print("Đăng bài Instagram thành công!")
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
