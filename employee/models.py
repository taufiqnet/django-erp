from django.db import models
from business.models import Business
from django.utils.translation import gettext_lazy as _
from django.utils.html import mark_safe
from django.contrib.auth import get_user_model
from django.conf import settings
from django.urls import reverse
from shortuuid.django_fields import ShortUUIDField
import os
import random

User = get_user_model()  # Use custom User model if applicable

class Department(models.Model):
    did = ShortUUIDField(unique=True, length=10, max_length=30, prefix='dep', alphabet="abcdefgh12345")
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name='departments',
        verbose_name=_("Business"),
    )
    name = models.CharField(max_length=100, verbose_name=_('Department Name'))
    description = models.TextField(verbose_name=_('Description'), blank=True)
    active = models.BooleanField(default=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, editable=False, help_text="This field is automatically set to the logged-in user.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Department')
        verbose_name_plural = _('Departments')

    def __str__(self):
        return self.name
    

class Position(models.Model):
    pid = ShortUUIDField(unique=True, length=10, max_length=30, prefix='pos', alphabet="abcdefgh12345")
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name='positions',
        verbose_name=_("Business"),
    )
    name = models.CharField(max_length=100, verbose_name=_('Position'))
    description = models.TextField(verbose_name=_('Description'), blank=True)
    salary_grade = models.PositiveIntegerField(verbose_name=_('Salary Grade'), null=True, blank=True)
    active = models.BooleanField(default=True)

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, editable=False, help_text="This field is automatically set to the logged-in user.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Position')
        verbose_name_plural = _('Positions')

    def __str__(self):
        return self.name
    
class Employee(models.Model):
    GENDER_CHOICES = [
        ('M', _('Male')),
        ('F', _('Female')),
        ('O', _('Other')),
    ]

    EMPLOYMENT_STATUS_CHOICES = [
        ('active', _('Active')),
        ('terminated', _('Terminated')),
        ('on_leave', _('On Leave')),
        ('retired', _('Retired')),
    ]

    EMPLOYMENT_TYPE_CHOICES = [
        ('full_time', _('Full Time')),
        ('part_time', _('Part Time')),
        ('contract', _('Contract')),
        ('intern', _('Intern')),
    ]

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name='employee',
        verbose_name=_("Business"),
    )
    emp_no = models.CharField(max_length=10, verbose_name=_('Employee Number'), unique=True, help_text='Unique Employee ID')
    first_name = models.CharField(max_length=100, verbose_name=_('First Name'))
    last_name = models.CharField(max_length=100, verbose_name=_('Last Name'), null=True, blank=True)
    
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name=_('Gender'))
    date_of_birth = models.DateField(verbose_name=_('Date of Birth'), null=True, blank=True)
    email = models.EmailField(verbose_name=_('Email Address'), unique=True, blank=True, null=True)
    phone_number = models.CharField(max_length=15, verbose_name=_('Phone Number'), blank=True, null=True)
    address = models.TextField(verbose_name=_('Address'), blank=True, null=True)

    photo = models.ImageField(upload_to='employee_photos/', null=True, blank=True)

    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='departments', limit_choices_to={'active': True}, verbose_name=_('Department'))
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, related_name='positions', null=True, limit_choices_to={'active': True}, verbose_name=_('Position'))
    employment_status = models.CharField(max_length=20, choices=EMPLOYMENT_STATUS_CHOICES, default='active', verbose_name=_('Employment Status'))
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE_CHOICES, default='full_time', verbose_name=_('Employment Type'))

    hire_date = models.DateField(verbose_name=_('Hire Date'))
    termination_date = models.DateField(verbose_name=_('Termination Date'), blank=True, null=True)

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile', null=True, blank=True)    
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subordinates', verbose_name=_('Manager'))

    def __str__(self):
        # return f"{self.first_name} {self.last_name}"
        return f"{self.emp_no}-{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_active(self):
        return self.employment_status == 'active'
        
    def save(self, *args, **kwargs):
        if not self.emp_no:
            # Generate employee number if not provided
            self.emp_no = f"EMP{random.randint(1000, 9999)}"
        super().save(*args, **kwargs)
        
    def get_absolute_url(self):
        return reverse('employee_detail', kwargs={'pk': self.pk})
    

