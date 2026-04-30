from django import forms
from .models import Customer, Connection, Area


class AreaForm(forms.ModelForm):
    class Meta:
        model = Area
        fields = ['name', 'city', 'description']


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'phone', 'phone_alt', 'email', 'cnic', 'address', 'area', 'photo', 'status', 'notes']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class ConnectionForm(forms.ModelForm):
    class Meta:
        model = Connection
        fields = [
            'customer', 'package', 'mikrotik_router', 'connection_type', 'username', 'password',
            'ip_address', 'mac_address', 'status', 'install_date', 'expiry_date',
            'area', 'olt_port', 'static_ip', 'notes',
        ]
        widgets = {
            'install_date': forms.DateInput(attrs={'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'password': forms.TextInput(),
        }
