from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from .models import Ticket, TicketComment
from .forms import TicketForm, TicketCommentForm


@login_required
def ticket_list(request):
    q = request.GET.get('q', '')
    status = request.GET.get('status', '')
    priority = request.GET.get('priority', '')
    category = request.GET.get('category', '')
    tickets = Ticket.objects.select_related('customer', 'assigned_to').all()
    if q:
        tickets = tickets.filter(Q(subject__icontains=q) | Q(customer__name__icontains=q) | Q(ticket_number__icontains=q))
    if status:
        tickets = tickets.filter(status=status)
    if priority:
        tickets = tickets.filter(priority=priority)
    if category:
        tickets = tickets.filter(category=category)
    return render(request, 'tickets/ticket_list.html', {
        'tickets': tickets, 'q': q, 'status': status, 'priority': priority, 'category': category,
    })


@login_required
def ticket_detail(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    comments = ticket.comments.select_related('author').all()
    comment_form = TicketCommentForm()
    if request.method == 'POST':
        comment_form = TicketCommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.ticket = ticket
            comment.author = request.user
            comment.save()
            messages.success(request, 'Comment added.')
            return redirect('tickets:ticket_detail', pk=pk)
    return render(request, 'tickets/ticket_detail.html', {
        'ticket': ticket, 'comments': comments, 'comment_form': comment_form,
    })


@login_required
def ticket_create(request):
    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.created_by = request.user
            ticket.save()
            messages.success(request, f'Ticket #{ticket.ticket_number} created.')
            return redirect('tickets:ticket_detail', pk=ticket.pk)
    else:
        form = TicketForm()
    return render(request, 'tickets/ticket_form.html', {'form': form, 'title': 'Open Ticket'})


@login_required
def ticket_edit(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    if request.method == 'POST':
        form = TicketForm(request.POST, instance=ticket)
        if form.is_valid():
            ticket = form.save()
            if ticket.status == Ticket.STATUS_RESOLVED and not ticket.resolved_at:
                ticket.resolved_at = timezone.now()
                ticket.save()
            messages.success(request, 'Ticket updated.')
            return redirect('tickets:ticket_detail', pk=ticket.pk)
    else:
        form = TicketForm(instance=ticket)
    return render(request, 'tickets/ticket_form.html', {'form': form, 'title': 'Edit Ticket', 'obj': ticket})


@login_required
def ticket_delete(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    if request.method == 'POST':
        ticket.delete()
        messages.success(request, 'Ticket deleted.')
        return redirect('tickets:ticket_list')
    return render(request, 'tickets/ticket_confirm_delete.html', {'obj': ticket})
