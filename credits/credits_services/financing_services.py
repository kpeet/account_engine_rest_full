from service_objects.services import Service
from service_objects.fields import MultipleFormField, ModelField
from django import forms
from account_engine.models import JournalTransactionType, Journal, Posting, AssetType, Account, DWHBalanceAccount
from account_engine.account_engine_services import UpdateBalanceAccountService
from django.db.models import Sum
from credits.models import CreditOperation
from django.forms.models import model_to_dict
from decimal import Decimal
from .base_forms import CostForm
from .helper_services import costTransaction
from sns_sqs_services.services import SnsService as SnsServiceLibrary
from core_account_engine.utils import generate_sns_topic
from django.conf import settings
from .helper_services import CUMPLO_COST_ACCOUNT, SEND_AWS_SNS


class FinanceOperationByInvestmentTransaction(Service):
    TRANSACTION_TYPE=4

    account = forms.IntegerField(required=True)
    investment_id = forms.IntegerField(required=True)
    total_amount = forms.DecimalField(required=True)
    investment_amount = forms.DecimalField(required=True)
    investment_costs = MultipleFormField(CostForm, required=False)
    external_operation_id = forms.IntegerField(required=True)
    asset_type = forms.IntegerField(required=True)



    def clean(self):
        total_cost = 0
        cleaned_data = super().clean()
        investment_id = cleaned_data.get('investment_id')
        external_operation_id = cleaned_data.get('external_operation_id')
        investor_account_id = cleaned_data.get('account')
        list_validation_investment_error = []

        for invesment_cost in cleaned_data.get('investment_costs'):
            total_cost = total_cost + invesment_cost.cleaned_data.get('amount')

        if cleaned_data.get('investment_amount') + total_cost != cleaned_data.get('total_amount'):
            investment_error = {
                "error": 'los montos de inversion y costos no coinciden con el total'
            }

            list_validation_investment_error.append(investment_error)
        try:
            CreditOperation.objects.filter(external_account_id=external_operation_id)
            JournalTransactionType.objects.filter(id=FinanceOperationByInvestmentTransaction.TRANSACTION_TYPE)

            investor_account = Account.objects.get(id=investor_account_id)

            ####################################################################################################################################
            ####################################################################################################################################
            ####################################################################################################################################ç

            print("investor_account Flag 1")
            print(investor_account)
            investor_amount_to_pay = DWHBalanceAccount.objects.get(account=investor_account)
            print("investor_amount_to_pay")
            print(str(investor_amount_to_pay))
            print(str(investor_amount_to_pay.balance_account_amount))

            print("Flag 2")
            if investor_amount_to_pay.balance_account_amount is not None and investor_amount_to_pay.balance_account_amount >= Decimal(
                    cleaned_data.get('investment_amount') + total_cost):
                print("Flag 3")
                pass
            else:
                print("Flag 4")
                investment_error = {
                    "message": 'El inversionista no tiene monto suficiente para pagar el monto de la inversion:' + str(
                        investment_id) + "- Monto Actual en cuenta inversionista:" + str(
                        investor_amount_to_pay.balance_account_amount)
                }
                list_validation_investment_error.append(investment_error)

            print("len(list_validation_investment_error)")
            print(str(len(list_validation_investment_error)))

            if len(list_validation_investment_error) > 0:

                #######################################################################################################
                #######################################################################################################
                #######################################################################################################
                #######################################################################################################

                investor_type = ""
                if investor_account.external_account_type_id == 1:  # PERSONA
                    investor_type = "user"
                elif investor_account.external_account_type_id == 2:  # Empresa
                    investor_type = "enterprise"
                else:
                    raise ValueError("Investor Type Error")
                print("Flag 5")
                if SEND_AWS_SNS:
                    sns = SnsServiceLibrary()
                    sns_topic = generate_sns_topic(settings.SNS_INVESTMENT_PAYMENT)
                    arn = sns.get_arn_by_name(sns_topic)
                    attribute = sns.make_attributes(entity=investor_type, type='response', status='fail')

                    payload = {
                        "message": str(list_validation_investment_error),
                        "investment_id": investment_id,
                    }
                    # TODO: VER TEMA ARN
                    sns.push('arn:aws:sns:us-east-1:002311116463:cl-staging-investment-payment', attribute, payload)

                #######################################################################################################
                #######################################################################################################
                #######################################################################################################
                #######################################################################################################

                raise forms.ValidationError(list_validation_investment_error)

        except Exception as e:
            raise forms.ValidationError(str(e))

        return cleaned_data

    def process(self):
        print("FLAG PROCESS 1")
        transaction_type = FinanceOperationByInvestmentTransaction.TRANSACTION_TYPE  # Financiamiento de operación por Inversión
        # Get Data
        account = self.cleaned_data['account']
        investment_id = self.cleaned_data['investment_id']
        total_amount = self.cleaned_data['total_amount']
        investment_amount = self.cleaned_data['investment_amount']
        investment_costs = self.cleaned_data['investment_costs']
        external_operation_id = self.cleaned_data['external_operation_id']
        asset_type = self.cleaned_data['asset_type']

        # Get and Process Data
        # TODO: definir transacción de financimiento

        # ACCOUNT common
        ################################################################################################################
        ################################################################################################################
        ################################################################################################################
        ################################################################################################################

        to_operation_account = CreditOperation.objects.get(external_account_id=external_operation_id)

        journal_transaction = JournalTransactionType.objects.get(id=transaction_type)
        from_account = Account.objects.get(id=account)

        asset_type = AssetType.objects.get(id=asset_type)
        # Traigo la cuenta de cumplo asesorias
        cumplo_cost_account = Account.objects.get(id=CUMPLO_COST_ACCOUNT)
        print("FLAG 5")

        # Creacion de asiento
        journal = Journal.objects.create(batch=None, gloss=journal_transaction.description,
                                         journal_transaction=journal_transaction)

        # Descuento a la cuenta del inversionista
        posting_from = Posting.objects.create(account=from_account, asset_type=asset_type, journal=journal,
                                              amount=(Decimal(total_amount) * -1))

        # Asignacion de inversionista a operacion
        posting_to = Posting.objects.create(account=to_operation_account, asset_type=asset_type, journal=journal,
                                            amount=Decimal(investment_amount))

        # asignacion de inversionista a costos cumplo
        if investment_costs:
            costTransaction(investment_costs, from_account, journal, asset_type)

        ################################################################################################################
        ################################################################################################################
        ################################################################################################################
        ################################################################################################################
        print("FLAG 6")
        UpdateBalanceAccountService.execute(
            {
                'account_id': from_account.id
            }
        )
        # if settings.DEBUG and settings.DEBUG != True:

        #########################################################################################################################
        #########################################################################################################################
        #########################################################################################################################
        #########################################################################################################################

        investor_type = ""
        if from_account.external_account_type_id == 1:  # PERSONA
            investor_type = "user"
        elif from_account.external_account_type_id == 2:  # Empresa
            investor_type = "enterprise"
        else:
            raise ValueError("Investor Type Error")

        # Send SNS to confirm the payment (to financing)
        if SEND_AWS_SNS:
            sns = SnsServiceLibrary()

            sns_topic = generate_sns_topic(settings.SNS_INVESTMENT_PAYMENT)

            arn = sns.get_arn_by_name(sns_topic)
            attribute = sns.make_attributes(entity=investor_type, type='response', status='success')

            payload = {
                "message": "OK",
                "investment_id": investment_id,
            }
            # TODO: VER TEMA ARN
            sns.push('arn:aws:sns:us-east-1:002311116463:cl-staging-investment-payment', attribute, payload)

        #########################################################################################################################
        #########################################################################################################################
        #########################################################################################################################
        #########################################################################################################################

        return model_to_dict(journal)
