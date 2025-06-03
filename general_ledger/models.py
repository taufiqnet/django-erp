from django.db import models

class ChartOfAccount(models.Model):
    ACCOUNT_TYPES = [
        ('asset', 'Asset'),
        ('liability', 'Liability'),
        ('equity', 'Equity'),
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]

    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    parent_account = models.ForeignKey(
        'self', null=True, blank=True, related_name='sub_accounts', on_delete=models.SET_NULL
    )

    def __str__(self):
        return f"{self.code} - {self.name} ({self.type})"


class Journal(models.Model):
    date = models.DateField()
    description = models.TextField()
    reference_number = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Journal {self.reference_number} on {self.date}"


class GeneralLedger(models.Model):
    account = models.ForeignKey(ChartOfAccount, on_delete=models.CASCADE)
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE)
    debit = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    credit = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Ledger Entry for {self.account.name} - Balance: {self.balance}"


class TrialBalance(models.Model):
    account = models.ForeignKey(ChartOfAccount, on_delete=models.CASCADE)
    debit = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    credit = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Trial Balance for {self.account.name}"
