from account_engine.models import Account, Posting
from decimal import Decimal

# ACCOUNT common
################################################################################################################
################################################################################################################
################################################################################################################
################################################################################################################

CUMPLO_COST_ACCOUNT = 1
SEND_AWS_SNS = False


def costTransaction(transaction_cost_list, payment_cost_account, journal, asset_type):

    for requester_cost in transaction_cost_list:

        # Descuento a la cuenta de operacion por el monto total
        cumplo_operation_asesorias = Account.objects.get(external_account_type_id=4, external_account_id=
        requester_cost.cleaned_data['account_engine_properties']['destination_account']['id'])


        posting_from = Posting.objects.create(account=payment_cost_account, asset_type=asset_type, journal=journal,
                                              amount=(Decimal(requester_cost.cleaned_data['amount']) * -1))
        # Asignacion de inversionista a operacion
        posting_to = Posting.objects.create(account=cumplo_operation_asesorias, asset_type=asset_type, journal=journal,
                                            amount=Decimal(requester_cost.cleaned_data['amount']))

# ACCOUNT common
################################################################################################################
################################################################################################################
################################################################################################################
################################################################################################################