import random
import redis
import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
from urllib.parse import urlparse

# Load env variables from .env file
load_dotenv()

# --- Redis connection from environment variable ---
# Example: REDIS_URL=redis://redis:6379/0
redis_url = os.getenv("REDIS_URL")

parsed_url = urlparse(redis_url)
redis_host = parsed_url.hostname
redis_port = parsed_url.port or 6379
redis_db = int(parsed_url.path.lstrip("/") or 0)

redis_client = redis.StrictRedis(
    host=redis_host,
    port=redis_port,
    db=redis_db,
    decode_responses=True
)

def generate_otp(length=6):
    """Generate a random numeric OTP of given length."""
    otp = ''.join([str(random.randint(0, 9)) for _ in range(length)])
    return otp

def store_otp(email, otp, ttl=300):
    """
    Store OTP in Redis.
    """
    key = f"otp:{email}"
    redis_client.setex(key, ttl, otp)

def send_email_otp_gmail(receiver_email, otp):
    """
    Send OTP email using Gmail SMTP, credentials from environment.
    """
    gmail_user = os.getenv("GMAIL_USER")
    gmail_password = os.getenv("GMAIL_PASSWORD")

    msg = EmailMessage()
    msg['Subject'] = 'Your OTP Code'
    msg['From'] = gmail_user
    msg['To'] = receiver_email
    msg.set_content(f'Your OTP is {otp}. It is valid for 5 minutes.')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(gmail_user, gmail_password)
            smtp.send_message(msg)
            print(f"OTP sent successfully to {receiver_email}")
            return 200
    except Exception as e:
        print(f"Error sending OTP to {receiver_email}: {e}")
        return 500

def verify_otp(email, otp_to_check, delete_on_success=False):
    """
    Verify OTP stored in Redis.
    If delete_on_success is True, delete the OTP only when verified.
    """
    key = f"otp:{email}"
    stored_otp = redis_client.get(key)
    if stored_otp is None:
        print("OTP expired or not found")
        return False
    if stored_otp == otp_to_check:
        if delete_on_success:
            redis_client.delete(key)
        print("OTP verified successfully")
        return True
    else:
        print("Invalid OTP")
        return False
