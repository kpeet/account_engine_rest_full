from service_objects.services import Service
from service_objects.fields import MultipleFormField, ModelField
from django import forms
from account_engine.models import JournalTransactionType, Journal, Posting, AssetType, Account, DWHBalanceAccount
from account_engine.account_engine_services import UpdateBalanceAccountService
from django.db.models import Sum
from credits.models import CreditOperation, Instalment
from django.forms.models import model_to_dict
from decimal import Decimal
from .base_forms import CostForm, InstalmentsForms, PaymentToInvestorForm
from .helper_services import costTransaction

class InvestorPaymentFromOperation(Service):
    # external_operation_id = forms.IntegerField(required=True)
    instalment = ModelField(Instalment)
    asset_type = forms.IntegerField(required=True)

    investors = MultipleFormField(PaymentToInvestorForm, required=False)

    # Validaciones que implica la operacion de pagar al solicitane
    def clean(self):

        cleaned_data = super().clean()
        external_operation_id = cleaned_data.get("external_operation_id")
        instalment = cleaned_data.get("instalment")
        instalment_amount = cleaned_data.get("instalment_amount")
        instalment.save()
        investors = cleaned_data.get('investors')

        total_investment_instalment = 0
        for investor in investors:

            investment_instalment_total_amount = investor.cleaned_data.get('total_amount')

            total_investment_instalment = total_investment_instalment + investment_instalment_total_amount

            investment_instalment_cost_amount = 0
            for inv_instal_cost in investor.cleaned_data.get('investment_instalment_cost'):
                investment_instalment_cost_amount = investment_instalment_cost_amount + inv_instal_cost.cleaned_data.get(
                    'amount')

            if investment_instalment_cost_amount > Decimal(investor.cleaned_data.get('total_amount') - investor.cleaned_data.get('investment_instalment_amount') ) or investment_instalment_cost_amount < Decimal(investor.cleaned_data.get('total_amount') - investor.cleaned_data.get('investment_instalment_amount')):
                raise forms.ValidationError("Montos de costos de InvestmentInstalments e invesment instalment No coinciden " + str(
                    investment_instalment_cost_amount)+", "+ str(Decimal(investor.cleaned_data.get('total_amount') - investor.cleaned_data.get('investment_instalment_amount'))))

        if total_investment_instalment > instalment.amount or total_investment_instalment < instalment.amount:
            raise forms.ValidationError("Montos de InvestmentInstalments e instalment No coinciden por " + str(
                total_investment_instalment - instalment.amount))


    def process(self):
        transaction_type = 7  # pago de investment instalment as inversionista
        investor_payments = self.cleaned_data['investors']
        instalment = self.cleaned_data['instalment']
        asset_type = self.cleaned_data['asset_type']

        # journal = Journal.objects.get(id=7)#Transaccion de pago a inversionista

        # Creacion de asiento
        journal_transaction = JournalTransactionType.objects.get(id=transaction_type)
        journal = Journal.objects.create(batch=None, gloss=journal_transaction.description,
                                         journal_transaction=journal_transaction)

        asset_type = AssetType.objects.get(id=asset_type)

        # POSTING ORIGEN
        origin_account_transaction = Posting()
        origin_account_transaction.amount = (instalment.amount * -1)
        origin_account_transaction.account = instalment.operation
        origin_account_transaction.journal = journal
        origin_account_transaction.asset_type = asset_type
        origin_account_transaction.save()


        # ACCOUNT common
        ################################################################################################################
        ################################################################################################################
        ################################################################################################################
        ################################################################################################################

        # POSTING DESTINO
        for investor_payment in investor_payments:
            investor_account = Account.objects.get(
                external_account_id=investor_payment.cleaned_data['investor_account_id'],
                external_account_type_id=investor_payment.cleaned_data['investor_account_type'])

            # if investor_payment.cleaned_data['investment_instalment_amount'] == 100500001:
            #     raise ValueError("Simulando Error")

            investment_instalment_costs = investor_payment.cleaned_data['investment_instalment_cost']
            investor_account_transaction = Posting()
            investor_account_transaction.amount = Decimal(investor_payment.cleaned_data['total_amount'])
            investor_account_transaction.account = investor_account
            investor_account_transaction.asset_type = asset_type
            investor_account_transaction.journal = journal
            investor_account_transaction.save()



            costTransaction(investment_instalment_costs, investor_account, journal, asset_type)

            UpdateBalanceAccountService.execute(
                {
                    'account_id': investor_account.id
                }
            )

        # ACCOUNT common
        ################################################################################################################
        ################################################################################################################
        ################################################################################################################
        ################################################################################################################
        return model_to_dict(journal)