import random
import string
import requests


from django.utils import timezone
from datetime import timedelta

def can_send_otp(user):
    now = timezone.now()

    # Reset count if expired (e.g., 1 hour window)
    if not user.otp_send_count_reset or now > user.otp_send_count_reset:
        user.otp_send_count = 0
        user.otp_send_count_reset = now + timedelta(hours=1)

    # Check cooldown (2 minutes between sends)
    if user.otp_last_sent and now < user.otp_last_sent + timedelta(minutes=2):
        return False, "Please wait before requesting another OTP."

    # Check max sends per hour (e.g., 3)
    if user.otp_send_count >= 3:
        return False, "You have reached the maximum OTP requests for this hour."

    return True, ""

def send_otp_with_rate_limit(user, api_token, sender_id):
    can_send, message = can_send_otp(user)
    if not can_send:
        return False, message

    otp = generate_otp()
    user.otp_code = otp
    user.otp_created_at = timezone.now()
    user.otp_last_sent = timezone.now()
    user.otp_send_count += 1
    user.save(update_fields=['otp_code', 'otp_created_at', 'otp_last_sent', 'otp_send_count', 'otp_send_count_reset'])

    sms_status = send_sms_jbd(user.phone_number, f"Your OTP is {otp}", api_token, sender_id)

    if sms_status == "SENT":
        return True, "OTP sent successfully."
    else:
        return False, "Failed to send OTP SMS."


def generate_otp(length=4):
    return ''.join(random.choices('0123456789', k=length))

def generate_password(length=8):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))



import logging

logger = logging.getLogger(__name__)

def send_sms_jbd(phone_number: str, message: str, api_token: str, sender_id: str = "YourName") -> str:
    url = "https://sms.jbdit.net/api/http/sms/send"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {
        "api_token": api_token,
        "recipient": phone_number,
        "sender_id": sender_id,
        "type": "plain",
        "message": message,
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()  # Raise exception for non-2xx responses
        result = response.json()

        # Check the result of the response
        if result.get("status") == "success":
            return "SENT"
        else:
            logger.error(f"Error response from SMS API: {result}")
            return f"FAILED: {result.get('error_message', 'Unknown error')}"
    except requests.RequestException as e:
        logger.error(f"Error in sending SMS: {e}")
        return f"FAILED: {e}"
    except ValueError as e:
        logger.error(f"Error parsing response: {e}")
        return f"FAILED: {e}"



from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect

def role_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated or getattr(user, 'role', None) not in allowed_roles:
                messages.error(request, "You are not authorized to access this page.")
                return redirect('index')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator