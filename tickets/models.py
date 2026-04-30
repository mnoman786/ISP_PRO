from django.db import models
from django.conf import settings


class Ticket(models.Model):
    PRIORITY_LOW = 'low'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_HIGH = 'high'
    PRIORITY_CRITICAL = 'critical'
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, 'Low'),
        (PRIORITY_MEDIUM, 'Medium'),
        (PRIORITY_HIGH, 'High'),
        (PRIORITY_CRITICAL, 'Critical'),
    ]

    STATUS_OPEN = 'open'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_RESOLVED = 'resolved'
    STATUS_CLOSED = 'closed'
    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_RESOLVED, 'Resolved'),
        (STATUS_CLOSED, 'Closed'),
    ]

    CATEGORY_BILLING = 'billing'
    CATEGORY_TECHNICAL = 'technical'
    CATEGORY_INSTALLATION = 'installation'
    CATEGORY_SPEED = 'speed'
    CATEGORY_OTHER = 'other'
    CATEGORY_CHOICES = [
        (CATEGORY_BILLING, 'Billing'),
        (CATEGORY_TECHNICAL, 'Technical'),
        (CATEGORY_INSTALLATION, 'Installation'),
        (CATEGORY_SPEED, 'Speed Issue'),
        (CATEGORY_OTHER, 'Other'),
    ]

    ticket_number = models.CharField(max_length=20, unique=True, blank=True)
    customer = models.ForeignKey('customers.Customer', on_delete=models.CASCADE, related_name='tickets')
    connection = models.ForeignKey('customers.Connection', on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets')
    subject = models.CharField(max_length=300)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default=CATEGORY_TECHNICAL)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_tickets')
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"#{self.ticket_number} — {self.subject}"

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            from django.utils import timezone
            now = timezone.now()
            last = Ticket.objects.order_by('-id').first()
            next_id = (last.id + 1) if last else 1
            self.ticket_number = f"TKT{now.year}{next_id:04d}"
        super().save(*args, **kwargs)


class TicketComment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author} on {self.ticket}"
