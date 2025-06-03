from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now
from django.contrib.auth import get_user_model

User = get_user_model()

class Doctor(models.Model):
    # Basic Details
    first_name = models.CharField(
        max_length=100,
        verbose_name=_("First Name")
    )
    last_name = models.CharField(
        max_length=100,
        verbose_name=_("Last Name"), 
        null=True,
        blank=True
    )
    email = models.EmailField(
        unique=True,
        verbose_name=_("Email Address"),
        null=True,
        blank=True
    )
    phone = models.CharField(
        max_length=15,
        verbose_name=_("Phone Number")
    )
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Date of Birth")
    )
    gender_choices = [
        ('male', _("Male")),
        ('female', _("Female")),
        ('other', _("Other")),
    ]
    gender = models.CharField(
        max_length=10,
        choices=gender_choices,
        verbose_name=_("Gender")
    )
    address = models.TextField(
        verbose_name=_("Address")
    )

    # Professional Identification
    doctor_id = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_("Doctor ID")
    )
    license_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Medical License Number")
    )
    national_id = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name=_("National ID")
    )

    # Professional Information
    specialization_choices = [
        ('general', _("General Practitioner")),
        ('cardiology', _("Cardiology")),
        ('neurology', _("Neurology")),
        ('orthopedics', _("Orthopedics")),
        ('pediatrics', _("Pediatrics")),
        ('dermatology', _("Dermatology")),
        ('psychiatry', _("Psychiatry")),
        ('surgery', _("Surgery")),
        ('gynecology', _("Gynecology")),
        ('ophthalmology', _("Ophthalmology")),
        ('ent', _("ENT Specialist")),
        ('dentistry', _("Dentistry")),
        ('other', _("Other Specialty")),
    ]
    specialization = models.CharField(
        max_length=50,
        choices=specialization_choices,
        verbose_name=_("Specialization")
    )
    other_specialization = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_("Other Specialization (if selected)")
    )
    years_of_experience = models.PositiveIntegerField(
        verbose_name=_("Years of Experience")
    )
    qualifications = models.TextField(
        verbose_name=_("Qualifications (Degrees, Certifications)")
    )

    # Work Information
    hospital_name = models.CharField(
        max_length=200,
        verbose_name=_("Hospital/Clinic Name")
    )
    department = models.CharField(
        max_length=100,
        verbose_name=_("Department")
    )
    designation = models.CharField(
        max_length=100,
        verbose_name=_("Designation")
    )
    working_hours = models.CharField(
        max_length=100,
        verbose_name=_("Working Hours")
    )
    available_days = models.CharField(
        max_length=100,
        verbose_name=_("Available Days")
    )

    # Contact Information
    emergency_contact_name = models.CharField(
        max_length=100,
        verbose_name=_("Emergency Contact Name")
    )
    emergency_contact_phone = models.CharField(
        max_length=15,
        verbose_name=_("Emergency Contact Phone")
    )
    relationship_to_doctor = models.CharField(
        max_length=50,
        verbose_name=_("Relationship to Doctor")
    )

    # Professional Status
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active Status")
    )
    is_verified = models.BooleanField(
        default=False,
        verbose_name=_("Verified Status")
    )
    joining_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Joining Date")
    )

    # System Fields
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='doctor_profile',
        verbose_name=_("System User Account")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.doctor_id:  # Only generate ID for new doctors
            current_year_month = now().strftime("%Y%m")
            last_doctor = Doctor.objects.filter(doctor_id__startswith=f"D{current_year_month}").order_by('-doctor_id').first()
            if last_doctor:
                last_id_number = int(last_doctor.doctor_id[-4:])
                new_id_number = last_id_number + 1
            else:
                new_id_number = 1
            self.doctor_id = f"D{current_year_month}{new_id_number:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Dr. {self.first_name} {self.last_name} ({self.doctor_id})"

    class Meta:
        verbose_name = _("Doctor")
        verbose_name_plural = _("Doctors")
        indexes = [
            models.Index(fields=['doctor_id'], name='doctor_idx_doctor_id'),
            models.Index(fields=['email'], name='doctor_idx_email'),
            models.Index(fields=['phone'], name='doctor_idx_phone'),
            models.Index(fields=['specialization'], name='doctor_idx_specialization'),
        ]