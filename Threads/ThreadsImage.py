import json
import requests
import asyncio
import time
from pymongo import MongoClient

# Load config
with open("Threads/config.json", encoding="utf-8") as f:
    config = json.load(f)

ACCESS_TOKEN = config["ACCESS_TOKEN"]
THREADS_USER_ID = config["THREADS_USER_ID"]
SUB_NAME = config["IDPOST"]
DB = config["DB"]

mongo_client = MongoClient(DB)
db = mongo_client.myVirtualDatabase
reddit_collection = db.reddit_posts

# === Create Threads container ===
def create_threads_container(caption: str, image_url: str = None):
    url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads"
    
    payload = {
        "media_type": "IMAGE" if image_url else "TEXT",
        "text": caption,
        "access_token": ACCESS_TOKEN
    }

    if image_url:
        payload["image_url"] = image_url

    response = requests.post(url, json=payload)
    response.raise_for_status()
    container_id = response.json().get("id")
    print(f"[✅] Media container created: {container_id}")
    return container_id

# === Wait until container is ready ===
def wait_for_container_ready(container_id, timeout=60):
    url = f"https://graph.threads.net/v1.0/{container_id}?access_token={ACCESS_TOKEN}"
    start_time = time.time()
    while True:
        response = requests.get(url)
        status = response.json().get("status", "UNKNOWN")
        print(f"[🧪] Trạng thái container: {status}")
        if status == "FINISHED":
            print("[✅] Container sẵn sàng để đăng.")
            return
        if time.time() - start_time > timeout:
            raise Exception("⏱ Quá thời gian chờ xử lý container.")
        time.sleep(5)

# === Publish Threads post ===
def publish_container(container_id):
    url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads_publish"
    payload = {
        "creation_id": container_id,
        "access_token": ACCESS_TOKEN
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    thread_id = response.json().get("id")
    print(f"[🎉] Thread published successfully! ID: {thread_id}")
    return thread_id

# === Posting flow ===
async def post_from_db(delay_seconds: int):
    posts = reddit_collection.find({"subreddit": SUB_NAME, "status": 0})
    for post in posts:
        title = post.get("Title", "").strip()
        content = post.get("content", "").strip()
        image_url = post.get("img", "").strip()

        if title.lower() == content.lower():
            content = ""

        caption = f"{title}\n\n{content}" if content else title

        try:
            container_id = create_threads_container(caption, image_url if image_url else None)

            wait_for_container_ready(container_id)
            publish_container(container_id)

            reddit_collection.update_one({"_id": post["_id"]}, {"$set": {"status": 1}})

            for remaining in range(delay_seconds, 0, -1):
                print(f"⏳ Chờ {remaining} giây trước bài tiếp theo...", end="\r")
                await asyncio.sleep(1)

        except Exception as e:
            print(f"[❌] Lỗi khi đăng: {e}")
            continue

# === Run ===
if __name__ == '__main__':
    try:
        user_delay = int(input("Nhập thời gian delay giữa các lần đăng (giây): ").strip())
        asyncio.run(post_from_db(user_delay))
    except ValueError:
        print("Vui lòng nhập một số nguyên hợp lệ.")
