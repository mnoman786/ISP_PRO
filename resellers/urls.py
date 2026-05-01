from django.urls import path
from . import views

app_name = 'resellers'

urlpatterns = [
    path('', views.reseller_list, name='reseller_list'),
    path('add/', views.reseller_create, name='reseller_create'),
    path('<int:pk>/', views.reseller_detail, name='reseller_detail'),
    path('<int:pk>/edit/', views.reseller_edit, name='reseller_edit'),
    path('<int:pk>/delete/', views.reseller_delete, name='reseller_delete'),
    path('<int:pk>/credit/', views.reseller_credit, name='reseller_credit'),
    path('<int:pk>/transfer/', views.reseller_transfer, name='reseller_transfer'),
]
