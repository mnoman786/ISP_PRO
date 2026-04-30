from django.db import models


class Package(models.Model):
    TYPE_FIBER = 'fiber'
    TYPE_CABLE = 'cable'
    TYPE_WIRELESS = 'wireless'
    TYPE_CHOICES = [
        (TYPE_FIBER, 'Fiber'),
        (TYPE_CABLE, 'Cable'),
        (TYPE_WIRELESS, 'Wireless'),
    ]

    STATUS_ACTIVE = 'active'
    STATUS_INACTIVE = 'inactive'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_INACTIVE, 'Inactive'),
    ]

    name = models.CharField(max_length=100)
    package_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_FIBER)
    speed_download = models.PositiveIntegerField(help_text='Download speed in Mbps')
    speed_upload = models.PositiveIntegerField(help_text='Upload speed in Mbps')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.PositiveIntegerField(default=30, help_text='Billing cycle in days')
    data_limit_gb = models.PositiveIntegerField(null=True, blank=True, help_text='0 or blank = unlimited')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['price']

    def __str__(self):
        return f"{self.name} ({self.speed_download}/{self.speed_upload} Mbps)"

    @property
    def is_unlimited(self):
        return not self.data_limit_gb
