from django import forms
from .models import NetworkDevice, IPPool


class NetworkDeviceForm(forms.ModelForm):
    class Meta:
        model = NetworkDevice
        fields = [
            'name', 'device_type', 'brand', 'model_no', 'ip_address', 'mac_address',
            'location', 'area', 'status', 'install_date', 'notes',
            # MikroTik fields
            'is_mikrotik', 'api_host', 'api_port', 'api_username', 'api_password', 'api_use_ssl',
            'radius_secret',
        ]
        widgets = {
            'install_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'api_password': forms.PasswordInput(render_value=True),
        }


class IPPoolForm(forms.ModelForm):
    class Meta:
        model = IPPool
        fields = ['name', 'subnet', 'gateway', 'dns_primary', 'dns_secondary', 'area', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
