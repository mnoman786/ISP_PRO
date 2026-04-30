from django import forms
from .models import Ticket, TicketComment


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['customer', 'connection', 'subject', 'description', 'category',
                  'priority', 'status', 'assigned_to']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class TicketCommentForm(forms.ModelForm):
    class Meta:
        model = TicketComment
        fields = ['body']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Add a comment...'}),
        }