class EmployeeDetails(models.Model):
    MARITAL_STATUS_CHOICES = [
        ('single', _('Single')),
        ('married', _('Married')),
        ('divorced', _('Divorced')),
        ('widow', _('Widow')),
    ]
    
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]
    
    RELIGION_CHOICES = [
        ('islam', _('Islam')),
        ('hinduism', _('Hinduism')),
        ('buddhism', _('Buddhism')),
        ('christianity', _('Christianity')),
        ('others', _('Others')),
    ]

    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='details', to_field='emp_no')

    # Emergency Contacts
    emergency_contact = models.CharField(max_length=100, verbose_name=_('Emergency Contact Name'), blank=True)
    emergency_phone = models.CharField(max_length=15, verbose_name=_('Emergency Contact Phone'), blank=True)
    personal_notes = models.TextField(verbose_name=_('Personal Notes'), blank=True)
    additional_info = models.JSONField(verbose_name=_('Additional Information'), blank=True, null=True)

    father_name = models.CharField(max_length=100, verbose_name=_('Father\'s Name'), blank=True, null=True)
    mother_name = models.CharField(max_length=100, verbose_name=_('Mother\'s Name'), blank=True, null=True)
    spouse_name = models.CharField(max_length=100, verbose_name=_('Spouse Name'), blank=True, null=True)
    marital_status = models.CharField(max_length=10, choices=MARITAL_STATUS_CHOICES, verbose_name=_('Marital Status'), blank=True, null=True)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, verbose_name=_('Blood Group'), blank=True, null=True)
    religion = models.CharField(max_length=20, choices=RELIGION_CHOICES, verbose_name=_('Religion'), blank=True, null=True)
    nationality = models.CharField(max_length=50, verbose_name=_('Nationality'), blank=True, null=True)
    nid = models.CharField(max_length=20, verbose_name=_('National ID'), blank=True, null=True)
    mobile_office = models.CharField(max_length=15, verbose_name=_('Office Mobile Number'), blank=True, null=True)
    email_office = models.EmailField(verbose_name=_('Office Email Address'), blank=True, null=True)
    driving_license = models.CharField(max_length=20, verbose_name=_('Driving License'), blank=True, null=True)

    def __str__(self):
        return f"{self.employee.emp_no} - {self.employee.full_name}"
    


class Education(models.Model):
    employee_details = models.ForeignKey(EmployeeDetails, on_delete=models.CASCADE, related_name='educations', verbose_name=_('Employee'))
    institution = models.CharField(max_length=255, verbose_name=_('Institution'))
    degree = models.CharField(max_length=255, verbose_name=_('Degree'))
    field_of_study = models.CharField(max_length=255, verbose_name=_('Field of Study'))
    start_date = models.DateField(verbose_name=_('Start Date'))
    end_date = models.DateField(verbose_name=_('End Date'), null=True, blank=True)

    def __str__(self):
        return f"{self.degree} in {self.field_of_study} at {self.institution} for {self.employee_details.employee.emp_no}"
    

class Training(models.Model):
    employee_details = models.ForeignKey(EmployeeDetails, on_delete=models.CASCADE, related_name='trainings', verbose_name=_('Employee'))
    course_name = models.CharField(max_length=255, verbose_name=_('Course Name'))
    organization = models.CharField(max_length=255, verbose_name=_('Organization'))
    completion_date = models.DateField(verbose_name=_('Completion Date'))

    def __str__(self):
        return f"Training: {self.course_name} for {self.employee_details.employee.emp_no}"
    

class Certification(models.Model):
    employee_details = models.ForeignKey(EmployeeDetails, on_delete=models.CASCADE, related_name='certifications', verbose_name=_('Employee'))
    name = models.CharField(max_length=255, verbose_name=_('Certification Name'))
    issued_by = models.CharField(max_length=255, verbose_name=_('Issued By'))
    issue_date = models.DateField(verbose_name=_('Issue Date'))
    expiry_date = models.DateField(verbose_name=_('Expiry Date'), null=True, blank=True)

    def __str__(self):
        return f"Certification: {self.name} for {self.employee_details.employee.emp_no}"