from django.contrib import admin
from .models import Invoice, Payment, Expense


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'customer', 'total', 'paid_amount', 'status', 'due_date']
    list_filter = ['status', 'billing_month', 'billing_year']
    search_fields = ['invoice_number', 'customer__name']
    inlines = [PaymentInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'amount', 'method', 'payment_date', 'received_by']
    list_filter = ['method']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['title', 'amount', 'category', 'date']
    list_filter = ['category']
