import requests
import time

ACCESS_TOKEN = "THAARNGtCUQG5BUVJ0dmhCeHhLR281OFNWc0dKbTZA6S1RXRERVdmFmTkQ1cjRPWVNLbWRkR1h4dmVqUDNSOHpXUkMwUWdsRWZA0QUNzSnZAOWmIycUk2QVVwZA1VsbEpYMnc1NTRBZAFFPSmpLYmZAGMVAwdElTOS1tM09rMERtQ0QwanBEREk4b1ozQXF1ZAnpPeDVjVTZAsb0xhbXpwZAwZDZD"
THREADS_USER_ID = "29839080199016697"
VIDEO_URL = "https://cdn.pixabay.com/video/2024/08/16/226795_large.mp4"
TEXT = "📹 Bài đăng Threads kèm video từ API!"

# BƯỚC 1: Tạo container chứa video
def create_video_container():
    url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads"
    payload = {
        "media_type": "VIDEO",
        "video_url": VIDEO_URL,
        "text": TEXT,
        "domain": "THREADS",
        "access_token": ACCESS_TOKEN
    }

    print("[📤] Gửi yêu cầu tạo video container...")
    response = requests.post(url, json=payload)
    response.raise_for_status()
    container_id = response.json().get("id")
    print(f"[✅] Media container (video) created: {container_id}")
    return container_id

# BƯỚC 1.5: Kiểm tra trạng thái container
def wait_for_container_ready(container_id, timeout=1000):
    check_url = f"https://graph.threads.net/v1.0/{container_id}?access_token={ACCESS_TOKEN}"
    start_time = time.time()

    print("[⏳] Đang chờ container xử lý video...")
    while True:
        response = requests.get(check_url)
        data = response.json()
        status = data.get("status", "UNKNOWN")
        print(f"[🧪] Trạng thái container: {status}")

        if status == "FINISHED":
            print("[✅] Container đã sẵn sàng để publish.")
            return
        if time.time() - start_time > timeout:
            raise Exception("⏱ Hết thời gian chờ container sẵn sàng.")
        time.sleep(5)

# BƯỚC 2: Publish bài viết từ container
def publish_container(container_id):
    url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads_publish"
    payload = {
        "creation_id": container_id,
        "domain": "THREADS",
        "access_token": ACCESS_TOKEN
    }

    print("[📤] Gửi yêu cầu xuất bản thread...")
    response = requests.post(url, json=payload)
    response.raise_for_status()
    thread_id = response.json().get("id")
    print(f"[🎉] Thread with video published successfully! ID: {thread_id}")
    return thread_id

# Chạy chương trình
if __name__ == "__main__":
    try:
        container_id = create_video_container()
        wait_for_container_ready(container_id)
        publish_container(container_id)
    except requests.exceptions.RequestException as e:
        print("❌ Lỗi khi gọi API:", e)
        if hasattr(e.response, "text"):
            print("🪵 Thông báo chi tiết:", e.response.text)
    except Exception as ex:
        print("⚠️ Lỗi khác:", ex)
