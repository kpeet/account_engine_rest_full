from django.db import models
from django.db.models.fields import DateTimeField
from decimal import Decimal


class MixinDateModel(models.Model):
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AccountType(MixinDateModel):
    account_type = models.CharField(unique=True, null=False, max_length=150)


class Account(MixinDateModel):
    name = models.CharField(max_length=150)
    external_account_id = models.CharField(null=False, max_length=150)
    external_account_type = models.ForeignKey(AccountType, null=False,  on_delete=models.PROTECT)

    class Meta:
        unique_together = ('external_account_id', 'external_account_type')
    primary = ('external_account_id', 'external_account_type')


class OperationAccount(Account):
    financing_amount = models.DecimalField(null=False, decimal_places=5, default=0, max_digits=20)
    requester_account = models.ForeignKey(Account, related_name='requestor', null=False, on_delete=models.PROTECT)


class DWHBalanceAccount(MixinDateModel):
    balance_account_amount = models.DecimalField( null=False, decimal_places=5, default=0, max_digits=20)
    account = models.OneToOneField(Account, unique=True, null=True, on_delete=models.PROTECT)


class BankAccount(MixinDateModel):
    """ Bank model, represents a banking institution

    """
    account = models.ForeignKey(Account,  null=False, on_delete=models.PROTECT)
    bank_account_number = models.IntegerField(null=False)
    account_notification_email = models.EmailField(null=False)
    bank_code = models.IntegerField(null=False)
    account_bank_type = models.IntegerField(null=False)
    account_holder_name = models.CharField(null=False, max_length=200)
    account_holder_document_number = models.CharField(null=False, max_length=12)


# def positive_number(value):
#     if value < Decimal(0):
#      raise ValidationError("Must be positive")


class Batch(MixinDateModel):
    description = models.CharField(max_length=150)
    total_amount = models.DecimalField(null=False, default=Decimal('0.00000'), max_digits=20, decimal_places=5)# validators=[positive_number])


class Instalment(MixinDateModel):
    operation = models.ForeignKey(OperationAccount, default=None, null=False, on_delete=models.PROTECT)
    amount = models.DecimalField(null=False, default=0, max_digits=20, decimal_places=2)


class JournalTransactionType(MixinDateModel):

    description = models.TextField(max_length=150)


class Journal(MixinDateModel):
    batch = models.ForeignKey(Batch, null=True, on_delete=models.PROTECT, related_name='journals')
    gloss = models.TextField(max_length=350)
    journal_transaction = models.ForeignKey(JournalTransactionType, default=None, null=False, on_delete=models.PROTECT)


class AssetType(MixinDateModel):
    description = models.CharField(max_length=150)


class Posting(MixinDateModel):
    account = models.ForeignKey(Account, null=False, on_delete=models.PROTECT)
    journal = models.ForeignKey(Journal, null=False, on_delete=models.PROTECT, related_name='postings')
    amount = models.DecimalField(null=False, default=0, max_digits=20, decimal_places=2)
    asset_type = models.ForeignKey(AssetType, default=1, null=False, on_delete=models.PROTECT)


class VirtualAccountDeposit(MixinDateModel):
    amount = models.DecimalField(null=False, decimal_places=2, default=0, max_digits=20)
    asset_type = models.ForeignKey(AssetType, default=1, null=False, on_delete=models.PROTECT)
    account = models.ForeignKey(Account,  null=False, on_delete=models.PROTECT)
    deposit_date = models.DateField()
    real_account =  models.ForeignKey(BankAccount, null=False, on_delete=models.PROTECT)
