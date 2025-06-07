import random
import redis
import sendgrid
from sendgrid.helpers.mail import Mail


def generate_otp(length=6):
    """Generate a random numeric OTP of given length."""
    otp = ''.join([str(random.randint(0, 9)) for _ in range(length)])
    return otp

# Initialize Redis client
redis_client = redis.StrictRedis(host='redis', port=6379, db=0, decode_responses=True)

def store_otp(email, otp, ttl=300):
    """
    Store OTP in Redis.
    
    email: the user's email address
    otp: the OTP to store
    ttl: time-to-live in seconds (default 300 seconds = 5 minutes)
    """
    key = f"otp:{email}"
    redis_client.setex(key, ttl, otp)



def send_email_otp(email, otp):
    sg = sendgrid.SendGridAPIClient(api_key='5G.bofjpfgnlezmqexu')
    message = Mail(
        from_email='mohancloud9676@gmail.com',
        to_emails=email,
        subject='Your OTP Code',
        plain_text_content=f'Your OTP is {otp}. It is valid for 5 minutes.'
    )
    response = sg.send(message)
    return response.status_code

def verify_otp(email, otp_to_check):
    """
    Verify OTP stored in Redis.
    
    Returns True if valid, False otherwise.
    """
    key = f"otp:{email}"
    stored_otp = redis_client.get(key)
    if stored_otp is None:
        return False  # OTP expired or not found
    if stored_otp == otp_to_check:
        # Optionally delete OTP after successful verification
        redis_client.delete(key)
        return True
    else:
        return False


