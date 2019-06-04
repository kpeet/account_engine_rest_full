from django.db import IntegrityError, transaction
from rest_framework import serializers
from django.utils.translation import ugettext_lazy as _
from rest_framework.fields import empty
from rest_framework.serializers import ModelSerializer
from rest_framework.validators import UniqueValidator
from django.db.models import Sum

from .constants import TRANSACTION_TYPE

from .models import Account, OperationAccount, AccountType, Journal, JournalTransactionType, Posting, DWHBalanceAccount, \
    BankAccount, VirtualAccountDeposit, AssetType

from .account_engine_services import UpdateBalanceAccountService


class NotUniqueSerializer(ModelSerializer):
    def __init__(self, instance=None, data=empty, **kwargs):
        super().__init__(instance, data, **kwargs)

        for field_value in self.fields.values():
            for validator in field_value.validators:
                if isinstance(validator, UniqueValidator):
                    field_value.validators.remove(validator)


class CoreSerializer(NotUniqueSerializer):
    default_lookup_field = 'id'
    default_error_messages = {
        'creation': _('An error occurred when try to create or update the object \"{data_value}\" in the database'),
    }

    def __init__(self, instance=None, data=empty, lookup_field=None, **kwargs):
        super().__init__(instance, data, **kwargs)

        self.lookup_field = lookup_field if lookup_field is not None else self.default_lookup_field

    def to_internal_value(self, data):
        validated_data = super().to_internal_value(data)

        try:
            lookup = {self.lookup_field: validated_data.pop(self.lookup_field)}
            instance, created = self.Meta.model.objects.update_or_create(defaults=validated_data, **lookup)

        except IntegrityError:
            self.fail('creation', data_value=data)

        return instance


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'


class OperationAccountSerializer(serializers.Serializer):
    operation_id = serializers.CharField(required=True, source='external_account_id', max_length=150)
    financing_amount = serializers.DecimalField(required=True, max_digits=20, decimal_places=2)
    requester_id = serializers.IntegerField(required=True, source='requester_account_id')

    def validate(self, data):
        try:

            Account.objects.get(external_account_id=data['requester_account_id'],
                                external_account_type_id=2)

            operation = OperationAccount.objects.filter(external_account_id=data['external_account_id'])
            if operation.exists():
                raise serializers.ValidationError("external_account_id ya ingresado")

            if data['financing_amount'] < 1:
                raise serializers.ValidationError("Monto de financiamiento Insuficiente ")

            return data

        except Exception as e:
            raise serializers.ValidationError(str(e))

    def create(self, validated_data):
        requester = Account.objects.get(external_account_id=validated_data['requester_account_id'],
                                        external_account_type_id=2)

        name = "Operacion " + str(validated_data['external_account_id'])
        create_operation = OperationAccount.objects.create(external_account_id=validated_data['external_account_id'],
                                                           name=name,
                                                           requester_account=requester,
                                                           financing_amount=validated_data['financing_amount'],
                                                           external_account_type_id=3)
        return create_operation

    def update(self, instance, validated_data):
        pass


class AccountTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountType
        fields = "__all__"


class JournalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Journal
        fields = "__all__"


class JournalTransactionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalTransactionType
        fields = "__all__"


class PostingSerializer(serializers.ModelSerializer):
    """
    Serializer of Posting used in Journal
    """

    class Meta:
        model = Posting
        fields = "__all__"


class DestinationAccountSerializer(serializers.Serializer):
    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    id = serializers.IntegerField(required=True)


class BillingPropertiesSerializers(serializers.Serializer):
    def update(self, instance, validated_data):
        return validated_data

    def create(self, validated_data):
        return validated_data

    billable = serializers.BooleanField(required=True)
    billing_entity = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    # TODO: TAX, validar con Barbara si es necesario este campo para presentación de info en datos de Facturación


class AccountEnginePropertiesSerializer(serializers.Serializer):
    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    destination_account = DestinationAccountSerializer()


class CostSerializer(serializers.Serializer):
    def update(self, instance, validated_data):
        return validated_data

    def create(self, validated_data):
        return validated_data

    amount = serializers.DecimalField(required=True, max_digits=20, decimal_places=2)
    billing_properties = BillingPropertiesSerializers(required=True)
    account_engine_properties = AccountEnginePropertiesSerializer(required=True)


