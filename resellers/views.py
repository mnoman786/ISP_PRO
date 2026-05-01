from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from .models import Reseller, ResellerTransaction
from .forms import ResellerForm, CreditBalanceForm, TransferBalanceForm


@login_required
def reseller_list(request):
    resellers = Reseller.objects.select_related('parent', 'area').all()
    total_balance = sum(r.balance for r in resellers)
    return render(request, 'resellers/reseller_list.html', {
        'resellers': resellers,
        'total_balance': total_balance,
    })


@login_required
def reseller_create(request):
    if request.method == 'POST':
        form = ResellerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Reseller added successfully.')
            return redirect('resellers:reseller_list')
    else:
        form = ResellerForm()
    return render(request, 'resellers/reseller_form.html', {'form': form, 'title': 'Add Reseller'})


@login_required
def reseller_edit(request, pk):
    reseller = get_object_or_404(Reseller, pk=pk)
    if request.method == 'POST':
        form = ResellerForm(request.POST, instance=reseller)
        if form.is_valid():
            form.save()
            messages.success(request, 'Reseller updated.')
            return redirect('resellers:reseller_detail', pk=pk)
    else:
        form = ResellerForm(instance=reseller)
    return render(request, 'resellers/reseller_form.html', {
        'form': form, 'title': 'Edit Reseller', 'obj': reseller,
    })


@login_required
def reseller_detail(request, pk):
    reseller = get_object_or_404(Reseller, pk=pk)
    transactions = reseller.transactions.select_related('created_by').order_by('-created_at')[:50]
    children = reseller.children.all()
    customers = reseller.customers.select_related('area').all()[:20]
    return render(request, 'resellers/reseller_detail.html', {
        'reseller': reseller,
        'transactions': transactions,
        'children': children,
        'customers': customers,
    })


@login_required
def reseller_credit(request, pk):
    reseller = get_object_or_404(Reseller, pk=pk)
    if request.method == 'POST':
        form = CreditBalanceForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            note = form.cleaned_data.get('note', '')
            reseller.credit(amount, note=note, created_by=request.user)
            messages.success(request, f'PKR {amount} credited to {reseller.name}. New balance: PKR {reseller.balance}')
            return redirect('resellers:reseller_detail', pk=pk)
    else:
        form = CreditBalanceForm()
    return render(request, 'resellers/reseller_credit.html', {'form': form, 'reseller': reseller})


@login_required
def reseller_transfer(request, pk):
    reseller = get_object_or_404(Reseller, pk=pk)
    if not reseller.children.exists():
        messages.warning(request, 'This reseller has no sub-resellers to transfer to.')
        return redirect('resellers:reseller_detail', pk=pk)
    if request.method == 'POST':
        form = TransferBalanceForm(request.POST, reseller=reseller)
        if form.is_valid():
            try:
                reseller.transfer_to(
                    form.cleaned_data['child'],
                    form.cleaned_data['amount'],
                    created_by=request.user,
                )
                messages.success(request, 'Balance transferred successfully.')
            except ValidationError as e:
                messages.error(request, e.message)
            return redirect('resellers:reseller_detail', pk=pk)
    else:
        form = TransferBalanceForm(reseller=reseller)
    return render(request, 'resellers/reseller_transfer.html', {'form': form, 'reseller': reseller})


@login_required
def reseller_delete(request, pk):
    reseller = get_object_or_404(Reseller, pk=pk)
    if request.method == 'POST':
        reseller.delete()
        messages.success(request, 'Reseller deleted.')
        return redirect('resellers:reseller_list')
    return render(request, 'resellers/reseller_confirm_delete.html', {'obj': reseller})
