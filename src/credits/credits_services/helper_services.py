from account_engine.models import Account, Posting
from decimal import Decimal
from account_engine.account_engine_services import AddPostingToJournalService

# ACCOUNT common
################################################################################################################
################################################################################################################
################################################################################################################
################################################################################################################

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

        # # Descuento a la cuenta de operacion por el monto total
        # cumplo_operation_asesorias = Account.objects.get(external_account_type_id=4, external_account_id=
        # requester_cost.cleaned_data['account_engine_properties']['destination_account']['id'])
        #
        #
        # posting_from = Posting.objects.create(account=payment_cost_account, asset_type=asset_type, journal=journal,
        #                                       amount=(Decimal(requester_cost.cleaned_data['amount']) * -1))
        # # Asignacion de inversionista a operacion
        # posting_to = Posting.objects.create(account=cumplo_operation_asesorias, asset_type=asset_type, journal=journal,
        #                                     amount=Decimal(requester_cost.cleaned_data['amount']))

# ACCOUNT common
################################################################################################################
################################################################################################################
################################################################################################################
################################################################################################################