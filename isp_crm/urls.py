from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls')),
    path('accounts/', include('accounts.urls')),
    path('customers/', include('customers.urls')),
    path('packages/', include('packages.urls')),
    path('billing/', include('billing.urls')),
    path('network/', include('network.urls')),
    path('tickets/', include('tickets.urls')),
    path('radius/', include('radius.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
