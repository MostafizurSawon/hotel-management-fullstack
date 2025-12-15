from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import (
    MiscPagesView,
    SiteSettingsUpdateView
)
from . import views

urlpatterns = [
    # Misc pages
    path("pages/misc/error/", MiscPagesView.as_view(template_name="pages_misc_error.html"), name="pages-misc-error"),
    path("pages/misc/under_maintenance/", MiscPagesView.as_view(template_name="pages_misc_under_maintenance.html"), name="pages-misc-under-maintenance"),
    path("pages/misc/comingsoon/", MiscPagesView.as_view(template_name="pages_misc_comingsoon.html"), name="pages-misc-comingsoon"),
    path("pages/misc/not_authorized/", MiscPagesView.as_view(template_name="pages_misc_not_authorized.html"), name="pages-misc-not-authorized"),


   

    # Site Settings
    path("site-settings/general", login_required(SiteSettingsUpdateView.as_view()), name="site_settings"),
    
]
