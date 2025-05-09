import requests

code = "LQ4M QSXS DUTV FBMB NFEY 32FD DOQG TR3K"
url = f"https://2fa.live/tok/{code}"

response = requests.get(url)
try:
    data = response.json()
    token = data.get("token")
    print(f"✅ Token: {token}")
except Exception as e:
    print(f"❌ Lỗi khi parse JSON: {e}")
    print(response.text)
