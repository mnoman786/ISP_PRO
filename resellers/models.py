from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


class Reseller(models.Model):
    ROLE_FRANCHISE = 'franchise'
    ROLE_DEALER = 'dealer'
    ROLE_SUBDEALER = 'subdealer'
    ROLE_CHOICES = [
        (ROLE_FRANCHISE, 'Franchise'),
        (ROLE_DEALER, 'Dealer'),
        (ROLE_SUBDEALER, 'Sub-Dealer'),
    ]

    name = models.CharField(max_length=200)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    parent = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='children',
        help_text='Leave blank for top-level franchise',
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='reseller_profile',
        help_text='Optional login account — reseller can log in and manage their own customers',
    )
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    area = models.ForeignKey(
        'customers.Area', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='resellers',
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['role', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_role_display()})"

    def can_afford(self, amount):
        return self.balance >= amount

    def credit(self, amount, note='', created_by=None):
        self.balance += amount
        self.save(update_fields=['balance', 'updated_at'])
        ResellerTransaction.objects.create(
            reseller=self,
            amount=amount,
            type='credit',
            note=note,
            balance_after=self.balance,
            created_by=created_by,
        )

    def debit(self, amount, note='', created_by=None):
        self.balance -= amount
        self.save(update_fields=['balance', 'updated_at'])
        ResellerTransaction.objects.create(
            reseller=self,
            amount=amount,
            type='debit',
            note=note,
            balance_after=self.balance,
            created_by=created_by,
        )

    def transfer_to(self, child, amount, created_by=None):
        if amount <= 0:
            raise ValidationError('Amount must be positive.')
        if not self.can_afford(amount):
            raise ValidationError(f'Insufficient balance. Available: PKR {self.balance}')
        if child.parent_id != self.pk:
            raise ValidationError('Can only transfer to your direct sub-resellers.')
        self.debit(amount, note=f'Transfer to {child.name}', created_by=created_by)
        child.credit(amount, note=f'Transfer from {self.name}', created_by=created_by)

    @property
    def customer_count(self):
        return self.customers.count()

    @property
    def children_count(self):
        return self.children.count()


class ResellerTransaction(models.Model):
    TYPE_CHOICES = [
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    ]

    reseller = models.ForeignKey(Reseller, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    note = models.CharField(max_length=255, blank=True)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reseller.name} {self.type} PKR {self.amount}"
