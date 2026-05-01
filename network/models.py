from django.db import models


class NetworkDevice(models.Model):
    TYPE_ROUTER = 'router'
    TYPE_SWITCH = 'switch'
    TYPE_OLT = 'olt'
    TYPE_ONU = 'onu'
    TYPE_AP = 'ap'
    TYPE_OTHER = 'other'
    TYPE_CHOICES = [
        (TYPE_ROUTER, 'Router'),
        (TYPE_SWITCH, 'Switch'),
        (TYPE_OLT, 'OLT'),
        (TYPE_ONU, 'ONU'),
        (TYPE_AP, 'Access Point'),
        (TYPE_OTHER, 'Other'),
    ]

    STATUS_ONLINE = 'online'
    STATUS_OFFLINE = 'offline'
    STATUS_MAINTENANCE = 'maintenance'
    STATUS_CHOICES = [
        (STATUS_ONLINE, 'Online'),
        (STATUS_OFFLINE, 'Offline'),
        (STATUS_MAINTENANCE, 'Maintenance'),
    ]

    name = models.CharField(max_length=100)
    device_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_ROUTER)
    brand = models.CharField(max_length=100, blank=True)
    model_no = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    mac_address = models.CharField(max_length=17, blank=True)
    location = models.CharField(max_length=200, blank=True)
    area = models.ForeignKey('customers.Area', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ONLINE)
    install_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    # MikroTik API credentials (only relevant for routers)
    is_mikrotik = models.BooleanField(default=False, verbose_name='MikroTik Router')
    api_host = models.CharField(max_length=100, blank=True, verbose_name='API Host/IP',
                                help_text='IP address MikroTik API listens on (usually same as device IP)')
    api_port = models.PositiveIntegerField(default=8728, verbose_name='API Port',
                                           help_text='Default: 8728 (unencrypted) or 8729 (SSL)')
    api_username = models.CharField(max_length=100, blank=True, verbose_name='API Username')
    api_password = models.CharField(max_length=100, blank=True, verbose_name='API Password')
    api_use_ssl = models.BooleanField(default=False, verbose_name='Use SSL')
    radius_secret = models.CharField(
        max_length=100, blank=True, verbose_name='RADIUS Secret',
        help_text='Shared secret between this router and FreeRADIUS (NAS secret)',
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_device_type_display()})"

    def get_api_host(self):
        return self.api_host or str(self.ip_address or '')


class IPPool(models.Model):
    name = models.CharField(max_length=100)
    subnet = models.CharField(max_length=50, help_text='e.g. 192.168.1.0/24')
    gateway = models.GenericIPAddressField()
    dns_primary = models.GenericIPAddressField(default='8.8.8.8')
    dns_secondary = models.GenericIPAddressField(default='8.8.4.4', blank=True, null=True)
    area = models.ForeignKey('customers.Area', on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.subnet})"
