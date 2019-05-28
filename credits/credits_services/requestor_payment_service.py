from service_objects.services import Service
from service_objects.fields import MultipleFormField, ModelField
from django import forms
from account_engine.models import JournalTransactionType, Journal, Posting, AssetType, Account, DWHBalanceAccount, BankAccount
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
from .helper_services import CUMPLO_COST_ACCOUNT
from .helper_services import SEND_AWS_SNS
import logging


class RequesterPaymentFromOperation(Service):
    TRANSACTION_TYPE = 5
    log = logging.getLogger("info_logger")

    account = forms.IntegerField(required=True)
    total_amount = forms.DecimalField(required=True)
    transfer_amount = forms.DecimalField(required=True)
    external_operation_id = forms.IntegerField(required=True)
    asset_type = forms.IntegerField(required=True)
    requester_costs = MultipleFormField(CostForm, required=False)

    # Validaciones que implica la operacion de pagar al solicitane

    # 1- que la operacion esté financiada
    # 2- que la operacion tenga suficiente financiamiento para pagar al solicitante y todos los costos asociados
    # 3- que los costos mas el monto a transferir sean iguales a el monto total de la transferencia
    # 4- que los costos no sean mayor que el monto a transferir al solicitante

    def clean(self):
        cleaned_data = super().clean()
        total_amount = cleaned_data.get("total_amount")
        transfer_amount = cleaned_data.get("transfer_amount")
        external_operation_id = cleaned_data.get("external_operation_id")
        operation_data = CreditOperation.objects.get(external_account_id=external_operation_id)
        operation_financing_total_amount = Posting.objects.filter(account=operation_data).aggregate(Sum('amount'))

        # 2- que la operacion tenga suficiente financiamiento para pagar al solicitante y todos los costos asociados

        if operation_financing_total_amount['amount__sum'] is None or operation_financing_total_amount[
            'amount__sum'] < total_amount:
            raise forms.ValidationError(
                "La operacion No tiene Financiamiento suficiente para pagar el total de la transacción")

        # 3- que los costos mas el monto a transferir sean iguales a el monto total de la transferencia
        total_amount_cost = 0
        # if requester_costs:
        for requester_cost in cleaned_data.get("requester_costs"):
            #     # asignacion de inversionista a costos cumplo

            requester_cost_amount = requester_cost.clean()

            total_amount_cost = total_amount_cost + requester_cost_amount['amount']

        if total_amount_cost + transfer_amount != total_amount:
            raise forms.ValidationError("Los montos no coinciden")

        # 4- que los costos no sean mayor que el monto a transferir al solicitante

        if total_amount_cost > transfer_amount:
            raise forms.ValidationError(
                "Los costos asociados al pago son mayores que el monto a transferir al solicitante")

        # 5- Validar cuentas bancarias

        return cleaned_data

    def process(self):
        # TODO: modificar este valor en duro
        transaction_type = 5  # Pago a solicitante
        # Get Data
        account = self.cleaned_data['account']
        total_amount = self.cleaned_data['total_amount']
        transfer_amount = self.cleaned_data['transfer_amount']
        external_operation_id = self.cleaned_data['external_operation_id']
        requester_costs = self.cleaned_data['requester_costs']
        asset_type = self.cleaned_data['asset_type']

        # Get and Process Data
        # TODO: definir transacción de Pago a solicitante
        journal_transaction = JournalTransactionType.objects.get(id=transaction_type)
        from_account = CreditOperation.objects.get(external_account_id=external_operation_id)
        cumplo_operation_bank_account = Account.objects.get(external_account_type_id=4, external_account_id=2)

        to_requester_account = Account.objects.get(id=account)

        asset_type = AssetType.objects.get(id=asset_type)

        # Traigo la cuenta de cumplo asesorias
        cumplo_cost_account = Account.objects.get(id=CUMPLO_COST_ACCOUNT)

        # Create Data
        ################################################################################################################
        ################################################################################################################

        # TODO: Llamar al modulo de facturación
        # asignacion de inversionista a costos cumplo
        total_amount_cost = 0
        for requester_cost in requester_costs:
            total_amount_cost = total_amount_cost + requester_cost.cleaned_data['amount']

        if total_amount_cost + transfer_amount != total_amount:
            raise Exception("Montos totales no coinciden")



        # ACCOUNT common
        ################################################################################################################
        ################################################################################################################
        ################################################################################################################
        ################################################################################################################
        # Creacion de asiento
        journal = Journal.objects.create(batch=None, gloss=journal_transaction.description,
                                         journal_transaction=journal_transaction)

        # Descuento a la cuenta de operacion por el monto total
        posting_from = Posting.objects.create(account=from_account, asset_type=asset_type, journal=journal,
                                              amount=(Decimal(total_amount) * -1))

        # Asignacion de inversionista a operacion
        posting_to = Posting.objects.create(account=to_requester_account, asset_type=asset_type, journal=journal,
                                            amount=Decimal(
                                                total_amount))  ## al solicitante se le gira el total delmonto y se le descuentan los costos con costTransaction



        # ACCOUNT common
        ################################################################################################################
        ################################################################################################################
        ################################################################################################################
        ################################################################################################################

        to_requestor_account_bank = BankAccount.objects.filter(
            account=to_requester_account).order_by('-updated_at')[0:1]

        from_account_bank = BankAccount.objects.filter(
            account=cumplo_operation_bank_account).order_by('-updated_at')[0:1]

        if to_requestor_account_bank.exists():
            to_requestor_account_bank = to_requestor_account_bank.get()
        else:
            raise Exception("No hay cuenta bancaria registrada para el solicitante. Operación Cancelada!!")

        if from_account_bank.exists():
            from_account_bank = from_account_bank.get()
        else:
            raise Exception("No hay cuenta bancaria registrada para la cuenta de operación. Operación Cancelada!!")

        costTransaction(requester_costs, to_requester_account, journal, asset_type)

        UpdateBalanceAccountService.execute(
            {
                'account_id': from_account.id
            }
        )
        UpdateBalanceAccountService.execute(
            {
                'account_id': to_requester_account.id
            }
        )

        if SEND_AWS_SNS:
            self.log.info("SNS start RequestorPayment Services to SNS_TREASURY_PAYSHEET")

            sns = SnsServiceLibrary()
            sns_topic = generate_sns_topic(settings.SNS_TREASURY_PAYSHEET)

            arn = sns.get_arn_by_name(sns_topic)

            attribute = {}  # sns.make_attributes(type='response', status='success')


            payload = {
                "origin_account": from_account_bank.bank_account_number,
                "beneficiary_name": to_requestor_account_bank.account_holder_name,
                "document_number": to_requestor_account_bank.account_holder_document_number,
                "email": to_requestor_account_bank.account_notification_email,
                "message": "Pago a Solicitante",  # journal_transaction.description,
                "destination_account": to_requestor_account_bank.bank_account_number,
                "transfer_amount": f'{transfer_amount:.2f}',
                # .format(transfer_amount)), #Decimal(transfer_amount, round(2))),
                "currency_type": "CLP",
                "paysheet_line_type": "requestor",
                "bank_code": to_requestor_account_bank.bank_code
            }

            sns.push(arn, attribute, payload)
            self.log.info("SNS Push  payload RequestorPayment Services to SNS_TREASURY_PAYSHEET")



        # sqs = SqsService(json_data={
        #     "origin_account": from_account_bank.bank_account_number,
        #     "beneficiary_name": to_requestor_account_bank.account_holder_name,
        #     "document_number": to_requestor_account_bank.account_holder_document_number,
        #     "email": to_requestor_account_bank.account_notification_email,
        #     "mesagge": journal_transaction.description,
        #     "destination_account": to_requestor_account_bank.bank_account_number,
        #     "transfer_amount": str(transfer_amount),
        #     "currency_type": "CLP",
        #     "paysheet_line_type": "requestor"
        # })
        #
        # sqs.push('sqs_account_engine_payment_requestor')

        # Send SNS to confirm the payment (to financing)
        if SEND_AWS_SNS:

            sns = SnsServiceLibrary()
            sns_topic = generate_sns_topic(settings.SNS_LOAN_PAYMENT)
            arn = sns.get_arn_by_name(sns_topic)
            attribute = sns.make_attributes(type='response', status='success')

            payload = {'operation_id': external_operation_id}

            sns.push(arn, attribute, payload)

        return model_to_dict(journal)