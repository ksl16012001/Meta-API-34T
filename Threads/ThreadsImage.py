import requests
import time
import json

with open("config.json", encoding="utf-8") as f:
    config = json.load(f)

ACCESS_TOKEN = config["ACCESS_TOKEN"]
THREADS_USER_ID = config["THREADS_USER_ID"]
IMAGE_URL = 'https://cdn-media.sforum.vn/storage/app/media/wp-content/uploads/2018/09/samsung-galaxy-s8-chong-nuoc.jpg'
TEXT = "Đây là bài viết thử nghiệm kèm ảnh từ Threads API 🚀"

# BƯỚC 1: Tạo Threads media container
def create_threads_container():
    url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads"
    params = {
        "media_type": "IMAGE",
        "image_url": IMAGE_URL,
        "text": TEXT,
        "access_token": ACCESS_TOKEN
    }
    response = requests.post(url, params=params)
    response.raise_for_status()
    container_id = response.json().get("id")
    print(f"[✅] Media container created: {container_id}")
    return container_id

# BƯỚC 2: Publish container sau 30 giây
def publish_container(container_id):
    print("[⏳] Chờ 30 giây để media container xử lý...")
    time.sleep(10)
    url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads_publish?creation_id={container_id}&access_token={ACCESS_TOKEN}"
    # params = {
    #     # "creation_id": container_id,
    #     "access_token": ACCESS_TOKEN
    # }
    response = requests.post(url)
    response.raise_for_status()
    thread_id = response.json().get("id")
    print(f"[🎉] Thread published successfully! ID: {thread_id}")
    return thread_id

if __name__ == "__main__":
    try:
        container_id = create_threads_container()
        publish_container(container_id)
    except requests.exceptions.RequestException as e:
        print("❌ Lỗi khi gọi API:", e)