from datetime import date

from django.core import mail
from django.test import TestCase
from decimal import Decimal

from account_engine.models import Account, JournalTransactionType, DWHBalanceAccount, AccountType, AssetType
from ..credits_services.financing_services import FinanceOperationByInvestmentTransaction
from ..models import CreditOperation
from account_engine.account_engine_services import UpdateBalanceAccountService


class CreditsOperationServiceTest(TestCase):

    def setUp(self):
        # journal_transaction = JournalTransactionType.objects.create(description="TEST")
        # asset_type = AssetType.objects.create(description='CL')

        initial_data = [
            'initial_data'
        ]


    def test_investment_without_cost(self):
        investment_id=43221
        initial_balance_investor_account=1000

        JournalTransactionType.objects.create(id=4,description="Financimiento por Inversion")

        account_type = AccountType.objects.create(account_type=2)
        account_type_credits_operation = AccountType.objects.create(account_type=CreditOperation.ACCOUNT_TYPE)
        asset_type = AssetType.objects.get(description='CL')

        requestor_account=Account.objects.create(external_account_id=123, external_account_type=account_type, balance_account=0)
        investor_account=Account.objects.create(external_account_id=1234, external_account_type=account_type, balance_account=initial_balance_investor_account)

        update_balance_requestor_account = { 'account_id': requestor_account.id}
        update_balance_investor_account = { 'account_id': investor_account.id}
        UpdateBalanceAccountService.execute(update_balance_requestor_account)
        UpdateBalanceAccountService.execute(update_balance_investor_account)

        credit_operation=CreditOperation.objects.create(
                                                        external_account_id=12343,
                                                        name="operation Test 1",
                                                        requestor_account=requestor_account,
                                                        financing_amount=initial_balance_investor_account,
                                                        external_account_type=account_type_credits_operation
                                                        )
        investor_amount_to_pay = DWHBalanceAccount.objects.get(account=investor_account)

        print("investor_amount_to_pay")
        print(str(investor_amount_to_pay))


        financing_response = FinanceOperationByInvestmentTransaction.execute(
            {
                'account': investor_account.id,
                'investment_id': investment_id,
                'total_amount': initial_balance_investor_account,
                'investment_amount': initial_balance_investor_account,
                'investment_costs': [],
                'external_operation_id': credit_operation.external_account_id,
                # TODO: definir el asset_type según sistema con que interactura
                'asset_type': 1, #asset_type.id
            }
        )

        balance_from_account_investor = DWHBalanceAccount.objects.get(account=investor_account)
        #balance_credit_operation = DWHBalanceAccount.objects.get(account_id=credit_operation)
        balance_to_account = DWHBalanceAccount.objects.get(account=requestor_account)

        self.assertEqual(balance_from_account_investor.balance_account_amount, 0)
        self.assertEqual(balance_to_account.balance_account_amount, 0)
        #self.assertEqual(balance_credit_operation.balance_account_amount, initial_balance_investor_account)



