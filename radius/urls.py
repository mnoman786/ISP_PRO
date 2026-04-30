from django.urls import path
from . import views

app_name = 'radius'

urlpatterns = [
    path('sessions/', views.sessions_list, name='sessions'),
    path('sessions/<str:username>/', views.user_sessions, name='user_sessions'),
]
