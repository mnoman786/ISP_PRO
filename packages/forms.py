from django import forms
from .models import Package


class PackageForm(forms.ModelForm):
    class Meta:
        model = Package
        fields = ['name', 'package_type', 'speed_download', 'speed_upload', 'price',
                  'duration_days', 'data_limit_gb', 'status', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