class JournalOperationInvestmentTransactionSerializer(serializers.Serializer):
    investor_account_id = serializers.CharField(required=True)
    investor_account_type = serializers.IntegerField(required=True)
    external_operation_id = serializers.CharField(required=True)
    investment_id = serializers.IntegerField(required=True)
    total_amount = serializers.DecimalField(required=True, max_digits=20, decimal_places=2)
    investment_amount = serializers.DecimalField(required=True, max_digits=20, decimal_places=2)
    investment_cost = CostSerializer(many=True)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):

        investor_account = Account.objects.get(external_account_id=validated_data['investor_account_id'],
                                               external_account_type_id=validated_data['investor_account_type'])

        try:
            return []

            # financing_response = FinanceOperationByInvestmentTransaction.execute(
            #     {
            #         'account': investor_account.id,
            #         'investment_id': validated_data['investment_id'],
            #         'total_amount': validated_data['total_amount'],
            #         'investment_amount': validated_data['investment_amount'],
            #         'investment_costs': validated_data['investment_cost'],
            #         'external_operation_id': validated_data['external_operation_id'],
            #         # TODO: definir el asset_type según sistema con que interactura
            #         'asset_type': 1
            #     }
            # )
            # return financing_response

        except Exception as e:
            raise e


class DWHBalanceAccountSerializer(ModelSerializer):
    class Meta:
        model = DWHBalanceAccount
        fields = "__all__"


class BankRegistrySerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = '__all__'


class BankRegistrySerializer2(serializers.Serializer):
    EXTERNAL_REQUESTOR_ACCOUNT_TYPE = 2

    bank_account_number = serializers.IntegerField(required=True)
    account_notification_email = serializers.EmailField(required=True, )
    account_holder_name = serializers.CharField(required=True, max_length=150)
    account_holder_document_number = serializers.CharField(required=True, max_length=12)
    bank_code = serializers.IntegerField(required=True)
    account_bank_type = serializers.IntegerField(required=True,)

    external_account_id = serializers.IntegerField(required=True, )
    external_account_type = serializers.IntegerField(required=True,)

    def validate(self, data):
        try:

            Account.objects.get(external_account_id=data['external_account_id'],
                                external_account_type_id=data['external_account_type'])

            return data

        except Exception as e:
            raise serializers.ValidationError(str(e))

    def create(self, validated_data):
        account = Account.objects.get(external_account_id=validated_data['external_account_id'],
                                      external_account_type_id=validated_data['external_account_type'])

        create_bank_account = BankAccount.objects.create(account=account,
                                                      bank_account_number=validated_data['bank_account_number'],
                                                      bank_code=validated_data['bank_code'],
                                                      account_notification_email=validated_data[
                                                          'account_notification_email'],
                                                      account_bank_type=validated_data['account_bank_type'],
                                                      account_holder_name=validated_data['account_holder_name'],
                                                      account_holder_document_number=validated_data[
                                                          'account_holder_document_number'],
                                                      )
        return create_bank_account

    def update(self, instance, validated_data):
        pass


class VirtualAccountDepositFormatSerializer(serializers.ModelSerializer):
    class Meta:
        model = VirtualAccountDeposit
        fields = '__all__'


class VirtualAccountDepositSerializer(serializers.Serializer):
    real_account = serializers.CharField(required=True, max_length=150)
    external_account_id = serializers.CharField(required=True, max_length=150)
    external_account_type = serializers.CharField(required=True, max_length=150)
    amount = serializers.DecimalField(required=True, max_digits=20, decimal_places=2)
    asset_type = serializers.IntegerField(required=True)
    deposit_date = serializers.DateField(required=True)

    def validate(self, data):
        try:
            Account.objects.get(external_account_id=data['external_account_id'],
                                external_account_type_id=data['external_account_type'])
            AssetType.objects.get(id=data['asset_type'])
            # TODO: Validar BankAccount v/s real_account
            BankAccount.objects.get(id=data['real_account'])

            return data
        except Exception as e:
            raise serializers.ValidationError(e)

    def create(self, validated_data):
        destiny_account = Account.objects.get(external_account_id=validated_data['external_account_id'],
                                              external_account_type_id=validated_data['external_account_type'])
        journal_transaction_type = JournalTransactionType.objects.get(id=TRANSACTION_TYPE.get('DEPOSIT_REAL_VIRTUAL'))

        bank_account = BankAccount.objects.get(id=validated_data['real_account'])

        ###############################################################################################
        ###############################################################################################
        ###############################################################################################

        virtual_account_deposits = VirtualAccountDeposit.objects.create(amount=validated_data['amount'],
                                                                        deposit_date=validated_data['deposit_date'],
                                                                        asset_type_id=validated_data['asset_type'],
                                                                        account=destiny_account,
                                                                        real_account=bank_account)

        journal = Journal.objects.create(journal_transaction=journal_transaction_type,
                                         gloss=journal_transaction_type.description + ", deposit date:" + str(
                                             validated_data['deposit_date']),
                                         batch=None)

        Posting.objects.create(account=destiny_account, journal=journal, amount=validated_data['amount'],
                               asset_type_id=validated_data['asset_type'])

        UpdateBalanceAccountService.execute(
            {
                'account_id': destiny_account.id
            }
        )

        ###############################################################################################
        ###############################################################################################
        ###############################################################################################

        return virtual_account_deposits

    def update(self, instance, validated_data):
        pass
