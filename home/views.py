from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.utils import timezone
from customers.models import Customer, Connection
from billing.models import Invoice, Payment
from tickets.models import Ticket


@login_required
def dashboard(request):
    today = timezone.now().date()
    this_month = today.month
    this_year = today.year

    # Customer stats
    total_customers = Customer.objects.count()
    active_customers = Customer.objects.filter(status='active').count()
    new_this_month = Customer.objects.filter(join_date__month=this_month, join_date__year=this_year).count()

    # Connection stats
    active_connections = Connection.objects.filter(status='active').count()
    expiring_soon = Connection.objects.filter(
        status='active',
        expiry_date__range=(today, today + timezone.timedelta(days=7))
    ).count()

    # Billing stats
    monthly_invoices = Invoice.objects.filter(billing_month=this_month, billing_year=this_year)
    monthly_revenue = monthly_invoices.aggregate(t=Sum('total'))['t'] or 0
    monthly_collected = monthly_invoices.filter(status='paid').aggregate(p=Sum('total'))['p'] or 0
    unpaid_invoices = Invoice.objects.filter(status__in=['unpaid', 'partial', 'overdue']).count()
    overdue_invoices = Invoice.objects.filter(status='overdue').count()

    # Ticket stats
    open_tickets = Ticket.objects.filter(status__in=['open', 'in_progress']).count()
    critical_tickets = Ticket.objects.filter(status__in=['open', 'in_progress'], priority='critical').count()

    # Recent activity
    recent_customers = Customer.objects.order_by('-created_at')[:5]
    recent_invoices = Invoice.objects.select_related('customer').order_by('-created_at')[:5]
    recent_tickets = Ticket.objects.select_related('customer').order_by('-created_at')[:5]

    # Monthly revenue chart (last 6 months)
    chart_labels = []
    chart_data = []
    for i in range(5, -1, -1):
        month_offset = (today.month - i - 1) % 12 + 1
        year_offset = today.year - ((i - today.month + 1) // 12 + (1 if (i - today.month + 1) % 12 > 0 else 0))
        if today.month - i <= 0:
            year_offset = today.year - 1
            month_offset = today.month - i + 12
        else:
            year_offset = today.year
            month_offset = today.month - i
        rev = Invoice.objects.filter(
            billing_month=month_offset, billing_year=year_offset, status='paid'
        ).aggregate(t=Sum('total'))['t'] or 0
        import calendar
        chart_labels.append(calendar.month_abbr[month_offset])
        chart_data.append(float(rev))

    context = {
        'total_customers': total_customers,
        'active_customers': active_customers,
        'new_this_month': new_this_month,
        'active_connections': active_connections,
        'expiring_soon': expiring_soon,
        'monthly_revenue': monthly_revenue,
        'monthly_collected': monthly_collected,
        'unpaid_invoices': unpaid_invoices,
        'overdue_invoices': overdue_invoices,
        'open_tickets': open_tickets,
        'critical_tickets': critical_tickets,
        'recent_customers': recent_customers,
        'recent_invoices': recent_invoices,
        'recent_tickets': recent_tickets,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
    }
    return render(request, 'home/dashboard.html', context)
