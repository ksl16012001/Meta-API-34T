import os
from instagrapi import Client
import traceback
import requests

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
def main():
    print("🔐 INSTAGRAM LOGIN (TOTP 2FA)")
    username = "sjl04vohia"
    password = "zdk9svhhucq8weo"
    code = "LQ4M QSXS DUTV FBMB NFEY 32FD DOQG TR3K"
    otp=get_otp_token_from_code(code)
    cl = Client()

    try:
        print("\n🚀 Đang đăng nhập...")
        cl.login(username, password, verification_code=otp)
        print("✅ Đăng nhập thành công!")

        # Tạo thư mục nếu chưa tồn tại
        os.makedirs("Instagram/Session", exist_ok=True)
        session_path = f"Instagram/Session/{username}.json"
        cl.dump_settings(session_path)
        print(f"💾 Đã lưu session tại: {session_path}")

    except Exception as e:
        print("❌ Đăng nhập thất bại:")
        traceback.print_exc()

if __name__ == "__main__":
    main()
