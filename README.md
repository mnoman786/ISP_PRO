# NetCRM — ISP Management System

A full-featured ISP CRM built with Django — an alternative to Zalpro ISP.

## Quick Start

```bash
pip install -r requirements.txt
python manage.py migrate
python create_superuser.py
python manage.py runserver
```

Open http://127.0.0.1:8000 and login with `admin` / `admin123`

## Features

| Module | Features |
|--------|----------|
| **Dashboard** | Stats, revenue chart, quick actions, recent activity |
| **Customers** | Full CRUD, search/filter, area management |
| **Connections** | PPPoE credentials, IP, MAC, expiry, OLT port |
| **Packages** | Internet plans with speed, price, data limits |
| **Billing** | Invoices, payments (Cash/EasyPaisa/JazzCash/Bank), expenses |
| **Network** | Routers, switches, OLTs, ONUs, IP pools |
| **Tickets** | Support tickets with priority, category, comments |
| **Staff** | Role-based access (Admin / Manager / Technician / Billing) |

## Staff Roles

- **Admin** — Full access including staff management
- **Manager** — All modules except staff create/delete
- **Technician** — Customers, connections, tickets, network
- **Billing Officer** — Invoices, payments, expenses

## Tech Stack

- Django 4.2 (LTS)
- Bootstrap 5.3
- Chart.js
- SQLite (switch to PostgreSQL for production)
