from django.urls import path
from .views import NoAccessPage

app_name = "core"

urlpatterns = [
    path("no-access/", NoAccessPage.as_view(), name="no_access"),

]
