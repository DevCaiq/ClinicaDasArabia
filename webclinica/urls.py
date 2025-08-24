from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from clinica import views 
from clinica.admin import custom_admin_site

urlpatterns = [
    path('admin/dashboard/agendamentos-json/', views.admin_agendamentos_json, name='admin_agendamentos_json'),
    # Substitui admin.site.urls pela custom_admin_site.urls
    path('admin/', custom_admin_site.urls),
    path('', include('clinica.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
