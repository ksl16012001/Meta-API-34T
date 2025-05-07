import json
import requests
import asyncio
import io
import random
from PIL import ImageFont, ImageDraw, Image
from pymongo import MongoClient

# Load config
with open("config.json", encoding="utf-8") as f:
    config = json.load(f)

ACCESS_TOKEN = config["ACCESS_TOKEN"]
PAGE_ID = config["PAGE_ID"]
SUB_NAME = config["sub"]

mongo_client = MongoClient("mongodb+srv://admin:Nhincaigi1!@cluster0.vvqguzg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = mongo_client.myVirtualDatabase
reddit_collection = db.reddit_posts

# === Image Posting Function ===
def post_image_to_facebook(page_id: str, access_token: str, image_bytes: io.BytesIO, caption: str):
    url = f"https://graph.facebook.com/v19.0/{page_id}/photos"
    files = {'source': ('image.jpg', image_bytes, 'image/jpeg')}
    data = {'access_token': access_token, 'message': caption}
    response = requests.post(url, files=files, data=data)
    if response.status_code != 200:
        raise Exception(f"Image post failed: {response.status_code} - {response.text}")
    print("Image posted successfully.")

# === Helper to load and resize image for upload ===
def load_image_as_bytes(image_path):
    with open(image_path, 'rb') as img_file:
        image_buffer = io.BytesIO(img_file.read())
    return image_buffer

# === Posting flow ===
async def post_from_db(delay_seconds: int):
    posts = reddit_collection.find({"subreddit": SUB_NAME, "status": 0})

    for post in posts:
        title = post.get("Title", "")
        content = post.get("content", "")
        image_path = post.get("img", "")

        if not image_path or not image_path.strip():
            print("Skipping post without image")
            continue

        try:
            caption = f"{title}\n\n{content}" if content else title
            image_bytes = load_image_as_bytes(image_path)
            post_image_to_facebook(PAGE_ID, ACCESS_TOKEN, image_bytes, caption)
            reddit_collection.update_one({"_id": post["_id"]}, {"$set": {"status": 1}})
            await asyncio.sleep(delay_seconds)
        except Exception as e:
            print(f"Failed to post: {e}")
            continue

# === Run ===
if __name__ == '__main__':
    try:
        user_delay = int(input("Nhập thời gian delay giữa các lần đăng (giây): ").strip())
        asyncio.run(post_from_db(user_delay))
    except ValueError:
        print("Vui lòng nhập một số nguyên hợp lệ.")
