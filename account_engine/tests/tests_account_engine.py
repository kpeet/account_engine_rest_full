from datetime import date

from django.core import mail
from django.test import TestCase
from decimal import Decimal

from ..models import Account, JournalTransactionType, DWHBalanceAccount, AccountType, AssetType
from ..account_engine_services import CreateJournalService, RealToVirtualDepositService


class AccountTransactionServiceTest(TestCase):

    def setUp(self):
        journal_transaction = JournalTransactionType.objects.create(description="TEST")
        asset_type = AssetType.objects.create(description='CLP')

    def test_text_content(self):
        account_type = AccountType.objects.create(account_type=2)
        Account.objects.create(external_account_id=123, external_account_type=account_type, balance_account=10000)
        # post = Account.objects.get(id=1)
        expected_object_name = 0  # f'{post.external_account_id}'
        self.assertEquals(expected_object_name, 0)

    def test_text_content_true(self):
        # post = Account.objects.get(id=1)
        expected_object_name = 0  # f'{post.external_account_id}'
        self.assertEquals(expected_object_name, 0)

    def test__journal_service_and_balance(self):
        journal_transaction = JournalTransactionType.objects.get(description="TEST")
        asset_type = AssetType.objects.get(description='CLP')
        account_type = AccountType.objects.create(account_type=2)
        to_account = Account.objects.create(external_account_id=123, external_account_type=account_type)
        from_account = Account.objects.create(external_account_id=1234, external_account_type=account_type,
                                              balance_account=10000)

        amount = 10000
        create_journal_input = {
            'transaction_type_id': journal_transaction.id,
            'from_account_id': from_account.id,
            'to_account_id': to_account.id,
            'asset_type': asset_type.id,
            'total_amount': Decimal(amount),
        }

        journal = CreateJournalService.execute(create_journal_input)

        balance_from_account = DWHBalanceAccount.objects.get(account=from_account)
        balance_to_account = DWHBalanceAccount.objects.get(account=to_account)

        # Test that a Customer gets created

        self.assertEqual(balance_from_account.balance_account_amount, 0)
        self.assertEqual(balance_to_account.balance_account_amount, amount)

    def test_journal__service_and_balance_with_deposit(self):
        from_account__initial_balance_account: int = 10000
        amount = 10000
        final_from_account__initial_balance_account: int = from_account__initial_balance_account+amount

        from_external_account_id=123
        to_external_account_id=1234

        account_type=2
        bank_account = 1

        depost_date = "2018-10-10"

        journal_transaction = JournalTransactionType.objects.get(description="TEST")
        asset_type = AssetType.objects.get(description='CLP')
        account_type = AccountType.objects.create(account_type=account_type)
        to_account = Account.objects.create(external_account_id=from_external_account_id, external_account_type=account_type)
        # journal_transaction = JournalTransactionType.objects.get(id=1)
        # asset_type = 1

        create_virtual_deposits_input = {
            "real_account_id": bank_account,
            "virtual_account_id": to_account.id,
            "asset_type_id": asset_type.id,
            "transaction_type_id": journal_transaction.id,
            "amount": amount,
            "deposit_date": depost_date

        }

        RealToVirtualDepositService.execute(create_virtual_deposits_input)

        from_account = Account.objects.create(external_account_id=to_external_account_id, external_account_type=account_type,
                                              balance_account=from_account__initial_balance_account)


        create_journal_input = {
            'transaction_type_id': journal_transaction.id,
            'from_account_id': from_account.id,
            'to_account_id': to_account.id,
            'asset_type': asset_type.id,
            'total_amount': Decimal(amount),
        }

        journal = CreateJournalService.execute(create_journal_input)

        balance_from_account = DWHBalanceAccount.objects.get(account=from_account)
        balance_to_account = DWHBalanceAccount.objects.get(account=to_account)

        # Test that a Customer gets created

        self.assertEqual(balance_from_account.balance_account_amount, 0)
        self.assertEqual(balance_to_account.balance_account_amount, final_from_account__initial_balance_account)
