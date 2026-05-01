from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings
from .models import NetworkDevice, IPPool
from .forms import NetworkDeviceForm, IPPoolForm
from .mikrotik import test_connection, get_active_sessions, enable_pppoe_user, disable_pppoe_user
from radius.clients import add_or_update_client, remove_client


@login_required
def device_list(request):
    devices = NetworkDevice.objects.select_related('area').all()
    mikrotik_devices = devices.filter(is_mikrotik=True)
    return render(request, 'network/device_list.html', {
        'devices': devices,
        'mikrotik_devices': mikrotik_devices,
    })


@login_required
def device_create(request):
    if request.method == 'POST':
        form = NetworkDeviceForm(request.POST)
        if form.is_valid():
            device = form.save()
            if device.is_mikrotik:
                ok, msg = add_or_update_client(device)
                if not ok:
                    messages.warning(request, f'Device added but RADIUS clients.conf update failed: {msg}')
            messages.success(request, 'Device added.')
            return redirect('network:device_list')
    else:
        form = NetworkDeviceForm()
    return render(request, 'network/device_form.html', {'form': form, 'title': 'Add Device'})


@login_required
def device_edit(request, pk):
    device = get_object_or_404(NetworkDevice, pk=pk)
    if request.method == 'POST':
        form = NetworkDeviceForm(request.POST, instance=device)
        if form.is_valid():
            device = form.save()
            if device.is_mikrotik:
                ok, msg = add_or_update_client(device)
                if not ok:
                    messages.warning(request, f'Device updated but RADIUS clients.conf update failed: {msg}')
            messages.success(request, 'Device updated.')
            return redirect('network:device_list')
    else:
        form = NetworkDeviceForm(instance=device)
    return render(request, 'network/device_form.html', {'form': form, 'title': 'Edit Device', 'obj': device})


@login_required
def device_delete(request, pk):
    device = get_object_or_404(NetworkDevice, pk=pk)
    if request.method == 'POST':
        remove_client(device)
        device.delete()
        messages.success(request, 'Device deleted.')
        return redirect('network:device_list')
    return render(request, 'network/device_confirm_delete.html', {'obj': device})


@login_required
def device_detail(request, pk):
    device = get_object_or_404(NetworkDevice, pk=pk)
    sessions = []
    sessions_error = None
    if device.is_mikrotik:
        ok, result = get_active_sessions(device)
        if ok:
            sessions = result
        else:
            sessions_error = result
    connections = device.connections.select_related('customer', 'package').all()
    server_ip = request.get_host().split(':')[0]
    radius_secret = device.radius_secret or getattr(settings, 'RADIUS_DEFAULT_SECRET', 'testing123')
    return render(request, 'network/device_detail.html', {
        'device': device,
        'sessions': sessions,
        'sessions_error': sessions_error,
        'connections': connections,
        'server_ip': server_ip,
        'radius_secret': radius_secret,
    })


@login_required
@require_POST
def mikrotik_test(request, pk):
    """AJAX — test MikroTik API connection."""
    device = get_object_or_404(NetworkDevice, pk=pk, is_mikrotik=True)
    ok, msg = test_connection(device)
    return JsonResponse({'success': ok, 'message': msg})


@login_required
@require_POST
def mikrotik_user_enable(request, pk):
    """Enable a PPPoE user on a MikroTik device."""
    device = get_object_or_404(NetworkDevice, pk=pk, is_mikrotik=True)
    username = request.POST.get('username', '').strip()
    if not username:
        messages.error(request, 'Username is required.')
        return redirect('network:device_detail', pk=pk)
    ok, msg = enable_pppoe_user(device, username)
    if ok:
        messages.success(request, msg)
    else:
        messages.error(request, f'Failed: {msg}')
    return redirect('network:device_detail', pk=pk)


@login_required
@require_POST
def mikrotik_user_disable(request, pk):
    """Disable a PPPoE user on a MikroTik device."""
    device = get_object_or_404(NetworkDevice, pk=pk, is_mikrotik=True)
    username = request.POST.get('username', '').strip()
    if not username:
        messages.error(request, 'Username is required.')
        return redirect('network:device_detail', pk=pk)
    ok, msg = disable_pppoe_user(device, username)
    if ok:
        messages.success(request, msg)
    else:
        messages.error(request, f'Failed: {msg}')
    return redirect('network:device_detail', pk=pk)


# --- IP Pools ---

@login_required
def ippool_list(request):
    pools = IPPool.objects.select_related('area').all()
    return render(request, 'network/ippool_list.html', {'pools': pools})


@login_required
def ippool_create(request):
    if request.method == 'POST':
        form = IPPoolForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'IP Pool added.')
            return redirect('network:ippool_list')
    else:
        form = IPPoolForm()
    return render(request, 'network/ippool_form.html', {'form': form, 'title': 'Add IP Pool'})


@login_required
def ippool_edit(request, pk):
    pool = get_object_or_404(IPPool, pk=pk)
    if request.method == 'POST':
        form = IPPoolForm(request.POST, instance=pool)
        if form.is_valid():
            form.save()
            messages.success(request, 'IP Pool updated.')
            return redirect('network:ippool_list')
    else:
        form = IPPoolForm(instance=pool)
    return render(request, 'network/ippool_form.html', {'form': form, 'title': 'Edit IP Pool', 'obj': pool})


@login_required
def ippool_delete(request, pk):
    pool = get_object_or_404(IPPool, pk=pk)
    if request.method == 'POST':
        pool.delete()
        messages.success(request, 'IP Pool deleted.')
        return redirect('network:ippool_list')
    return render(request, 'network/ippool_confirm_delete.html', {'obj': pool})
