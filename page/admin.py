from django.contrib import admin
from .models import Banner, Ads, Campaign

@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'type', 'is_active',)
    list_editable = ('order', 'is_active')
    list_filter = ('type',)
    search_fields = ('title', 'description',)
    ordering = ('order',)


@admin.register(Ads)
class AdsAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'type', 'is_active',)
    list_editable = ('order', 'is_active')
    list_filter = ('type',)
    search_fields = ('title', 'description')
    ordering = ('order',)


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'type', 'is_active',)
    list_editable = ('order', 'is_active')
    list_filter = ('type',)
    search_fields = ('title', 'description')
    ordering = ('order',)