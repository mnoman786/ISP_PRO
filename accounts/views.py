from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.contrib.auth.views import LoginView
from .models import User
from .forms import LoginForm, StaffCreateForm, StaffUpdateForm, ProfileUpdateForm


class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = 'accounts/login.html'


def logout_view(request):
    logout(request)
    return redirect('accounts:login')


@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully.')
            return redirect('accounts:profile')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {'form': form})


@login_required
def staff_list(request):
    if not request.user.is_manager:
        messages.error(request, 'Access denied.')
        return redirect('home:dashboard')
    staff = User.objects.all().order_by('username')
    return render(request, 'accounts/staff_list.html', {'staff': staff})


@login_required
def staff_create(request):
    if not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('home:dashboard')
    if request.method == 'POST':
        form = StaffCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Staff member created successfully.')
            return redirect('accounts:staff_list')
    else:
        form = StaffCreateForm()
    return render(request, 'accounts/staff_form.html', {'form': form, 'title': 'Add Staff'})


@login_required
def staff_edit(request, pk):
    if not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('home:dashboard')
    staff = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = StaffUpdateForm(request.POST, request.FILES, instance=staff)
        if form.is_valid():
            form.save()
            messages.success(request, 'Staff member updated.')
            return redirect('accounts:staff_list')
    else:
        form = StaffUpdateForm(instance=staff)
    return render(request, 'accounts/staff_form.html', {'form': form, 'title': 'Edit Staff', 'obj': staff})


@login_required
def staff_delete(request, pk):
    if not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('home:dashboard')
    staff = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        staff.delete()
        messages.success(request, 'Staff member deleted.')
        return redirect('accounts:staff_list')
    return render(request, 'accounts/staff_confirm_delete.html', {'obj': staff})
