from account_engine.models import Account, Posting
from decimal import Decimal
from account_engine.account_engine_services import AddPostingToJournalService
from sns_sqs_services.services import SnsService as SnsServiceLibrary
from core_account_engine.utils import generate_sns_topic
from account_engine.models import BankAccount
from django.conf import settings
from django.db.models import Sum
from credits.models import CreditOperation
from django.forms.models import model_to_dict

CUMPLO_COST_ACCOUNT = 1
SEND_AWS_SNS = True


def costTransaction(transaction_cost_list, journal, asset_type, from_account):
    for requester_cost in transaction_cost_list:
        add_posting_to_journal_input = {
            'journal_id': journal.id,
            'from_account_id': from_account.id,
            'to_account_id': requester_cost.cleaned_data['account_engine_properties']['destination_account']['id'],
            'asset_type': asset_type.id,
            'total_amount': Decimal(requester_cost.cleaned_data['amount']),
        }
        AddPostingToJournalService.execute(add_posting_to_journal_input)


def send_AWS_SNS_treasury_paysheet_line(self, to_account, from_account, transfer_amount, paysheet_type):
    self.log.info("SNS start RequestorPayment Services to SNS_TREASURY_PAYSHEET")

    sns = SnsServiceLibrary()
    sns_topic = generate_sns_topic(settings.SNS_TREASURY_PAYSHEET)
    self.log.info("FLG 1")

    arn = sns.get_arn_by_name(sns_topic)

    attribute = {}  # sns.make_attributes(type='response', status='success')

    to_requestor_account_bank_last = BankAccount.objects.filter(
        account=to_account).order_by('-updated_at')[0:1]

    from_account_bank_last = BankAccount.objects.filter(
        account=from_account).order_by('-updated_at')[0:1]

    if to_requestor_account_bank_last.exists():
        to_requestor_account_bank = to_requestor_account_bank_last.get()

        self.log.info("SI existe cuenta bancaria de solicitante")
    else:
        self.log.info("No existe cuenta bancaria de solicitante")

    if from_account_bank_last.exists():
        from_account_bank = from_account_bank_last.get()
        self.log.info("SI existe cuenta bancaria de FROM account")
    else:
        self.log.info("No existe cuenta bancaria de  FROM account")

    payload = {
        "origin_account": from_account_bank.bank_account_number,
        "beneficiary_name": to_requestor_account_bank.account_holder_name,
        "document_number": to_requestor_account_bank.account_holder_document_number,
        "email": to_requestor_account_bank.account_notification_email,
        "message": "Pago a Solicitante",  # journal_transaction.description,
        "destination_account": to_requestor_account_bank.bank_account_number,
        "transfer_amount": f'{transfer_amount:.2f}',
        "currency_type": "CLP",
        "paysheet_line_type": paysheet_type,
        "bank_code": to_requestor_account_bank.bank_code
    }
    if SEND_AWS_SNS:
        sns.push(arn, attribute, payload)
        self.log.info("SNS Push  payload RequestorPayment Services to SNS_TREASURY_PAYSHEET")
    else:
        self.log.info("SNS Push  payload ")
        self.log.info(str(payload))


def send_aws_sns_to_loans_requestor_payment_confirmation(self, external_operation_id):
    sns = SnsServiceLibrary()
    sns_topic = generate_sns_topic(settings.SNS_LOAN_PAYMENT)
    arn = sns.get_arn_by_name(sns_topic)
    attribute = sns.make_attributes(type='response', status='success')

    payload = {'operation_id': external_operation_id}

    if SEND_AWS_SNS:
        sns.push(arn, attribute, payload)
        self.log.info("SNS Push  payload RequestorPayment Services to SNS_LOAN_PAYMENT")
    else:
        self.log.info("SNS Push  payload ")
        self.log.info(str(payload))
