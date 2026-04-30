from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    # Invoices
    path('', views.invoice_list, name='invoice_list'),
    path('invoices/add/', views.invoice_create, name='invoice_create'),
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<int:pk>/edit/', views.invoice_edit, name='invoice_edit'),
    path('invoices/<int:pk>/delete/', views.invoice_delete, name='invoice_delete'),
    # Payments
    path('payments/add/', views.payment_create, name='payment_create'),
    path('payments/<int:pk>/delete/', views.payment_delete, name='payment_delete'),
    # Expenses
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/add/', views.expense_create, name='expense_create'),
    path('expenses/<int:pk>/edit/', views.expense_edit, name='expense_edit'),
    path('expenses/<int:pk>/delete/', views.expense_delete, name='expense_delete'),
]
