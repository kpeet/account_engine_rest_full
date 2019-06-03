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


class CreditOperation(Account):
    ACCOUNT_TYPE=3
    STATE_BEING_CREDIT_OPERATION = 'being_credit_operation'
    STATE_FINANCED = 'financed'
    STATE_REQUESTOR_PAYMENT = 'requestor_payment'
    STATE_PAYMENT_COLLECTING_INSTALMENTS = 'collecting_instalments'
    STATE_ = 'requestor_payment'
    STATE_CANCELED = 'canceled'
    STATE_COMPLETED = 'completed'
    STATE_DEFAULT = 'default'
    STATES = (
        (STATE_BEING_CREDIT_OPERATION, 'En financiamiento'),
        (STATE_FINANCED, 'Financiada'),
        (STATE_REQUESTOR_PAYMENT, 'Solicitante Pagado'),
        (STATE_PAYMENT_COLLECTING_INSTALMENTS, 'Pago y Cobranza de Cuotas'),
        (STATE_COMPLETED, 'Completada'),
        (STATE_CANCELED, 'Cancelada'),
        (STATE_DEFAULT, 'Cobranza Judicial'),

    )

    state = models.CharField(max_length=30, choices=STATES, default=STATE_BEING_CREDIT_OPERATION)
    financing_amount = models.DecimalField(null=False, decimal_places=2, default=0, max_digits=20)
    requestor_account = models.ForeignKey(Account, related_name='requestor_credits_operation', null=False,
                                          on_delete=models.PROTECT)

    def financing_credit_operation(self):
        if self.state != CreditOperation.STATE_BEING_CREDIT_OPERATION:
            return self, False

        self.state = CreditOperation.STATE_FINANCED
        self.save()

        return self, True

    def requestor_payment(self):
        if self.state != CreditOperation.STATE_FINANCED:
            return self, False

        self.state = CreditOperation.STATE_REQUESTOR_PAYMENT
        self.save()

        return self, True

    def payment_instalment(self):
        if self.state != CreditOperation.STATE_REQUESTOR_PAYMENT:
            return self, False

        self.state = CreditOperation.STATE_PAYMENT_COLLECTING_INSTALMENTS
        self.save()

        return self, True

    def complete_operation(self):
        if self.state != CreditOperation.STATE_PAYMENT_COLLECTING_INSTALMENTS:
            return self, False

        self.state = CreditOperation.STATE_COMPLETED
        self.save()

        return self, True

    def default_operation(self):
        if self.state != CreditOperation.STATE_PAYMENT_COLLECTING_INSTALMENTS:
            return self, False

        self.state = CreditOperation.STATE_DEFAULT
        self.save()

        return self, True


class Instalment(MixinDateModel):
    """

    """
    credit_operation = models.ForeignKey(CreditOperation, default=None, null=False, on_delete=models.PROTECT)
    amount = models.DecimalField(null=False, default=0, max_digits=20, decimal_places=2)
    external_instalment_id = models.IntegerField(null=False, unique=True, default=None,)
