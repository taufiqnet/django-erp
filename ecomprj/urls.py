from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from core.sitemaps import ProductSitemap

sitemaps = {
    'products': ProductSitemap,
}


urlpatterns = [
    path('admin/', admin.site.urls),
    # path('', include('core.urls')),
    path('', include('website.urls')),
    path('sales/', include('sales.urls')),
    path('retail/', include('retail.urls')),
    path('pharmacy/', include('pharmacy.urls')),
    path('ecom/', include('ecom.urls')),
    path('hrm/', include('hrm.urls')),
    path('user/', include('userauths.urls')),

    path('tinymce/', include('tinymce.urls')),

    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
