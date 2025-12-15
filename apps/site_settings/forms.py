# Site Settings

from django import forms
from .models import SiteSettings

class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Institution Name'}),
            'post': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Post Office'}),
            'upozilla': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Upazila'}),
            'district': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'District'}),
            'eiin': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'EIIN Number'}),
            'school_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'College Code'}),
            'established': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Established at'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'map_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Map Link URL'}),
            'img': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'favicon': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
