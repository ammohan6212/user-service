import random
import redis
import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

# Load env variables from .env file
load_dotenv()


redis_client = redis.StrictRedis(host="redis", port=6379, db=0, decode_responses=True)

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
    Send OTP email using Gmail SMTP.
    """
    gmail_user = "mohancloud9676@gmail.com"
    gmail_password = "bofjpfgnlezmqexu"

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

def verify_otp(email, otp_to_check):
    """
    Verify OTP stored in Redis.
    """
    key = f"otp:{email}"
    stored_otp = redis_client.get(key)
    if stored_otp is None:
        print("OTP expired or not found")
        return False
    if stored_otp == otp_to_check:
        redis_client.delete(key)
        print("OTP verified successfully")
        return True
    else:
        print("Invalid OTP")
        return False
