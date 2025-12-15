# apps/core/site_meta.py
from django.conf import settings
from django.apps import apps

def get_hotel_meta():
    """
    Returns (hotel_name, hotel_phone) from site_settings.SiteSettings if present.
    Fallback: settings.HOTEL_NAME / HOTEL_PHONE / JBD_SENDER_ID / "Your Hotel".
    """
    hotel_name = (
        getattr(settings, "HOTEL_NAME", None)
        or getattr(settings, "JBD_SENDER_ID", None)
        or "Your Hotel"
    )
    hotel_phone = getattr(settings, "HOTEL_PHONE", "")  # optional

    # Prefer plural SiteSettings; fall back to other common names
    Model = None
    for app_label, model_name in [
        ("site_settings", "SiteSettings"),
        ("site_settings", "SiteSetting"),
        ("site_settings", "Setting"),
    ]:
        try:
            Model = apps.get_model(app_label, model_name)
            if Model:
                break
        except Exception:
            continue

    if Model:
        try:
            obj = Model.objects.first()
            if obj:
                # Be liberal about field names
                name = (
                    getattr(obj, "name", None)
                    or getattr(obj, "site_name", None)
                    or getattr(obj, "title", None)
                )
                phone = (
                    getattr(obj, "phone", None)
                    or getattr(obj, "site_phone", None)
                    or getattr(obj, "site_settings_phone", None)
                )
                if name:
                    hotel_name = str(name).strip() or hotel_name
                if phone:
                    hotel_phone = str(phone).strip() or hotel_phone
        except Exception:
            pass

    return hotel_name, hotel_phone
