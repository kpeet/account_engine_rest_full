from rest_framework import serializers
from decimal import Decimal
from account_engine.models import (Account, Posting)
from .models import (InvestmentCreditOperation,)


class InvestmentCreditOperationSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvestmentCreditOperation
        fields = '__all__'



class DestinationAccountSerializer(serializers.Serializer):
    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    id = serializers.IntegerField(required=True)


class AccountEnginePropertiesSerializer(serializers.Serializer):
    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    destination_account = DestinationAccountSerializer()


class BillingPropertiesSerializers(serializers.Serializer):
    def update(self, instance, validated_data):
        return validated_data

    def create(self, validated_data):
        return validated_data

    billable = serializers.BooleanField(required=True)
    billing_entity = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    #TODO: TAX, validar con Barbara si es necesario este campo para presentación de info en datos de Facturación


class CostSerializer(serializers.Serializer):
    def update(self, instance, validated_data):
        return validated_data

    def create(self, validated_data):
        return validated_data

    amount = serializers.DecimalField(required=True, max_digits=20, decimal_places=5)
    billing_properties = BillingPropertiesSerializers(required=True)
    account_engine_properties = AccountEnginePropertiesSerializer(required=True)


class JournalOperationInvestmentTransactionSerializer(serializers.Serializer):
    investor_account_id = serializers.CharField(required=True)
    investor_account_type = serializers.IntegerField(required=True)
    external_operation_id = serializers.CharField(required=True)
    investment_id = serializers.IntegerField(required=True)
    total_amount = serializers.DecimalField(required=True, max_digits=20, decimal_places=5)
    investment_amount = serializers.DecimalField(required=True, max_digits=20, decimal_places=5)
    investment_cost = CostSerializer(many=True)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):


        investor_account = Account.objects.get(external_account_id=validated_data['investor_account_id'],
                                               external_account_type_id=validated_data['investor_account_type'])

        try:


            print("investor_account")
            print(str(investor_account))

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

            return investor_account

        except Exception as e:
            raise e

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