from django.urls import path
from . import views

app_name = 'customers'

urlpatterns = [
    # Customers
    path('', views.customer_list, name='customer_list'),
    path('add/', views.customer_create, name='customer_create'),
    path('<int:pk>/', views.customer_detail, name='customer_detail'),
    path('<int:pk>/edit/', views.customer_edit, name='customer_edit'),
    path('<int:pk>/delete/', views.customer_delete, name='customer_delete'),
    # Connections
    path('connections/', views.connection_list, name='connection_list'),
    path('connections/add/', views.connection_create, name='connection_create'),
    path('<int:customer_pk>/connections/add/', views.connection_create, name='connection_create_for_customer'),
    path('connections/<int:pk>/edit/', views.connection_edit, name='connection_edit'),
    path('connections/<int:pk>/delete/', views.connection_delete, name='connection_delete'),
    # Areas
    path('areas/', views.area_list, name='area_list'),
    path('areas/add/', views.area_create, name='area_create'),
    path('areas/<int:pk>/edit/', views.area_edit, name='area_edit'),
    path('areas/<int:pk>/delete/', views.area_delete, name='area_delete'),
]
