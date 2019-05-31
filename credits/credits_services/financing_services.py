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
import logging
from account_engine.account_engine_services import CreateJournalService


class FinanceOperationByInvestmentTransaction(Service):
    """
       Funcion de Financionamiento de Credito por Inversion:

       Genera movimientos en cuentas T de Operacion/cuenta Inversionista/Costos .

           Validaciones que implica la operacion de pagar al solicitane

           1- que la operacion esté financiada

           2- que la operacion tenga suficiente financiamiento para pagar al solicitante y todos los costos asociados

           3- que los costos mas el monto a transferir sean iguales a el monto total de la transferencia

           4- que los costos no sean mayor que el monto a transferir al solicitante
       """
    TRANSACTION_TYPE=4
    log = logging.getLogger("info_logger")

    account = forms.IntegerField(required=True)
    investment_id = forms.IntegerField(required=True)
    total_amount = forms.DecimalField(required=True)
    investment_amount = forms.DecimalField(required=True)
    investment_costs = MultipleFormField(CostForm, required=False)
    external_operation_id = forms.IntegerField(required=True)
    asset_type = forms.IntegerField(required=True)

    def clean(self):
        self.log.info("FinanceOperationByInvestmentTransaction:: clean start")
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

            investor_amount_to_pay = DWHBalanceAccount.objects.get(account=investor_account)

            if investor_amount_to_pay.balance_account_amount is not None and investor_amount_to_pay.balance_account_amount >= Decimal(
                    cleaned_data.get('investment_amount') + total_cost):

                pass
            else:
                investment_error = {
                    "message": 'El inversionista no tiene monto suficiente para pagar el monto de la inversion:' + str(
                        investment_id) + "- Monto Actual en cuenta inversionista:" + str(
                        investor_amount_to_pay.balance_account_amount)
                }
                list_validation_investment_error.append(investment_error)


            if len(list_validation_investment_error) > 0:
                self.log.info("FinanceOperationByInvestmentTransaction:: clean Fail Validation")

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
                if SEND_AWS_SNS:



                    #######################################################################################################
                    #######################################################################################################
                    #######################################################################################################
                    #######################################################################################################


                    sns = SnsServiceLibrary()

                    #attribute = sns.make_attributes(investor_type, "response", "fail")
                    attribute = sns.make_attributes(entity=investor_type, type='response', status='fail')

                    arn = sns.get_arn_by_name(settings.SNS_INVESTMENT_PAYMENT)
                    payload = {
                        "message": str(list_validation_investment_error),
                        "investment_id": investment_id,
                    }

                    sns.push(arn, attribute, payload)

                #######################################################################################################
                #######################################################################################################
                #######################################################################################################
                #######################################################################################################

                raise forms.ValidationError(list_validation_investment_error)

        except Exception as e:
            raise forms.ValidationError(str(e))

        self.log.info("FinanceOperationByInvestmentTransaction:: clean OK")

        return cleaned_data

    def process(self):
        self.log.info("FinanceOperationByInvestmentTransaction:: process start")
        transaction_type = FinanceOperationByInvestmentTransaction.TRANSACTION_TYPE  # Financiamiento de operación por Inversión
        # Init Data
        account = self.cleaned_data['account']
        investment_id = self.cleaned_data['investment_id']
        total_amount = self.cleaned_data['total_amount']
        investment_amount = self.cleaned_data['investment_amount']
        investment_costs = self.cleaned_data['investment_costs']
        external_operation_id = self.cleaned_data['external_operation_id']
        asset_type = self.cleaned_data['asset_type']


        # Get and Process Data
        to_operation_account = CreditOperation.objects.get(external_account_id=external_operation_id)
        journal_transaction = JournalTransactionType.objects.get(id=transaction_type)
        from_account = Account.objects.get(id=account)
        asset_type = AssetType.objects.get(id=asset_type)
        # Traigo la cuenta de cumplo asesorias
        cumplo_cost_account = Account.objects.get(id=CUMPLO_COST_ACCOUNT)

        # Posting Operation v/s Investor, T Accounts
        ###########################################
        create_journal_input = {
            'transaction_type_id': journal_transaction.id,
            'from_account_id': from_account.id,
            'to_account_id': to_operation_account.id,
            'asset_type': asset_type.id,
            'total_amount': Decimal(investment_amount),
        }
        journal = CreateJournalService.execute(create_journal_input)

        # POSTING inversionista v/s costos cumplo
        if investment_costs:
            costTransaction(self,transaction_cost_list=investment_costs, journal=journal, asset_type=asset_type,
                            from_account=from_account)

        # TODO: definir transacción de financimiento

        self.log.info("Update Account Balance account_id:"+str(from_account.id))
        self.log.info("Update Account Balance account_id:"+str(to_operation_account.id))

        # Send SNS to confirm the payment (to financing)

        if SEND_AWS_SNS:
            investor_type = ""
            if from_account.external_account_type_id == 1:  # PERSONA
                investor_type = "user"
            elif from_account.external_account_type_id == 2:  # Empresa
                investor_type = "enterprise"
            else:
                raise ValueError("Investor Type Error")

            self.log.info("SNS start Financing Services to SNS_INVESTMENT_PAYMENT")
            sns = SnsServiceLibrary()
            self.log.info("SNS_INVESTMENT_PAYMENT")
            self.log.info(settings.SNS_INVESTMENT_PAYMENT)

            self.log.info("AWS_REGION_NAME")
            self.log.info(settings.AWS_REGION_NAME)

            self.log.info("AWS_ACCESS_KEY_ID")
            self.log.info(settings.AWS_ACCESS_KEY_ID)

            self.log.info("AWS_SECRET_ACCESS_KEY")
            self.log.info(settings.AWS_SECRET_ACCESS_KEY)



            arn = sns.get_arn_by_name(settings.SNS_INVESTMENT_PAYMENT)
            self.log.info("ARN SNS AWS INVESTMENT PAYMeNT")
            self.log.info(arn)
            attribute = sns.make_attributes(entity=investor_type, type='response', status='success')

            payload = {
                "message": "OK",
                "investment_id": investment_id,
            }

            sns.push(arn, attribute, payload)

            self.log.info("SNS Push  payload Financing Services to SNS_INVESTMENT_PAYMENT")
            self.log.info(str(payload))

        else:
            self.log.info("Sin envio Financing Services to SNS_INVESTMENT_PAYMENT")

        return model_to_dict(journal)
