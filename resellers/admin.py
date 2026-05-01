from django.contrib import admin
from .models import Reseller, ResellerTransaction


@admin.register(Reseller)
class ResellerAdmin(admin.ModelAdmin):
    list_display = ['name', 'role', 'parent', 'balance', 'is_active', 'created_at']
    list_filter = ['role', 'is_active']
    search_fields = ['name', 'phone', 'email']


@admin.register(ResellerTransaction)
class ResellerTransactionAdmin(admin.ModelAdmin):
    list_display = ['reseller', 'type', 'amount', 'balance_after', 'note', 'created_at']
    list_filter = ['type']
    readonly_fields = ['created_at']
