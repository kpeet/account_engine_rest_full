from service_objects.services import Service
from service_objects.fields import MultipleFormField, ModelField
from django import forms
from .models import JournalTransactionType, Journal, Posting, AssetType, Account, DWHBalanceAccount, Batch,BatchTransactionType, BATCH_TRANSACTION_TYPE_REAL_VIRTUAL_ID
from django.db.models import Sum
from decimal import Decimal
import logging

COLLECT_ACCOUNT_TYPE = 7
PAY_ACCOUNT_TYPE = 6
REINBURSABLE_COSTS_TYPE = 5
CUMPLO_COSTS_ACCOUNT_TYPE = 4



class UpdateBalanceAccountService(Service):
    account_id = forms.CharField(required=True, max_length=150)

    def process(self):
        account_id_input = self.cleaned_data['account_id']
        account_to_update = Account.objects.get(id=account_id_input)

        dwh_balance_account = Posting.objects.filter(account=account_to_update).aggregate(Sum('amount'))

        if dwh_balance_account['amount__sum'] is None:
            balance_account = 0
        else:
            balance_account = dwh_balance_account['amount__sum']

        balance_account = account_to_update.balance_account + balance_account

        balance_update = DWHBalanceAccount.objects.update_or_create(account=account_to_update, defaults={
            'balance_account_amount': balance_account})
        return balance_update


class CreateJournalService(Service):
    log = logging.getLogger("info_logger")
    batch_transaction_id = forms.IntegerField(required=True)
    transaction_type_id = forms.IntegerField(required=True)
    from_account_id = forms.IntegerField(required=True)
    to_account_id = forms.IntegerField(required=True)
    asset_type = forms.IntegerField(required=True)
    total_amount = forms.DecimalField(required=True)

    def clean(self):
        self.log.info("CreateJournalService INIT clean")
        total_cost = 0
        cleaned_data = super().clean()
        transaction_type_id = cleaned_data.get('transaction_type_id')
        from_account_id = cleaned_data.get('from_account_id')
        to_account_id = cleaned_data.get('to_account_id')
        total_amount = cleaned_data.get('total_amount')
        batch_transaction_id = cleaned_data.get('batch_transaction_id')

        try:
            self.log.info("CreateJournalService transaction_type_id::"+str(transaction_type_id))
            self.log.info("CreateJournalService batch_transaction_id::"+str(batch_transaction_id))

            BatchTransactionType.objects.get(id=batch_transaction_id)
            JournalTransactionType.objects.get(id=transaction_type_id)
            from_account = Account.objects.get(id=from_account_id)
            Account.objects.get(id=to_account_id)

            balance_from_account = DWHBalanceAccount.objects.get(account=from_account)
            balance_from_account_amount = Decimal(balance_from_account.balance_account_amount)

            if balance_from_account_amount < total_amount:
                raise forms.ValidationError("la cuenta de " + str(from_account.name) + "No tiene el monto suficiente")
        except Exception as e:
            raise forms.ValidationError(str(e))
        self.log.info("CreateJournalService END clean")

        # TODO: VALIDAR QUE TIENE LOS MONTOS LA CUENTA DE DONDE PROVIENEN LOS INGRESOS

    def process(self):
        self.log.info("CreateJournalService INIT process")
        transaction_type_id = self.cleaned_data['transaction_type_id']
        batch_transaction_id = self.cleaned_data['batch_transaction_id']
        from_account_id = self.cleaned_data['from_account_id']
        to_account_id = self.cleaned_data['to_account_id']
        asset_type = self.cleaned_data['asset_type']
        total_amount = self.cleaned_data['total_amount']


        batch_transaction_type = BatchTransactionType.objects.get(id=batch_transaction_id)
        journal_transaction = JournalTransactionType.objects.get(id=transaction_type_id)

        # Creacion de asiento
        batch = Batch.objects.create(batch_transaction=batch_transaction_type, total_amount=Decimal(total_amount))
        journal = Journal.objects.create(batch=batch, gloss=journal_transaction.description,
                                         journal_transaction=journal_transaction)

        # Descuento a la cuenta del inversionista
        posting_from = Posting.objects.create(account_id=from_account_id, asset_type_id=asset_type, journal=journal,
                                              amount=(Decimal(total_amount) * -1))

        # Asignacion de inversionista a operacion
        posting_to = Posting.objects.create(account_id=to_account_id, asset_type_id=asset_type, journal=journal,
                                            amount=Decimal(total_amount))

        UpdateBalanceAccountService.execute(
            {
                'account_id': from_account_id
            }
        )
        UpdateBalanceAccountService.execute(
            {
                'account_id': to_account_id
            }
        )
        self.log.info("CreateJournalService END process")

        return journal


