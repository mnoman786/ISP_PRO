from django.urls import path
from . import views

app_name = 'network'

urlpatterns = [
    path('', views.device_list, name='device_list'),
    path('add/', views.device_create, name='device_create'),
    path('<int:pk>/', views.device_detail, name='device_detail'),
    path('<int:pk>/edit/', views.device_edit, name='device_edit'),
    path('<int:pk>/delete/', views.device_delete, name='device_delete'),
    # MikroTik actions
    path('<int:pk>/test/', views.mikrotik_test, name='mikrotik_test'),
    path('<int:pk>/enable-user/', views.mikrotik_user_enable, name='mikrotik_user_enable'),
    path('<int:pk>/disable-user/', views.mikrotik_user_disable, name='mikrotik_user_disable'),
    # IP Pools
    path('ip-pools/', views.ippool_list, name='ippool_list'),
    path('ip-pools/add/', views.ippool_create, name='ippool_create'),
    path('ip-pools/<int:pk>/edit/', views.ippool_edit, name='ippool_edit'),
    path('ip-pools/<int:pk>/delete/', views.ippool_delete, name='ippool_delete'),
]
