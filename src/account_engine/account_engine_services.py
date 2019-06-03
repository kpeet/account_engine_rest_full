from service_objects.services import Service
from service_objects.fields import MultipleFormField, ModelField
from django import forms
from .models import JournalTransactionType, Journal, Posting, AssetType, Account, DWHBalanceAccount
from django.db.models import Sum
from decimal import Decimal
import logging


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

        try:
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
        from_account_id = self.cleaned_data['from_account_id']
        to_account_id = self.cleaned_data['to_account_id']
        asset_type = self.cleaned_data['asset_type']
        total_amount = self.cleaned_data['total_amount']

        journal_transaction = JournalTransactionType.objects.get(id=transaction_type_id)

        # Creacion de asiento
        journal = Journal.objects.create(batch=None, gloss=journal_transaction.description,
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


class AddPostingToJournalService(Service):
    log = logging.getLogger("info_logger")
    journal_id = forms.IntegerField(required=True)
    from_account_id = forms.IntegerField(required=True)
    to_account_id = forms.IntegerField(required=True)
    asset_type = forms.IntegerField(required=True)
    total_amount = forms.DecimalField(required=True)

    def clean(self):
        self.log.info("AddPostingToJournalService INIT clean")
        total_cost = 0
        cleaned_data = super().clean()
        journal_id = cleaned_data.get('journal_id')
        from_account_id = cleaned_data.get('from_account_id')
        to_account_id = cleaned_data.get('to_account_id')

        try:
            Journal.objects.get(id=journal_id)
            Account.objects.get(id=from_account_id)
            Account.objects.get(id=to_account_id)
        except Exception as e:
            raise forms.ValidationError(str(e))
        self.log.info("AddPostingToJournalService END clean")


        # TODO: VALIDAR QUE TIENE LOS MONTOS LA CUENTA DE DONDE PROVIENEN LOS INGRESOS

    def process(self):
        self.log.info("AddPostingToJournalService INIT process")
        journal_id = self.cleaned_data['journal_id']
        from_account_id = self.cleaned_data['from_account_id']
        to_account_id = self.cleaned_data['to_account_id']
        asset_type = self.cleaned_data['asset_type']
        total_amount = self.cleaned_data['total_amount']

        # Creacion de asiento
        journal = Journal.objects.get(id=journal_id)

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

    def clean(self):
        try:
            cleaned_data = super().clean()
            transaction_type_input = cleaned_data.get('transaction_type_id')
            asset_type_id_input = cleaned_data.get('asset_type_id')
            virtual_account_id_input = cleaned_data.get('virtual_account_id')
            JournalTransactionType.objects.get(id=transaction_type_input)
            AssetType.objects.get(id=asset_type_id_input)
            Account.objects.get(id=virtual_account_id_input)

            return cleaned_data
        except Exception as e:
            raise forms.ValidationError(str(e))

    def process(self):
        try:
            real_account_id_input = self.cleaned_data['real_account_id']
            virtual_account_id_input = self.cleaned_data['virtual_account_id']
            asset_type_id_input = self.cleaned_data['asset_type_id']
            amount_input = self.cleaned_data['amount']
            transaction_type_input = self.cleaned_data['transaction_type_id']
            transaction_type_input = 2
            deposit_date_input = self.cleaned_data['deposit_date']
            # Get Datas
            transaction_type = JournalTransactionType.objects.get(id=transaction_type_input)

            journal = Journal.objects.create(journal_transaction_id=transaction_type_input,
                                             gloss=transaction_type.description + ", deposit date:" + str(
                                                 deposit_date_input),
                                             batch=None)

            posting_data = Posting.objects.create(account_id=virtual_account_id_input, journal=journal,
                                                  amount=amount_input,
                                                  asset_type_id=asset_type_id_input)

            updated_account_balance = {
                'account_id': virtual_account_id_input
            }
            UpdateBalanceAccountService.execute(updated_account_balance)

            return posting_data
        except Exception as e:
            raise e
