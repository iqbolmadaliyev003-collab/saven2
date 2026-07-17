from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health(request):
    """Render health-check va deploy tekshiruvi uchun engil endpoint."""
    return JsonResponse({"status": "ok", "service": "saven-backend"})


urlpatterns = [
    path('', health, name='root-health'),
    path('api/v1/health/', health, name='health'),

    path('django-admin/', admin.site.urls),

    path('api/v1/', include('users.urls')),
    path('api/v1/', include('businesses.urls')),
    path('api/v1/', include('discounts.urls')),
    path('api/v1/', include('payments.urls')),
    path('api/v1/', include('notifications.urls')),
    path('api/v1/', include('analytics.urls')),
    path('api/v1/', include('transactions.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
