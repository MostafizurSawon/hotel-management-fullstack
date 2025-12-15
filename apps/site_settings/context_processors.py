from .models import (
    SiteSettings
)



def global_site_data(request):
    return {
        'site_settings': SiteSettings.objects.first() or {},
    }
