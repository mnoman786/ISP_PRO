from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.utils import timezone
from .models import Invoice, Payment, Expense
from .forms import InvoiceForm, PaymentForm, ExpenseForm
from network.mikrotik import enable_pppoe_user
from radius import service as radius


@login_required
def invoice_list(request):
    q = request.GET.get('q', '')
    status = request.GET.get('status', '')
    month = request.GET.get('month', '')
    year = request.GET.get('year', str(timezone.now().year))
    invoices = Invoice.objects.select_related('customer', 'package').all()
    if q:
        invoices = invoices.filter(Q(customer__name__icontains=q) | Q(invoice_number__icontains=q))
    if status:
        invoices = invoices.filter(status=status)
    if month:
        invoices = invoices.filter(billing_month=month)
    if year:
        invoices = invoices.filter(billing_year=year)
    total = invoices.aggregate(t=Sum('total'))['t'] or 0
    paid = invoices.filter(status='paid').aggregate(p=Sum('total'))['p'] or 0
    return render(request, 'billing/invoice_list.html', {
        'invoices': invoices, 'q': q, 'status': status,
        'month': month, 'year': year, 'total': total, 'paid': paid,
    })


@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    payments = invoice.payments.all()
    payment_form = PaymentForm(initial={'invoice': invoice, 'amount': invoice.balance})
    return render(request, 'billing/invoice_detail.html', {
        'invoice': invoice, 'payments': payments, 'payment_form': payment_form,
    })


@login_required
def invoice_create(request):
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.created_by = request.user
            invoice.save()
            messages.success(request, f'Invoice #{invoice.invoice_number} created.')
            return redirect('billing:invoice_detail', pk=invoice.pk)
    else:
        form = InvoiceForm()
    return render(request, 'billing/invoice_form.html', {'form': form, 'title': 'Create Invoice'})


@login_required
def invoice_edit(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == 'POST':
        form = InvoiceForm(request.POST, instance=invoice)
        if form.is_valid():
            form.save()
            messages.success(request, 'Invoice updated.')
            return redirect('billing:invoice_detail', pk=invoice.pk)
    else:
        form = InvoiceForm(instance=invoice)
    return render(request, 'billing/invoice_form.html', {'form': form, 'title': 'Edit Invoice', 'obj': invoice})


@login_required
def invoice_delete(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == 'POST':
        invoice.delete()
        messages.success(request, 'Invoice deleted.')
        return redirect('billing:invoice_list')
    return render(request, 'billing/invoice_confirm_delete.html', {'obj': invoice})


# --- Payments ---

@login_required
def payment_create(request):
    invoice_pk = request.GET.get('invoice') or request.POST.get('invoice')
    invoice = get_object_or_404(Invoice, pk=invoice_pk) if invoice_pk else None
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.received_by = request.user
            payment.save()
            messages.success(request, f'Payment of PKR {payment.amount} recorded.')
            # Auto-enable suspended/expired connection on payment
            inv = payment.invoice
            conn = inv.connection
            if conn and conn.status in ('suspended', 'expired'):
                conn.status = 'active'
                conn.save(update_fields=['status', 'updated_at'])
                # MikroTik
                if conn.mikrotik_router:
                    mt_ok, mt_msg = enable_pppoe_user(conn.mikrotik_router, conn.username)
                    if not mt_ok:
                        messages.warning(request, f'Payment recorded but MikroTik re-enable failed: {mt_msg}')
                # RADIUS
                r_ok, r_msg = radius.enable_user(conn)
                if not r_ok:
                    messages.warning(request, f'Payment recorded but RADIUS re-enable failed: {r_msg}')
                if (not conn.mikrotik_router or mt_ok if conn.mikrotik_router else True) and r_ok:
                    messages.success(request, f'Connection {conn.username} re-enabled.')
            return redirect('billing:invoice_detail', pk=payment.invoice.pk)
    else:
        initial = {'invoice': invoice, 'amount': invoice.balance if invoice else None}
        form = PaymentForm(initial=initial)
    return render(request, 'billing/payment_form.html', {'form': form, 'invoice': invoice})


@login_required
def payment_delete(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    invoice_pk = payment.invoice.pk
    if request.method == 'POST':
        payment.delete()
        # Recalculate paid_amount
        invoice = payment.invoice
        total_paid = sum(p.amount for p in invoice.payments.all())
        invoice.paid_amount = total_paid
        if total_paid >= invoice.total:
            invoice.status = Invoice.STATUS_PAID
        elif total_paid > 0:
            invoice.status = Invoice.STATUS_PARTIAL
        else:
            invoice.status = Invoice.STATUS_UNPAID
        invoice.save()
        messages.success(request, 'Payment deleted.')
        return redirect('billing:invoice_detail', pk=invoice_pk)
    return render(request, 'billing/payment_confirm_delete.html', {'obj': payment})


# --- Expenses ---

@login_required
def expense_list(request):
    expenses = Expense.objects.all()
    total = expenses.aggregate(t=Sum('amount'))['t'] or 0
    return render(request, 'billing/expense_list.html', {'expenses': expenses, 'total': total})


@login_required
def expense_create(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.created_by = request.user
            expense.save()
            messages.success(request, 'Expense added.')
            return redirect('billing:expense_list')
    else:
        form = ExpenseForm()
    return render(request, 'billing/expense_form.html', {'form': form, 'title': 'Add Expense'})


@login_required
def expense_edit(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense updated.')
            return redirect('billing:expense_list')
    else:
        form = ExpenseForm(instance=expense)
    return render(request, 'billing/expense_form.html', {'form': form, 'title': 'Edit Expense', 'obj': expense})


@login_required
def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Expense deleted.')
        return redirect('billing:expense_list')
    return render(request, 'billing/expense_confirm_delete.html', {'obj': expense})
