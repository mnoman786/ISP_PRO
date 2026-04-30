from django.contrib import admin
from .models import Area, Customer, Connection


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ['name', 'city']
    search_fields = ['name', 'city']


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'area', 'status', 'join_date']
    list_filter = ['status', 'area']
    search_fields = ['name', 'phone', 'cnic', 'email']


@admin.register(Connection)
class ConnectionAdmin(admin.ModelAdmin):
    list_display = ['username', 'customer', 'package', 'status', 'install_date', 'expiry_date']
    list_filter = ['status', 'connection_type']
    search_fields = ['username', 'customer__name', 'ip_address']
