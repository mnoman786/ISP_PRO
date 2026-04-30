"""
Run: python create_superuser.py
Creates the default admin account for ISP CRM.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'isp_crm.settings')
django.setup()

from accounts.models import User

username = 'admin'
password = 'admin123'
email = 'admin@isp.local'

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, password=password, email=email, role='admin')
    print(f"Superuser created: {username} / {password}")
else:
    print(f"User '{username}' already exists.")
