from service_objects.services import Service
from service_objects.fields import MultipleFormField, ModelField
from django import forms
from account_engine.models import JournalTransactionType, Journal, Posting, AssetType, Account, DWHBalanceAccount
from account_engine.account_engine_services import UpdateBalanceAccountService
from django.db.models import Sum
from credits.models import CreditOperation, Instalment
from django.forms.models import model_to_dict
from decimal import Decimal
from .base_forms import CostForm, InstalmentsForms
from .helper_services import costTransaction
from sns_sqs_services.services import SnsService as SnsServiceLibrary
from core_account_engine.utils import generate_sns_topic
from django.conf import settings
from .helper_services import CUMPLO_COST_ACCOUNT
from account_engine.account_engine_services import CreateJournalService
import logging

from .helper_services import SEND_AWS_SNS


class InstalmentPayment(Service):
    instalment_list_to_pay = MultipleFormField(InstalmentsForms, required=True)

    log = logging.getLogger("info_logger")

    # Validaciones que implica la operacion de pagar al solicitane

    # 1- que la operacion esté financiada
    # 2- que la operacion tenga suficiente financiamiento para pagar al solicitante y todos los costos asociados
    # 3- que los costos mas el monto a transferir sean iguales a el monto total de la transferencia
    # 4- que los costos no sean mayor que el monto a transferir al solicitante

    def clean(self):
        print("InstalmentPayment : clean")
        cleaned_data = super().clean()

        list_validation_payment_error = []
        for instalment in cleaned_data.get('instalment_list_to_pay'):

            payer_account_id = instalment.cleaned_data["payer_account_id"]
            instalment_amount = instalment.cleaned_data["instalment_amount"]
            fine_amount = instalment.cleaned_data["fine_amount"]
            instalment_id = instalment.cleaned_data["instalment_id"]
            pay_date = instalment.cleaned_data['pay_date']
            external_operation_id = instalment.cleaned_data['external_operation_id']
            payer_posting_amount = Posting.objects.filter(account_id=payer_account_id).aggregate(Sum('amount'))
            # posting = Posting(account)
            if payer_posting_amount['amount__sum'] is not None and payer_posting_amount['amount__sum'] >= Decimal(
                    instalment_amount + fine_amount):
                pass
            else:
                instalment_error = {
                    "id": instalment_id,
                    "pay_date": str(pay_date),
                    "message": 'El pagador no tiene monto suficiente para pagar el monto de Cuota ID:' + str(
                        instalment_id) + "- Monto Actual en cuenta pagador:" + str(payer_posting_amount['amount__sum'])
                }
                list_validation_payment_error.append(instalment_error)

        if len(list_validation_payment_error) > 0:


            if SEND_AWS_SNS:

                self.log.info("start SEND_AWS_SNS")
                sns = SnsServiceLibrary()

                sns_topic = generate_sns_topic(settings.SNS_INSTALMENT_PAYMENT)

                arn = sns.get_arn_by_name(sns_topic)
                attribute = sns.make_attributes(
                    type='response', status='fail')

                payload = {
                    "result": "NOT-OK",
                    "operation_id": external_operation_id,
                    "instalments": list_validation_payment_error
                }
                sns.push(arn, attribute, payload)

                self.log.info("SNS Push  payload SEND_AWS_SNS")
                self.log.info(str(payload))

            else:
                self.log.info("Sin envio a SEND_AWS_SNS")

            raise forms.ValidationError(list_validation_payment_error)
        else:
            return cleaned_data

    def process(self):
        print("InstalmentPayment : process")
        transaction_type = 6  # Pago de cuotas
        # Init Data
        instalments_ok_for_notification = []
        for instalment in self.cleaned_data['instalment_list_to_pay']:
            print("PROCESS FLAG 1")
            payer_account_id = instalment.cleaned_data['payer_account_id']
            external_operation_id = instalment.cleaned_data['external_operation_id']
            instalment_id = instalment.cleaned_data['instalment_id']
            instalment_amount = instalment.cleaned_data['instalment_amount']
            fine_amount = instalment.cleaned_data['fine_amount']
            pay_date = instalment.cleaned_data['pay_date']
            asset_type = instalment.cleaned_data['asset_type']

            print("PROCESS FLAG 2")
            # Get and Process Data
            journal_transaction = JournalTransactionType.objects.get(id=transaction_type)
            to_operation_account = CreditOperation.objects.get(external_account_id=external_operation_id)
            from_payer_account = Account.objects.get(id=payer_account_id)
            asset_type = AssetType.objects.get(id=asset_type)
            print("PROCESS FLAG 3::: to_operation_account")
            print(str(to_operation_account))

            #Guardado de Couta
            new_instalment = Instalment()
            new_instalment.amount = instalment_amount
            new_instalment.external_instalment_id = instalment_id
            new_instalment.credit_operation = to_operation_account
            new_instalment.save()
            print("PROCESS FLAG 4")


            # Creacion de Posting
            try:
                print("PROCESS FLAG 5")
                create_journal_input = {
                    'transaction_type_id': journal_transaction.id,
                    'from_account_id': from_payer_account.id,
                    'to_account_id': to_operation_account.id,
                    'asset_type': 1,
                    'total_amount': Decimal(instalment_amount + fine_amount),
                }
                print("PROCESS FLAG 6")
                journal = CreateJournalService.execute(create_journal_input)

                instalments_ok_for_notification.append(
                    {
                        "pay_date": str(pay_date),
                        "id": instalment_id
                    }
                )

                ############################################################################
                # TODO: Implementar SNS, verificar cual es y como esta configurado su comportamiento
                if SEND_AWS_SNS:

                    self.log.info("start SEND_AWS_SNS")
                    sns = SnsServiceLibrary()

                    sns_topic = generate_sns_topic(settings.SNS_INSTALMENT_PAYMENT)

                    arn = sns.get_arn_by_name(sns_topic)
                    attribute = sns.make_attributes(
                        type='response', status='success')

                    payload = {
                        "result": "OK",
                        "operation_id": external_operation_id,
                        "instalments": instalments_ok_for_notification,
                    }
                    sns.push(arn, attribute, payload)

                    self.log.info("SNS Push  payload SEND_AWS_SNS")
                    self.log.info(str(payload))

                else:
                    self.log.info("Sin envio a SEND_AWS_SNS")

                return model_to_dict(journal_transaction)
            except Exception as e:
                raise e

