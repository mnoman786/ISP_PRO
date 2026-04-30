@echo off
cd /d %~dp0
python manage.py expire_connections >> logs\expiry.log 2>&1
