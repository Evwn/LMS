from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('course/', include('course.urls')),
    path('quiz/', include('quiz.urls')),
    path('analytics/', include('analytics.urls')),
    path('', include('django_prometheus.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 