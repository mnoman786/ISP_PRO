from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Customer, Connection, Area
from .forms import CustomerForm, ConnectionForm, AreaForm
from network.mikrotik import sync_connection, disable_pppoe_user, enable_pppoe_user
from radius import service as radius


@login_required
def customer_list(request):
    q = request.GET.get('q', '')
    status = request.GET.get('status', '')
    area = request.GET.get('area', '')
    customers = Customer.objects.select_related('area').all()
    if q:
        customers = customers.filter(Q(name__icontains=q) | Q(phone__icontains=q) | Q(cnic__icontains=q))
    if status:
        customers = customers.filter(status=status)
    if area:
        customers = customers.filter(area_id=area)
    areas = Area.objects.all()
    return render(request, 'customers/customer_list.html', {
        'customers': customers, 'areas': areas,
        'q': q, 'status': status, 'selected_area': area,
    })


@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    connections = customer.connections.select_related('package', 'area').all()
    invoices = customer.invoices.all()[:10]
    tickets = customer.tickets.all()[:10]
    return render(request, 'customers/customer_detail.html', {
        'customer': customer, 'connections': connections,
        'invoices': invoices, 'tickets': tickets,
    })


@login_required
def customer_create(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST, request.FILES)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.created_by = request.user
            customer.save()
            messages.success(request, f'Customer "{customer.name}" added successfully.')
            return redirect('customers:customer_detail', pk=customer.pk)
    else:
        form = CustomerForm()
    return render(request, 'customers/customer_form.html', {'form': form, 'title': 'Add Customer'})


@login_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        form = CustomerForm(request.POST, request.FILES, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Customer updated.')
            return redirect('customers:customer_detail', pk=customer.pk)
    else:
        form = CustomerForm(instance=customer)
    return render(request, 'customers/customer_form.html', {'form': form, 'title': 'Edit Customer', 'obj': customer})


@login_required
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        customer.delete()
        messages.success(request, 'Customer deleted.')
        return redirect('customers:customer_list')
    return render(request, 'customers/customer_confirm_delete.html', {'obj': customer})


# --- Connections ---

@login_required
def connection_list(request):
    q = request.GET.get('q', '')
    status = request.GET.get('status', '')
    connections = Connection.objects.select_related('customer', 'package', 'area').all()
    if q:
        connections = connections.filter(
            Q(username__icontains=q) | Q(customer__name__icontains=q) | Q(ip_address__icontains=q)
        )
    if status:
        connections = connections.filter(status=status)
    return render(request, 'customers/connection_list.html', {
        'connections': connections, 'q': q, 'status': status,
    })


@login_required
def connection_create(request, customer_pk=None):
    customer = get_object_or_404(Customer, pk=customer_pk) if customer_pk else None
    if request.method == 'POST':
        form = ConnectionForm(request.POST)
        if form.is_valid():
            connection = form.save()
            mt_ok, mt_msg = sync_connection(connection)
            r_ok, r_msg = radius.push_user(connection)
            if connection.mikrotik_router and not mt_ok:
                messages.warning(request, f'Connection saved but MikroTik sync failed: {mt_msg}')
            if not r_ok:
                messages.warning(request, f'Connection saved but RADIUS sync failed: {r_msg}')
            if (not connection.mikrotik_router or mt_ok) and r_ok:
                messages.success(request, 'Connection added and synced.')
            return redirect('customers:customer_detail', pk=connection.customer.pk)
    else:
        initial = {'customer': customer} if customer else {}
        form = ConnectionForm(initial=initial)
    return render(request, 'customers/connection_form.html', {
        'form': form, 'title': 'Add Connection', 'customer': customer,
    })


@login_required
def connection_edit(request, pk):
    connection = get_object_or_404(Connection, pk=pk)
    if request.method == 'POST':
        form = ConnectionForm(request.POST, instance=connection)
        if form.is_valid():
            connection = form.save()
            mt_ok, mt_msg = sync_connection(connection)
            r_ok, r_msg = radius.push_user(connection)
            if connection.mikrotik_router and not mt_ok:
                messages.warning(request, f'Connection updated but MikroTik sync failed: {mt_msg}')
            if not r_ok:
                messages.warning(request, f'Connection updated but RADIUS sync failed: {r_msg}')
            if (not connection.mikrotik_router or mt_ok) and r_ok:
                messages.success(request, 'Connection updated and synced.')
            return redirect('customers:customer_detail', pk=connection.customer.pk)
    else:
        form = ConnectionForm(instance=connection)
    return render(request, 'customers/connection_form.html', {
        'form': form, 'title': 'Edit Connection', 'obj': connection,
    })


@login_required
def connection_delete(request, pk):
    connection = get_object_or_404(Connection, pk=pk)
    customer_pk = connection.customer.pk
    if request.method == 'POST':
        radius.delete_user(connection.username)
        connection.delete()
        messages.success(request, 'Connection deleted.')
        return redirect('customers:customer_detail', pk=customer_pk)
    return render(request, 'customers/connection_confirm_delete.html', {'obj': connection})


# --- Areas ---

@login_required
def area_list(request):
    areas = Area.objects.all()
    return render(request, 'customers/area_list.html', {'areas': areas})


@login_required
def area_create(request):
    if request.method == 'POST':
        form = AreaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Area created.')
            return redirect('customers:area_list')
    else:
        form = AreaForm()
    return render(request, 'customers/area_form.html', {'form': form, 'title': 'Add Area'})


@login_required
def area_edit(request, pk):
    area = get_object_or_404(Area, pk=pk)
    if request.method == 'POST':
        form = AreaForm(request.POST, instance=area)
        if form.is_valid():
            form.save()
            messages.success(request, 'Area updated.')
            return redirect('customers:area_list')
    else:
        form = AreaForm(instance=area)
    return render(request, 'customers/area_form.html', {'form': form, 'title': 'Edit Area', 'obj': area})


@login_required
def area_delete(request, pk):
    area = get_object_or_404(Area, pk=pk)
    if request.method == 'POST':
        area.delete()
        messages.success(request, 'Area deleted.')
        return redirect('customers:area_list')
    return render(request, 'customers/area_confirm_delete.html', {'obj': area})
