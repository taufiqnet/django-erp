from django.contrib import admin
from .models import Doctor

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('doctor_id', 'first_name', 'last_name', 'specialization', 'hospital_name', 'is_active', 'is_verified')
    list_filter = ('specialization', 'is_active', 'is_verified')
    search_fields = ('doctor_id', 'first_name', 'last_name', 'email', 'license_number')
    ordering = ('-created_at',)
    # Read-only fields (for autogenerated fields)
    readonly_fields = ('doctor_id',)
    # fieldsets = (
    #     ('Basic Information', {
    #         'fields': ('first_name', 'last_name', 'date_of_birth', 'gender', 'user')
    #     }),
    #     ('Professional Information', {
    #         'fields': ('specialization', 'other_specialization', 'license_number', 'years_of_experience', 'qualifications')
    #     }),
    #     ('Work Information', {
    #         'fields': ('hospital_name', 'department', 'designation', 'working_hours', 'available_days')
    #     }),
    #     ('Status', {
    #         'fields': ('is_active', 'is_verified')
    #     })
    # )