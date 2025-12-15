import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)
JBD_URL = "https://sms.jbdit.net/api/http/sms/send"

def normalize_bd_mobile(mobile: str) -> str | None:
    """
    Returns local 01XXXXXXXXX (11 digits), or None.
    Accepts +8801XXXXXXXXX / 8801XXXXXXXXX / 01XXXXXXXXX.
    """
    if not mobile:
        return None
    m = str(mobile).strip().replace(' ', '')
    m = m.replace('+880', '').replace('880', '')
    if not m.startswith('0'):
        m = '0' + m
    return m if m.isdigit() and len(m) == 11 and m.startswith('01') else None

def send_sms_jbd(phone_number_local_01: str, message: str) -> str:
    """
    phone_number_local_01: 01XXXXXXXXX (11 digits) -> will send as 8801XXXXXXXXX
    Returns "SENT" or "FAILED: <reason>"
    """
    api_token = getattr(settings, "JBD_SMS_TOKEN", "")
    sender_id = getattr(settings, "JBD_SENDER_ID", "8809617615010")

    if not api_token:
        logger.info("JBD_SMS_TOKEN missing; skipping real send. Would send to %s: %s",
                    phone_number_local_01, message)
        return "SENT"  # টোকেন না থাকলে ফ্লো ব্লক না করতে চাইলে: pretend success

    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    payload = {
        "api_token": api_token,
        "recipient": f"880{phone_number_local_01[1:]}",
        "sender_id": sender_id,
        "type": "plain",
        "message": message,
    }

    try:
        r = requests.post(JBD_URL, json=payload, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        if str(data.get("status")).lower() == "success":
            return "SENT"
        logger.error("JBD API error: %s", data)
        return f"FAILED: {data.get('error_message', 'Unknown error')}"
    except requests.RequestException as e:
        logger.exception("JBD request error")
        return f"FAILED: {e}"
    except ValueError as e:
        logger.exception("JBD parse error")
        return f"FAILED: {e}"