class AddPostingToBatchService(Service):
    log = logging.getLogger("info_logger")
    batch_id = forms.IntegerField(required=True)
    journal_type_id = forms.IntegerField(required=True)
    from_account_id = forms.IntegerField(required=True)
    to_account_id = forms.IntegerField(required=True)
    asset_type = forms.IntegerField(required=True)
    total_amount = forms.DecimalField(required=True)

    def clean(self):
        self.log.info("AddPostingToJournalService INIT clean")
        total_cost = 0
        cleaned_data = super().clean()
        batch_id= cleaned_data.get('batch_id')
        from_account_id = cleaned_data.get('from_account_id')
        to_account_id = cleaned_data.get('to_account_id')
        journal_type_id = cleaned_data.get('journal_type_id')

        try:
            self.log.info("AddPostingToBatchService journal_type_id::" + str(journal_type_id))
            self.log.info("AddPostingToBatchService batch_id::" + str(batch_id))

            Batch.objects.get(id=batch_id)
            JournalTransactionType.objects.get(id=journal_type_id)
            Account.objects.get(id=from_account_id)
            Account.objects.get(id=to_account_id)
        except Exception as e:
            raise forms.ValidationError(str(e))
        self.log.info("AddPostingToJournalService END clean")

        # TODO: VALIDAR QUE TIENE LOS MONTOS LA CUENTA DE DONDE PROVIENEN LOS INGRESOS

    def process(self):
        self.log.info("AddPostingToJournalService INIT process")
        journal_type_id = self.cleaned_data['journal_type_id']
        batch_id = self.cleaned_data['batch_id']
        from_account_id = self.cleaned_data['from_account_id']
        to_account_id = self.cleaned_data['to_account_id']
        asset_type = self.cleaned_data['asset_type']
        total_amount = self.cleaned_data['total_amount']

        # Creacion de asiento
        journal_transaction = JournalTransactionType.objects.get(id=journal_type_id)
        batch = Batch.objects.get(id=batch_id)

        # Creacion de asiento
        journal = Journal.objects.create(batch=batch, gloss=journal_transaction.description,
                                         journal_transaction=journal_transaction)

        # Descuento a la cuenta del inversionista
        posting_from = Posting.objects.create(account_id=from_account_id, asset_type_id=asset_type, journal=journal,
                                              amount=(Decimal(total_amount) * -1))

        # Asignacion de inversionista a operacion
        posting_to = Posting.objects.create(account_id=to_account_id, asset_type_id=asset_type, journal=journal,
                                            amount=Decimal(total_amount))

        UpdateBalanceAccountService.execute(
            {
                'account_id': from_account_id
            }
        )
        UpdateBalanceAccountService.execute(
            {
                'account_id': to_account_id
            }
        )
        self.log.info("AddPostingToJournalService END process")

        return journal


class RealToVirtualDepositService(Service):
    real_account_id = forms.IntegerField(required=True)
    virtual_account_id = forms.IntegerField(required=True)
    asset_type_id = forms.IntegerField(required=True)
    amount = forms.DecimalField(required=True, max_digits=20, decimal_places=5)
    transaction_type_id = forms.IntegerField(required=True)
    deposit_date = forms.DateField(required=True)

    log = logging.getLogger("info_logger")

    def clean(self):
        self.log.info("RealToVirtualDepositService clean : start")

        try:
            cleaned_data = super().clean()
            transaction_type_input = cleaned_data.get('transaction_type_id')
            asset_type_id_input = cleaned_data.get('asset_type_id')
            virtual_account_id_input = cleaned_data.get('virtual_account_id')

            JournalTransactionType.objects.get(id=transaction_type_input)
            AssetType.objects.get(id=asset_type_id_input)
            Account.objects.get(id=virtual_account_id_input)
            Batch.objects.get(id=BATCH_TRANSACTION_TYPE_REAL_VIRTUAL_ID)
            self.log.info("RealToVirtualDepositService clean : END")

            return cleaned_data
        except Exception as e:
            raise forms.ValidationError(str(e))

    def process(self):
        self.log.info("RealToVirtualDepositService process : start")

        try:
            real_account_id_input = self.cleaned_data['real_account_id']

            virtual_account_id_input = self.cleaned_data['virtual_account_id']
            asset_type_id_input = self.cleaned_data['asset_type_id']
            amount_input = self.cleaned_data['amount']
            transaction_type_input = self.cleaned_data['transaction_type_id']
            transaction_type_input = 2
            deposit_date_input = self.cleaned_data['deposit_date']
            # Get Datas
            batch_transaction_type = BatchTransactionType.objects.get(id=BATCH_TRANSACTION_TYPE_REAL_VIRTUAL_ID)
            transaction_type = JournalTransactionType.objects.get(id=transaction_type_input)

            #Creacion de asiendo para caso real a virtual
            batch = Batch.objetcs.create(batch_transaction=batch_transaction_type, total_amount=amount_input)

            journal = Journal.objects.create(journal_transaction_id=transaction_type_input,
                                             gloss=transaction_type.description + ", deposit date:" + str(
                                                 deposit_date_input),
                                             batch=batch)

            posting_data = Posting.objects.create(account_id=virtual_account_id_input, journal=journal,
                                                  amount=amount_input,
                                                  asset_type_id=asset_type_id_input)

            updated_account_balance = {
                'account_id': virtual_account_id_input
            }
            UpdateBalanceAccountService.execute(updated_account_balance)
            self.log.info("RealToVirtualDepositService process : END")
            return posting_data
        except Exception as e:
            raise e
