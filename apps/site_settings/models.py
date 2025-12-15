from django.db import models

class SiteSettings(models.Model):
    name = models.CharField(max_length=150, null=True, blank=True)
    post = models.CharField(max_length=40, null=True, blank=True)
    upozilla = models.CharField(max_length=50, null=True, blank=True)
    district = models.CharField(max_length=50, null=True, blank=True)

    img = models.ImageField(upload_to='site_settings/', blank=True, null=True, verbose_name="site_header_image")

    code = models.CharField(max_length=10, null=True, blank=True)
    established = models.CharField(max_length=10, null=True, blank=True)

    # Link to MediaFiles by category (one per category)
    logo = models.ImageField(upload_to='site_settings/logo_fav/', blank=True, null=True, verbose_name="site_logo")
    favicon = models.ImageField(upload_to='site_settings/logo_fav/', blank=True, null=True, verbose_name="site_fav")


    # Contact Info
    phone = models.CharField(max_length=18, blank=True, null=True)
    whatsapp = models.CharField(max_length=18,blank=True,null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    map_link = models.URLField(null=True, blank=True)

    # Footer Info
    footer = models.CharField(max_length=255, blank=True)
    footer_description = models.CharField(max_length=255, blank=True)

    # Social Links
    facebook = models.URLField(blank=True, null=True)
    instagram = models.URLField(blank=True, null=True)
    youtube = models.URLField(blank=True, null=True)
    x = models.URLField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name or "Site Settings"
