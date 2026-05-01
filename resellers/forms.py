from django import forms
from .models import Reseller


class ResellerForm(forms.ModelForm):
    class Meta:
        model = Reseller
        fields = ['name', 'role', 'parent', 'user', 'phone', 'email', 'address', 'area', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent'].queryset = Reseller.objects.filter(is_active=True).exclude(role='subdealer')
        self.fields['parent'].empty_label = '— None (Top-Level Franchise) —'
        self.fields['user'].empty_label = '— No Login Account —'
        self.fields['area'].empty_label = '— Any Area —'

    def clean(self):
        cleaned = super().clean()
        role = cleaned.get('role')
        parent = cleaned.get('parent')
        if role == 'franchise' and parent:
            raise forms.ValidationError('A Franchise cannot have a parent.')
        if role in ('dealer', 'subdealer') and not parent:
            raise forms.ValidationError(f'A {role.title()} must have a parent.')
        if role == 'subdealer' and parent and parent.role != 'dealer':
            raise forms.ValidationError('A Sub-Dealer\'s parent must be a Dealer.')
        if role == 'dealer' and parent and parent.role != 'franchise':
            raise forms.ValidationError('A Dealer\'s parent must be a Franchise.')
        return cleaned


class CreditBalanceForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=12, decimal_places=2, min_value=1,
        widget=forms.NumberInput(attrs={'placeholder': '0.00', 'step': '0.01'}),
    )
    note = forms.CharField(
        max_length=255, required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Optional note (e.g. cash received)'}),
    )


class TransferBalanceForm(forms.Form):
    child = forms.ModelChoiceField(queryset=Reseller.objects.none(), label='Transfer To', empty_label='— Select —')
    amount = forms.DecimalField(
        max_digits=12, decimal_places=2, min_value=1,
        widget=forms.NumberInput(attrs={'placeholder': '0.00', 'step': '0.01'}),
    )
    note = forms.CharField(
        max_length=255, required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Optional note'}),
    )

    def __init__(self, *args, reseller=None, **kwargs):
        super().__init__(*args, **kwargs)
        if reseller:
            self.fields['child'].queryset = reseller.children.filter(is_active=True)
