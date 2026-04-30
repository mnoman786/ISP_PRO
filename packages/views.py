from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Package
from .forms import PackageForm
from radius import service as radius


@login_required
def package_list(request):
    packages = Package.objects.all()
    return render(request, 'packages/package_list.html', {'packages': packages})


@login_required
def package_create(request):
    if request.method == 'POST':
        form = PackageForm(request.POST)
        if form.is_valid():
            package = form.save()
            radius.sync_package(package)
            messages.success(request, 'Package created.')
            return redirect('packages:package_list')
    else:
        form = PackageForm()
    return render(request, 'packages/package_form.html', {'form': form, 'title': 'Add Package'})


@login_required
def package_edit(request, pk):
    package = get_object_or_404(Package, pk=pk)
    if request.method == 'POST':
        form = PackageForm(request.POST, instance=package)
        if form.is_valid():
            package = form.save()
            radius.sync_package(package)
            messages.success(request, 'Package updated.')
            return redirect('packages:package_list')
    else:
        form = PackageForm(instance=package)
    return render(request, 'packages/package_form.html', {'form': form, 'title': 'Edit Package', 'obj': package})


@login_required
def package_delete(request, pk):
    package = get_object_or_404(Package, pk=pk)
    if request.method == 'POST':
        package.delete()
        messages.success(request, 'Package deleted.')
        return redirect('packages:package_list')
    return render(request, 'packages/package_confirm_delete.html', {'obj': package})
