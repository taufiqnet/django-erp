from django.contrib import admin
from .models import ChartOfAccount, Journal, GeneralLedger, TrialBalance

# Chart of Accounts Admin
@admin.register(ChartOfAccount)
class ChartOfAccountAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'type', 'parent_account')  # Fields to display in the list view
    search_fields = ('name', 'code')  # Add a search bar for these fields
    list_filter = ('type',)  # Filter options for account type
    ordering = ('code',)  # Order by code

# Journal Admin
@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
    list_display = ('reference_number', 'date', 'description', 'created_at')  # List view fields
    search_fields = ('reference_number', 'description')  # Search bar
    date_hierarchy = 'date'  # Add a date filter

# General Ledger Admin
@admin.register(GeneralLedger)
class GeneralLedgerAdmin(admin.ModelAdmin):
    list_display = ('account', 'journal', 'debit', 'credit', 'balance')  # Fields in list view
    search_fields = ('account__name', 'journal__reference_number')  # Search by related fields
    list_filter = ('account',)  # Filter by accounts
    ordering = ('account',)

# Trial Balance Admin
@admin.register(TrialBalance)
class TrialBalanceAdmin(admin.ModelAdmin):
    list_display = ('account', 'debit', 'credit')  # List view fields
    search_fields = ('account__name',)  # Search by account name
    ordering = ('account',)  # Order by account
