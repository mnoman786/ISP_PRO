from django.db import models
from django.conf import settings


class Invoice(models.Model):
    STATUS_UNPAID = 'unpaid'
    STATUS_PAID = 'paid'
    STATUS_PARTIAL = 'partial'
    STATUS_OVERDUE = 'overdue'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_UNPAID, 'Unpaid'),
        (STATUS_PAID, 'Paid'),
        (STATUS_PARTIAL, 'Partial'),
        (STATUS_OVERDUE, 'Overdue'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    customer = models.ForeignKey('customers.Customer', on_delete=models.CASCADE, related_name='invoices')
    connection = models.ForeignKey('customers.Connection', on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    package = models.ForeignKey('packages.Package', on_delete=models.SET_NULL, null=True, blank=True)
    invoice_number = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    issue_date = models.DateField()
    due_date = models.DateField()
    billing_month = models.PositiveSmallIntegerField(null=True, blank=True)
    billing_year = models.PositiveSmallIntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_UNPAID)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"INV-{self.invoice_number} | {self.customer.name}"

    @property
    def balance(self):
        return self.total - self.paid_amount

    def save(self, *args, **kwargs):
        self.total = self.amount - self.discount + self.tax
        if not self.invoice_number:
            from django.utils import timezone
            now = timezone.now()
            last = Invoice.objects.order_by('-id').first()
            next_id = (last.id + 1) if last else 1
            self.invoice_number = f"{now.year}{now.month:02d}{next_id:04d}"
        super().save(*args, **kwargs)


class Payment(models.Model):
    METHOD_CASH = 'cash'
    METHOD_BANK = 'bank'
    METHOD_EASYPAISA = 'easypaisa'
    METHOD_JAZZCASH = 'jazzcash'
    METHOD_ONLINE = 'online'
    METHOD_OTHER = 'other'
    METHOD_CHOICES = [
        (METHOD_CASH, 'Cash'),
        (METHOD_BANK, 'Bank Transfer'),
        (METHOD_EASYPAISA, 'EasyPaisa'),
        (METHOD_JAZZCASH, 'JazzCash'),
        (METHOD_ONLINE, 'Online'),
        (METHOD_OTHER, 'Other'),
    ]

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default=METHOD_CASH)
    reference_no = models.CharField(max_length=100, blank=True)
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date']

    def __str__(self):
        return f"PKR {self.amount} for {self.invoice}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        invoice = self.invoice
        total_paid = sum(p.amount for p in invoice.payments.all())
        invoice.paid_amount = total_paid
        if total_paid >= invoice.total:
            invoice.status = Invoice.STATUS_PAID
        elif total_paid > 0:
            invoice.status = Invoice.STATUS_PARTIAL
        invoice.save()


class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('equipment', 'Equipment'),
        ('salary', 'Salary'),
        ('rent', 'Rent'),
        ('utilities', 'Utilities'),
        ('maintenance', 'Maintenance'),
        ('marketing', 'Marketing'),
        ('other', 'Other'),
    ]

    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='other')
    date = models.DateField()
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.title} - PKR {self.amount}"
