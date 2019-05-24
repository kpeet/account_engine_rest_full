from service_objects.services import Service
from service_objects.fields import MultipleFormField, ModelField
from django import forms
from account_engine.models import JournalTransactionType, Journal, Posting, AssetType, Account, DWHBalanceAccount
from account_engine.account_engine_services import UpdateBalanceAccountService
from django.db.models import Sum
from credits.models import CreditOperation
from django.forms.models import model_to_dict
from decimal import Decimal
from .base_forms import CostForm, InstalmentsForms
from .helper_services import costTransaction
from sns_sqs_services.services import SnsService as SnsServiceLibrary
from core_account_engine.utils import generate_sns_topic
from django.conf import settings
from .helper_services import CUMPLO_COST_ACCOUNT
from account_engine.account_engine_services import CreateJournalService

from .helper_services import SEND_AWS_SNS


class InstalmentPayment(Service):
    instalment_list_to_pay = MultipleFormField(InstalmentsForms, required=True)

    # Validaciones que implica la operacion de pagar al solicitane

    # 1- que la operacion esté financiada
    # 2- que la operacion tenga suficiente financiamiento para pagar al solicitante y todos los costos asociados
    # 3- que los costos mas el monto a transferir sean iguales a el monto total de la transferencia
    # 4- que los costos no sean mayor que el monto a transferir al solicitante

    def clean(self):
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

            ############################################################################
            ############################################################################
            ############################################################################
            #TODO: Implementar SNS, verificar cual es y como esta configurado su comportamiento

            if SEND_AWS_SNS:
                sqs = SqsService(json_data={
                    "result": "NOT-OK",
                    "operation_id": external_operation_id,
                    "instalments": list_validation_payment_error
                })
                sqs.push('sqs_account_engine_instalment_payment_notification')



            ############################################################################
            ############################################################################
            ############################################################################

            raise forms.ValidationError(list_validation_payment_error)
        else:
            return cleaned_data

    def process(self):
        # TODO: modificar este valor en duro

        transaction_type = 6  # Pago de cuotas
        # Get Data
        instalments_ok_for_notification = []
        for instalment in self.cleaned_data['instalment_list_to_pay']:
            payer_account_id = instalment.cleaned_data['payer_account_id']
            external_operation_id = instalment.cleaned_data['external_operation_id']
            instalment_id = instalment.cleaned_data['instalment_id']
            instalment_amount = instalment.cleaned_data['instalment_amount']
            fine_amount = instalment.cleaned_data['fine_amount']
            pay_date = instalment.cleaned_data['pay_date']
            asset_type = instalment.cleaned_data['asset_type']



            # Get and Process Data
            # TODO: definir transacción de Pago a solicitante
            journal_transaction = JournalTransactionType.objects.get(id=transaction_type)
            to_operation_account = CreditOperation.objects.get(external_account_id=external_operation_id)
            from_payer_account = Account.objects.get(id=payer_account_id)

            asset_type = AssetType.objects.get(id=asset_type)

            # ACCOUNT common
            ################################################################################################################
            ################################################################################################################
            ################################################################################################################
            ################################################################################################################

            # Creacion de Posting
            try:
                create_journal_input = {
                        'transaction_type_id': journal_transaction.id,
                        'from_account_id': from_payer_account.id,
                        'to_account_id': to_operation_account.id,
                        'asset_type': asset_type,
                        'total_amount': Decimal(instalment_amount + fine_amount),
                    }
                CreateJournalService.execute(create_journal_input)

                instalments_ok_for_notification.append(
                    {
                        "pay_date": str(pay_date),
                        "id": instalment_id
                    }
                )
                ############################################################################
                # TODO: Implementar SNS, verificar cual es y como esta configurado su comportamiento
                if SEND_AWS_SNS:
                    sqs = SqsService(json_data={
                        "result": "OK",
                        "operation_id": external_operation_id,
                        "instalments": instalments_ok_for_notification,
                    })
                    sqs.push('sqs_account_engine_instalment_payment_notification')
                ############################################################################
                ############################################################################
                ############################################################################

                return model_to_dict(journal_transaction)
            except Exception as e:
                raise e

            # journal = Journal.objects.create(batch=None, gloss=journal_transaction.description,
            #                                  journal_transaction=journal_transaction)
            #
            # # Descuento a la cuenta de operacion por el monto total
            # posting_from = Posting.objects.create(account=from_payer_account, asset_type=asset_type, journal=journal,
            #                                       amount=(Decimal(instalment_amount + fine_amount) * -1))
            #
            # # Asignacion de inversionista a operacion
            # posting_to = Posting.objects.create(account=to_operation_account, asset_type=asset_type, journal=journal,
            #                                     amount=Decimal(instalment_amount + fine_amount))
            #
            # UpdateBalanceAccountService.execute(
            #     {
            #         'account_id': from_payer_account.id
            #     }
            # )
            # UpdateBalanceAccountService.execute(
            #     {
            #         'account_id': to_operation_account.id
            #     }
            # )

            # ACCOUNT common
            ################################################################################################################
            ################################################################################################################
            ################################################################################################################
            ################################################################################################################



        ############################################################################
        ############################################################################
