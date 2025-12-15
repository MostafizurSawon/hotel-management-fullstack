from .models import SmsLog

def log_sms(*, to: str, body: str, result: str, context: str, booking_id=None, provider="JBDSMS"):
    try:
        SmsLog.objects.create(
            to=to, body=body, result=str(result)[:200],
            context=context, booking_id=booking_id, provider=provider
        )
    except Exception:
        # never break your flow if logging fails
        pass
