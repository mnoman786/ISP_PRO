from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_ADMIN = 'admin'
    ROLE_MANAGER = 'manager'
    ROLE_TECHNICIAN = 'technician'
    ROLE_BILLING = 'billing'
    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Admin'),
        (ROLE_MANAGER, 'Manager'),
        (ROLE_TECHNICIAN, 'Technician'),
        (ROLE_BILLING, 'Billing Officer'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_BILLING)
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN or self.is_superuser

    @property
    def is_manager(self):
        return self.role in (self.ROLE_ADMIN, self.ROLE_MANAGER) or self.is_superuser
