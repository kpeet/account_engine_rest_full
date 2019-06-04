from service_objects.services import Service
from service_objects.fields import MultipleFormField, ModelField
from django import forms
from account_engine.models import JournalTransactionType, Journal, Posting, AssetType, Account, DWHBalanceAccount, BankAccount
from account_engine.account_engine_services import UpdateBalanceAccountService, CreateJournalService
from django.db.models import Sum
from credits.models import CreditOperation
from django.forms.models import model_to_dict
from decimal import Decimal
from .base_forms import CostForm
from .helper_services import costTransaction
from sns_sqs_services.services import SnsService as SnsServiceLibrary
from core_account_engine.utils import generate_sns_topic
from django.conf import settings
from .helper_services import CUMPLO_COST_ACCOUNT, CUMPLO_OPERATION_ACCOUNT_ID, AUTOMATIC_BANK_TRANSFER, REINBURSABLE_COSTS_TYPE
from .helper_services import send_AWS_SNS_treasury_paysheet_line, send_aws_sns_to_loans_requestor_payment_confirmation
import logging


class RequesterPaymentFromOperation(Service):
    """
    Funcion de Pago a Solicitante:

    Genera movimientos en cuentas T de Operacion/cuenta Solicitante/Costos .

        Validaciones que implica la operacion de pagar al solicitane

        1- que la operacion esté financiada

        2- que la operacion tenga suficiente financiamiento para pagar al solicitante y todos los costos asociados

        3- que los costos mas el monto a transferir sean iguales a el monto total de la transferencia

        4- que los costos no sean mayor que el monto a transferir al solicitante
    """
    TRANSACTION_TYPE = 5
    log = logging.getLogger("info_logger")

    account = forms.IntegerField(required=True)
    total_amount = forms.DecimalField(required=True)
    transfer_amount = forms.DecimalField(required=True)
    external_operation_id = forms.IntegerField(required=True)
    asset_type = forms.IntegerField(required=True)
    requester_costs = MultipleFormField(CostForm, required=False)



    def clean(self):
        self.log.info("RequesterPaymentFromOperation Service : clean start")
        #TODO: Validar que el solicitante sea el incrito en la operacion
        cleaned_data = super().clean()
        account = cleaned_data.get("account")
        total_amount = cleaned_data.get("total_amount")
        transfer_amount = cleaned_data.get("transfer_amount")
        external_operation_id = cleaned_data.get("external_operation_id")
        credit_operation_account = CreditOperation.objects.get(external_account_id=external_operation_id)
        operation_financing_total_amount = Posting.objects.filter(account=credit_operation_account).aggregate(Sum('amount'))
        #CUENTA ASOCIADA a la CUENTA OPERACIONAL DE BANCO EN CUMPLO
        cumplo_operation_account = Account.objects.get(id=CUMPLO_OPERATION_ACCOUNT_ID)

        to_requester_account = Account.objects.get(id=account)

        to_requestor_account_bank = BankAccount.objects.filter(
            account=to_requester_account).order_by('-updated_at')[0:1]

        from_account_bank = BankAccount.objects.filter(
            account=cumplo_operation_account).order_by('-updated_at')[0:1]

        if to_requestor_account_bank.exists():
            to_requestor_account_bank = to_requestor_account_bank.get()
        else:
            raise forms.ValidationError("No hay cuenta bancaria registrada para el solicitante. Operación Cancelada!!")

        if from_account_bank.exists():
            from_account_bank = from_account_bank.get()
        else:
            raise forms.ValidationError("No hay cuenta bancaria registrada para la cuenta de operación. Operación Cancelada!!")

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
        self.log.info("RequesterPaymentFromOperation Service : clean start")
        # TODO: modificar estos valores en duro
        BILLING_ENTITY=True
        paysheet_type="requestor"

        # Init Data
        account = self.cleaned_data['account']
        total_amount = self.cleaned_data['total_amount']
        transfer_amount = self.cleaned_data['transfer_amount']
        external_operation_id = self.cleaned_data['external_operation_id']
        requester_costs = self.cleaned_data['requester_costs']
        asset_type = self.cleaned_data['asset_type']

        # Get and Process Data
        journal_transaction = JournalTransactionType.objects.get(id=self.TRANSACTION_TYPE)
        from_credit_operation_account = CreditOperation.objects.get(external_account_id=external_operation_id)

        to_requester_account = Account.objects.get(id=account)
        asset_type = AssetType.objects.get(id=asset_type)

        if BILLING_ENTITY:
        ###### SI ES facturABLE el COSTO AL SOLICITANTE###############
            # Posting Operation v/s Requestor, T Accounts
            ###########################################
            create_journal_input = {
                'transaction_type_id': journal_transaction.id,
                'from_account_id': from_credit_operation_account.id,
                'to_account_id': to_requester_account.id,
                'asset_type': asset_type.id,
                'total_amount': Decimal(total_amount),
                }
            journal = CreateJournalService.execute(create_journal_input)

            # Posting Operation v/s Requestor, T Accounts
            # Cost Posting Process
            #######################
            costTransaction(self, transaction_cost_list=requester_costs, journal=journal, asset_type=asset_type, from_account=to_requester_account)

        else:
        ###### NO ES facturABLE el COSTO AL SOLICITANTE:::UTILIDAD POR MAYOR VALOR!!!###############
        # Posting Operation v/s Requestor, T Accounts
        ###########################################
        #TODO: Analizar los costos para ver si son facturable o no, dependiendo de eso es como se distribuyen en entre las cuentas T los montos

            create_journal_input = {
                'transaction_type_id': journal_transaction.id,
                'from_account_id': from_credit_operation_account.id,
                'to_account_id': to_requester_account.id,
                'asset_type': asset_type.id,
                'total_amount': Decimal(transfer_amount),
            }
            journal = CreateJournalService.execute(create_journal_input)

            # Posting Operation v/s Requestor, T Accounts
            # Cost Posting Process
            #######################
            costTransaction(self, transaction_cost_list=requester_costs, journal=journal, asset_type=asset_type,
                    from_account=from_credit_operation_account)


        # TODO: Llamar al modulo de facturación
        # asignacion de inversionista a costos cumplo
        # Traigo la cuenta de cumplo asesorias
        #cumplo_cost_account = Account.objects.get(id=CUMPLO_COST_ACCOUNT)
        total_amount_cost = 0
        for requester_cost in requester_costs:
            total_amount_cost = total_amount_cost + requester_cost.cleaned_data['amount']

        if total_amount_cost + transfer_amount != total_amount:
            raise Exception("Montos totales no coinciden")

        # AWS SNS Notification
        #######################
        #Envio a Paysheet
        if AUTOMATIC_BANK_TRANSFER:
            journal_transaction_reinbursable_cost = JournalTransactionType.objects.get(id=REINBURSABLE_COSTS_TYPE)
            cumplo_operation_bank_account = Account.objects.get(id=CUMPLO_OPERATION_ACCOUNT_ID)

            create_journal_input = {
                'transaction_type_id': journal_transaction_reinbursable_cost.id,
                'from_account_id': to_requester_account.id,
                'to_account_id': cumplo_operation_bank_account.id,
                'asset_type': asset_type.id,
                'total_amount': Decimal(transfer_amount)
            }
            journal = CreateJournalService.execute(create_journal_input)

            send_AWS_SNS_treasury_paysheet_line(self, to_account=to_requester_account, from_account=cumplo_operation_bank_account, transfer_amount=transfer_amount, paysheet_type=paysheet_type)

        #Notificacion de envio  a LOANS
        send_aws_sns_to_loans_requestor_payment_confirmation(self, external_operation_id=external_operation_id)
        return model_to_dict(journal)