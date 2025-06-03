from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now
from django.contrib.auth import get_user_model

User = get_user_model()  # Use custom User model if applicable

class Patient(models.Model):
    # Basic Details
    first_name = models.CharField(
        max_length=100, 
        verbose_name=_("First Name")
    )
    last_name = models.CharField(
        max_length=100, 
        null=True, 
        blank=True,
        verbose_name=_("Last Name")
    )
    email = models.EmailField(
        null=True, 
        blank=True, 
        verbose_name=_("Email Address")
    )
    phone = models.CharField(
        max_length=15, 
        null=True, 
        blank=True, 
        verbose_name=_("Phone Number")
    )
    date_of_birth = models.DateField(
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
        null=True, 
        blank=True, 
        verbose_name=_("Address")
    )

    # Identification
    patient_id = models.CharField(
        max_length=20, 
        unique=True, 
        verbose_name=_("Patient ID")
    )
    national_id = models.CharField(
        max_length=20, 
        null=True, 
        blank=True, 
        verbose_name=_("National ID")
    )

    # Personal Information
    father_name = models.CharField(
        max_length=100, 
        null=True, 
        blank=True, 
        verbose_name=_("Father's Name")
    )
    mother_name = models.CharField(
        max_length=100, 
        null=True, 
        blank=True, 
        verbose_name=_("Mother's Name")
    )
    spouse_name = models.CharField(
        max_length=100, 
        null=True, 
        blank=True, 
        verbose_name=_("Spouse's Name")
    )

    # Medical Details
    blood_group_choices = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]
    blood_group = models.CharField(
        max_length=3, 
        choices=blood_group_choices, 
        null=True, 
        blank=True, 
        verbose_name=_("Blood Group")
    )
    allergies = models.TextField(
        null=True, 
        blank=True, 
        verbose_name=_("Allergies")
    )
    chronic_conditions = models.TextField(
        null=True, 
        blank=True, 
        verbose_name=_("Chronic Conditions")
    )
    current_medications = models.TextField(
        null=True, 
        blank=True, 
        verbose_name=_("Current Medications")
    )

    # Emergency Contact
    emergency_contact_name = models.CharField(
        max_length=100, 
        null=True, 
        blank=True, 
        verbose_name=_("Emergency Contact Name")
    )
    emergency_contact_phone = models.CharField(
        max_length=15, 
        null=True, 
        blank=True, 
        verbose_name=_("Emergency Contact Phone")
    )
    relationship_to_patient = models.CharField(
        max_length=50, 
        null=True, 
        blank=True, 
        verbose_name=_("Relationship to Patient")
    )

    # Additional Information
    insurance_provider = models.CharField(
        max_length=100, 
        null=True, 
        blank=True, 
        verbose_name=_("Insurance Provider")
    )
    insurance_policy_number = models.CharField(
        max_length=50, 
        null=True, 
        blank=True, 
        verbose_name=_("Insurance Policy Number")
    )
    registration_date = models.DateTimeField(auto_now_add=True)

    last_updated = models.DateTimeField(
        auto_now=True, 
        verbose_name=_("Last Updated")
    )

    # Status
    is_active = models.BooleanField(
        default=True, 
        verbose_name=_("Active Status")
    )

    user = models.ForeignKey(User, on_delete=models.SET_NULL, 
        null=True, blank=True, editable=False, help_text="This field is automatically set to the logged-in user.")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.patient_id:  # Only generate ID for new patients
            current_year_month = now().strftime("%Y%m")
            last_patient = Patient.objects.filter(patient_id__startswith=f"P{current_year_month}").order_by('-patient_id').first()
            if last_patient:
                last_id_number = int(last_patient.patient_id[-4:])
                new_id_number = last_id_number + 1
            else:
                new_id_number = 1
            self.patient_id = f"P{current_year_month}{new_id_number:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name} (ID: {self.patient_id})"

    class Meta:
        verbose_name = _("Patient")
        verbose_name_plural = _("Patients")
        indexes = [
            models.Index(fields=['patient_id'], name='patient_idx_patient_id'),
            models.Index(fields=['email'], name='patient_idx_email'),
            models.Index(fields=['phone'], name='patient_idx_phone'),
        ]
