from django.db import models
from account_engine.models import OperationAccount, MixinDateModel,Account

# Create your models here.


class BillingProperties(MixinDateModel):
    billable = models.BooleanField(null=False)
    billing_entity = models.CharField(max_length=150, null=True)


class CostAccountProperties(MixinDateModel):
    destination_account = models.ForeignKey(Account, related_name='cost_account', null=False, on_delete=models.PROTECT)


class CreditsCost(MixinDateModel):
    cost_amount=models.DecimalField(null=False, decimal_places=2, max_digits=20)
    billing_properties = models.ForeignKey(BillingProperties, null=False, on_delete=models.PROTECT)
    account_engine_properties = models.ForeignKey(CostAccountProperties, null=False, on_delete=models.PROTECT)


class InvestmentCreditOperation(MixinDateModel):
    investor = models.ForeignKey(Account, related_name='investor', null=False, on_delete=models.PROTECT)
    credits_operation = models.ForeignKey(OperationAccount, null=False, on_delete=models.PROTECT)
    investment_id = models.IntegerField(null=False, unique=True)
    total_amount = models.DecimalField(null=False, decimal_places=2, max_digits=20)
    investment_amount = models.DecimalField(null=False, decimal_places=2, max_digits=20)
    investment_cost = models.ForeignKey(CreditsCost, null=False, on_delete=models.PROTECT)


