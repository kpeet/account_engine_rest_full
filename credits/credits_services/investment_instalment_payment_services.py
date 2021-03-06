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
from account_engine.models import BankAccount
from account_engine.account_engine_services import CreateJournalService
import logging
from sns_sqs_services.services import SnsService as SnsServiceLibrary
from sns_sqs_services.services import SqsService
from django.conf import settings
from core_account_engine.utils import generate_sns_topic
from .helper_services import CUMPLO_COST_ACCOUNT, SEND_AWS_SNS

class InvestorPaymentFromOperation(Service):
    log = logging.getLogger("info_logger")

    asset_type = forms.IntegerField(required=True)
    external_credit_operation_id = forms.IntegerField(required=True)
    instalment_id = forms.IntegerField(required=True)
    instalment_amount = forms.DecimalField(required=True, max_digits=20, decimal_places=2)
    investors = MultipleFormField(PaymentToInvestorForm, required=False)

    # Validaciones que implica la operacion de pagar al solicitane
    def clean(self):
        self.log.info("InvestorPaymentFromOperation:: clean")

        cleaned_data = super().clean()
        external_operation_id = cleaned_data.get("external_credit_operation_id")
        instalment_id = cleaned_data.get("instalment_id")
        instalment_amount = cleaned_data.get("instalment_amount")
        investors = cleaned_data.get('investors')
        self.log.info("InvestorPaymentFromOperation:: FLAG 1")

        try:
            self.log.info("InvestorPaymentFromOperation:: FLAG 1-1"+str(external_operation_id))
            credit_operation=CreditOperation.objects.get(external_account_id=external_operation_id)
            self.log.info("InvestorPaymentFromOperation:: FLAG 1-2")


            instalment=Instalment.objects.filter(external_instalment_id=instalment_id, credit_operation=credit_operation)
            if instalment.exists():
                pass
            else:
                raise forms.ValidationError("La Cuota No hay sido Ingresada en el proceso de pago de cuotas")


                self.log.info("InvestorPaymentFromOperation:: FLAG 2")
        except Exception as e:
            raise forms.ValidationError(str(e))

        try:
            DWHBalanceAccount.objects.get(account=credit_operation.id)
            self.log.info("InvestorPaymentFromOperation:: FLAG 3")
        except Exception as e:
            raise forms.ValidationError(str(e))

        cumplo_operation_bank_account = Account.objects.get(external_account_type_id=4, external_account_id=2)
        from_account_bank_list = BankAccount.objects.filter(
            account=cumplo_operation_bank_account).order_by('-updated')[0:1]


        #cumplo_operation_bank_account = Account.objects.get(external_account_type_id=4, external_account_id=2)
        self.log.info("InvestorPaymentFromOperation:: FLAG 4")
        if from_account_bank_list.exists():
            self.log.info("InvestorPaymentFromOperation:: FLAG 4-1")
            pass
        else:
            raise forms.ValidationError(
                "No hay cuenta bancaria registrada para la cuenta de operación. Operación Cancelada!!")

        total_investment_instalment = 0
        for investor in investors:

            external_investment_instalment = investor.cleaned_data['investment_id']
            self.log.info("InvestorPaymentFromOperation:: FLAG 5")
            investor_account = Account.objects.get(
                external_account_id=investor.cleaned_data['investor_account_id'],
                external_account_type_id=investor.cleaned_data['investor_account_type'])

            investor_bank_account = BankAccount.objects.filter(account=investor_account).order_by('-updated_at')[0:1]
            self.log.info("InvestorPaymentFromOperation:: FLAG 6:: id_investor_account"+str(investor_account))
            if investor_bank_account.exists():
                self.log.info("InvestorPaymentFromOperation:: FLAG 6-1")
                investor_bank_account = investor_bank_account.get()
                self.log.info("InvestorPaymentFromOperation:: FLAG 6-2")
                if investor_bank_account.account_holder_document_number == "" or investor_bank_account.account_holder_document_number is None:
                    self.log.info("InvestorPaymentFromOperation:: FLAG 6-3")
                    raise forms.ValidationError(
                        "account_holder_document_number Empty")

                if investor_bank_account.account_holder_name == "" or investor_bank_account.account_holder_name is None:
                    self.log.info("InvestorPaymentFromOperation:: FLAG 6-4")
                    raise forms.ValidationError(
                        "account_holder_name Empty")

                self.log.info("InvestorPaymentFromOperation:: FLAG 6-5")

            else:
                raise forms.ValidationError(
                    "No hay cuenta bancaria registrada para la cuenta de Inversionista. Operación Cancelada!!")
            self.log.info("InvestorPaymentFromOperation:: FLAG 7")
            ##################################

            investment_instalment_total_amount = investor.cleaned_data.get('total_amount')

            total_investment_instalment = total_investment_instalment + investment_instalment_total_amount

            investment_instalment_cost_amount = 0
            self.log.info("InvestorPaymentFromOperation:: FLAG 8")
            for inv_instal_cost in investor.cleaned_data.get('investment_instalment_cost'):
                investment_instalment_cost_amount = investment_instalment_cost_amount + inv_instal_cost.cleaned_data.get(
                    'amount')
            self.log.info("InvestorPaymentFromOperation:: FLAG 9")
            if investment_instalment_cost_amount > Decimal(
                    investor.cleaned_data.get('total_amount') - investor.cleaned_data.get(
                            'investment_instalment_amount')) or investment_instalment_cost_amount < Decimal(
                    investor.cleaned_data.get('total_amount') - investor.cleaned_data.get(
                            'investment_instalment_amount')):
                raise forms.ValidationError(
                    "Montos de costos de InvestmentInstalments e invesment instalment No coinciden " + str(
                        investment_instalment_cost_amount) + ", " + str(Decimal(
                        investor.cleaned_data.get('total_amount') - investor.cleaned_data.get(
                            'investment_instalment_amount'))))
        self.log.info("InvestorPaymentFromOperation:: FLAG 10")
        if total_investment_instalment > instalment_amount or total_investment_instalment < instalment_amount:
            raise forms.ValidationError("Montos de InvestmentInstalments e instalment No coinciden por " + str(
                total_investment_instalment - instalment_amount))

    def process(self):
        self.log.info("InvestorPaymentFromOperation:: process start")
        transaction_type = 7  # pago de investment instalment a inversionista
        # Init Data
        investor_payments = self.cleaned_data['investors']
        external_credit_operation_id = self.cleaned_data['external_credit_operation_id']
        instalment_id = self.cleaned_data['instalment_id']
        instalment_amount = self.cleaned_data['instalment_amount']

        asset_type = self.cleaned_data['asset_type']


        # Get and Process Data
        journal_transaction = JournalTransactionType.objects.get(id=transaction_type)
        journal = Journal.objects.create(batch=None, gloss=journal_transaction.description,
                                         journal_transaction=journal_transaction)
        asset_type = AssetType.objects.get(id=asset_type)



        operation = CreditOperation.objects.get(external_account_id=external_credit_operation_id)


        self.log.info("InvestorPaymentFromOperation:: process FLag 2")


        # POSTING DESTINO
        for investor_payment in investor_payments:

            investor_account = Account.objects.get(
                external_account_id=investor_payment.cleaned_data['investor_account_id'],
                external_account_type_id=investor_payment.cleaned_data['investor_account_type'])

            # Posting Operation v/s Investor, T Accounts
            ###########################################
            create_journal_input = {
                'transaction_type_id': journal_transaction.id,
                'from_account_id': operation.id,
                'to_account_id': investor_account.id,
                'asset_type': asset_type.id,
                'total_amount': Decimal(investor_payment.cleaned_data['total_amount']),
            }
            journal = CreateJournalService.execute(create_journal_input)


            cumplo_operation_bank_account = Account.objects.get(external_account_type_id=4, external_account_id=2)

            self.send_AWS_SNS_Treasury(to_account=investor_account, from_account=cumplo_operation_bank_account,transfer_amount=investor_payment.cleaned_data['total_amount']  )





        return model_to_dict(journal)

    def send_aws_sns_loans(self, external_investment_instalment):

        sqs = SqsService(json_data={
            "result": "OK",
            "invesment_instalment_id": external_investment_instalment
        })

        sqs.push('sqs_invesment_instalment_loans_notification')
        logging.getLogger("error_logger").error(
            "send to sqs_invesment_instalment_loans_notification :: external_investment_instalment" + str(
                external_investment_instalment))



    def send_AWS_SNS_Treasury(self,to_account, from_account, transfer_amount ):
        self.log.info("SNS start RequestorPayment Services to SNS_TREASURY_PAYSHEET")
        self.log.info(" SNS_TREASURY_PAYSHEET"+str(settings.SNS_TREASURY_PAYSHEET))

        sns = SnsServiceLibrary()
        sns_topic = generate_sns_topic(settings.SNS_TREASURY_PAYSHEET)

        arn = sns.get_arn_by_name(sns_topic)

        attribute = {}  # sns.make_attributes(type='response', status='success')

        to_account_bank = BankAccount.objects.filter(
            account=to_account).order_by('-updated_at')[0:1]

        from_account_bank = BankAccount.objects.filter(
            account=from_account).order_by('-updated_at')[0:1]

        payload = {
            "origin_account": from_account_bank.bank_account_number,
            "beneficiary_name": to_account_bank.account_holder_name,
            "document_number": to_account_bank.account_holder_document_number,
            "email": to_account_bank.account_notification_email,
            "message": "Pago a Solicitante",  # journal_transaction.description,
            "destination_account": to_account_bank.bank_account_number,
            "transfer_amount": f'{transfer_amount:.2f}',
            # .format(transfer_amount)), #Decimal(transfer_amount, round(2))),
            "currency_type": "CLP",
            "paysheet_line_type": "requestor",
            "bank_code": to_account_bank.bank_code
        }

        if SEND_AWS_SNS:
            sns.push(arn, attribute, payload)
            self.log.info("SNS Push  payload RequestorPayment Services to SNS_TREASURY_PAYSHEET")
        else:
            self.log.info("SNS Push  payload ")
            self.log.info(str(payload))