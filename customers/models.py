from django.db import models
from django.conf import settings


class Area(models.Model):
    name = models.CharField(max_length=100)
    city = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Customer(models.Model):
    STATUS_ACTIVE = 'active'
    STATUS_INACTIVE = 'inactive'
    STATUS_SUSPENDED = 'suspended'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_INACTIVE, 'Inactive'),
        (STATUS_SUSPENDED, 'Suspended'),
    ]

    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    phone_alt = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    cnic = models.CharField(max_length=20, blank=True, verbose_name='CNIC/ID')
    address = models.TextField()
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True, related_name='customers')
    reseller = models.ForeignKey(
        'resellers.Reseller', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='customers',
        help_text='Franchise / Dealer / Sub-Dealer who owns this customer',
    )
    photo = models.ImageField(upload_to='customers/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    join_date = models.DateField(auto_now_add=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_active_connection(self):
        return self.connections.filter(status='active').first()


class Connection(models.Model):
    STATUS_ACTIVE = 'active'
    STATUS_INACTIVE = 'inactive'
    STATUS_SUSPENDED = 'suspended'
    STATUS_EXPIRED = 'expired'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_INACTIVE, 'Inactive'),
        (STATUS_SUSPENDED, 'Suspended'),
        (STATUS_EXPIRED, 'Expired'),
    ]

    TYPE_FIBER = 'fiber'
    TYPE_CABLE = 'cable'
    TYPE_WIRELESS = 'wireless'
    TYPE_CHOICES = [
        (TYPE_FIBER, 'Fiber'),
        (TYPE_CABLE, 'Cable'),
        (TYPE_WIRELESS, 'Wireless'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='connections')
    package = models.ForeignKey('packages.Package', on_delete=models.SET_NULL, null=True, related_name='connections')
    mikrotik_router = models.ForeignKey(
        'network.NetworkDevice',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='connections',
        verbose_name='MikroTik Router',
        help_text='Router that manages this PPPoE user',
        limit_choices_to={'is_mikrotik': True},
    )
    connection_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_FIBER)
    username = models.CharField(max_length=100, unique=True, help_text='PPPoE username')
    password = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    mac_address = models.CharField(max_length=17, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    install_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True)
    olt_port = models.CharField(max_length=50, blank=True, verbose_name='OLT/Device Port')
    static_ip = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.customer.name} — {self.username}"
