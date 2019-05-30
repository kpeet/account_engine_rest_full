from rest_framework import serializers
from decimal import Decimal
from account_engine.models import (Account, Posting, BankAccount)
from .models import (InvestmentCreditOperation, CreditsCost, CreditOperation, Instalment)
from .credits_services.financing_services import FinanceOperationByInvestmentTransaction
from .credits_services.requestor_payment_service import RequesterPaymentFromOperation
from .credits_services.instalment_payment_service import InstalmentPayment
from .credits_services.investment_instalment_payment_services import InvestorPaymentFromOperation
import logging

ASSET_TYPE = 1


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
    # TODO: TAX, validar con Barbara si es necesario este campo para presentación de info en datos de Facturación


class Cost2Serializer(serializers.ModelSerializer):
    class Meta:
        model = CreditsCost
        fields = '__all__'


class CostSerializer(serializers.Serializer):
    def update(self, instance, validated_data):
        return validated_data

    def create(self, validated_data):
        return validated_data

    amount = serializers.DecimalField(required=True, max_digits=20, decimal_places=2)
    billing_properties = BillingPropertiesSerializers(required=True)
    account_engine_properties = AccountEnginePropertiesSerializer(required=True)


class FinancingCreditOperationSerializer(serializers.Serializer):
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


class CreditOperationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditOperation
        fields = ('id', 'financing_amount', 'requestor_account', 'external_account_id', 'external_account_type_id')
        read_only_fields = ('state',)


class CreditOperationSerializer2(serializers.Serializer):
    EXTERNAL_REQUESTOR_ACCOUNT_TYPE = 2

    operation_id = serializers.CharField(required=True, source='external_account_id', max_length=150)
    financing_amount = serializers.DecimalField(required=True, max_digits=20, decimal_places=2)
    requester_id = serializers.IntegerField(required=True, source='requester_account_id')

    def validate(self, data):
        try:

            Account.objects.get(external_account_id=data['requester_account_id'],
                                external_account_type_id=CreditOperationSerializer2.EXTERNAL_REQUESTOR_ACCOUNT_TYPE)

            operation = CreditOperation.objects.filter(external_account_id=data['external_account_id'],
                                                       external_account_type_id=CreditOperation.ACCOUNT_TYPE)
            if operation.exists():
                raise serializers.ValidationError("operation_id ya ingresado")

            if data['financing_amount'] < 1:
                raise serializers.ValidationError("Monto de financiamiento Insuficiente ")

            return data

        except Exception as e:
            raise serializers.ValidationError(str(e))

    def create(self, validated_data):
        requester = Account.objects.get(external_account_id=validated_data['requester_account_id'],
                                        external_account_type_id=CreditOperationSerializer2.EXTERNAL_REQUESTOR_ACCOUNT_TYPE)

        name = "Operacion " + str(validated_data['requester_account_id'])
        create_operation = CreditOperation.objects.create(external_account_id=validated_data['external_account_id'],
                                                          name=name,
                                                          requestor_account=requester,
                                                          financing_amount=validated_data['financing_amount'],
                                                          external_account_type_id=CreditOperation.ACCOUNT_TYPE)
        return create_operation

    def update(self, instance, validated_data):
        pass


class FinancingCreditOperationSerializer(serializers.Serializer):
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

            financing_response = FinanceOperationByInvestmentTransaction.execute(
                {
                    'account': investor_account.id,
                    'investment_id': validated_data['investment_id'],
                    'total_amount': validated_data['total_amount'],
                    'investment_amount': validated_data['investment_amount'],
                    'investment_costs': validated_data['investment_cost'],
                    'external_operation_id': validated_data['external_operation_id'],
                    # TODO: definir el asset_type según sistema con que interactura
                    'asset_type': 1
                }
            )
            return financing_response

        except Exception as e:
            raise e


class RequestorPaymentSerializer(serializers.Serializer):
    # TODO: ASSET TYPE DEBE SER DEFINIDO EN ALGUN PUNTO PARA DIFERENCIAS INGRESOS CON OTROS TIPOS DE MONEDA

    def positive_number(value):
        if value < Decimal(0):
            raise serializers.ValidationError("Must be positive ")

    requester_account_id = serializers.IntegerField(required=True)
    requester_account_type = serializers.IntegerField(required=True)
    external_operation_id = serializers.IntegerField(required=True)
    total_amount = serializers.DecimalField(allow_null=False, default=Decimal('0.00000'), max_digits=20,
                                            decimal_places=5, validators=[positive_number])
    transfer_amount = serializers.DecimalField(allow_null=False, default=Decimal('0.00000'), max_digits=20,
                                               decimal_places=5, validators=[positive_number])
    requester_cost = CostSerializer(many=True)

    def validate(self, data):
        # TODO: Separar Validaciones de negocio
        try:
            CreditOperation.objects.filter(external_account_type_id=data['external_operation_id'])

            requester_account = Account.objects.get(external_account_id=data['requester_account_id'],
                                                    external_account_type_id=data['requester_account_type'])

            bank_account = BankAccount.objects.filter(account=requester_account)[0:1].get()

        except BankAccount.DoesNotExist as e:
            raise serializers.ValidationError("No hay cuenta Bancaria asociada al solicitante")

        except Exception as e:
            raise serializers.ValidationError(str(e))

        return data

    def create(self, validated_data):
        requester_account = Account.objects.get(external_account_id=validated_data['requester_account_id'],
                                                external_account_type_id=validated_data['requester_account_type'])

        requester_payment_from_operation = RequesterPaymentFromOperation.execute(
            {
                "account": requester_account.id,
                "total_amount": validated_data['total_amount'],
                "transfer_amount": validated_data['transfer_amount'],
                "external_operation_id": validated_data['external_operation_id'],
                "asset_type": RequestorPaymentSerializer.ASSET_TYPE,
                "requester_costs": validated_data['requester_cost']
            }
        )

        return requester_payment_from_operation

    def update(self, instance, validated_data):
        pass


class InstalmentPaymentSerializers(serializers.Serializer):
    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        print("Flag 2")
        return validated_data

    payer_account_id = serializers.IntegerField(required=True)
    payer_account_type = serializers.IntegerField(required=True)
    external_operation_id = serializers.IntegerField(required=True)
    instalment_id = serializers.IntegerField(required=True)
    instalment_amount = serializers.DecimalField(required=True, max_digits=20, decimal_places=5)
    fine_amount = serializers.DecimalField(required=True, max_digits=20, decimal_places=5)
    pay_date = serializers.DateField(required=True)


class InstalmentPaymentSerializer(serializers.Serializer):
    instalments = InstalmentPaymentSerializers(many=True)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        print("Flag 3")
        instalments = validated_data['instalments']
        instalment_list_to_services = []
        for instalment in instalments:
            payer_account = Account.objects.get(external_account_id=instalment['payer_account_id'],
                                                external_account_type_id=instalment['payer_account_type'])

            external_operation_id = instalment['external_operation_id']
            instalment_id = instalment['instalment_id']
            instalment_amount = instalment['instalment_amount']
            fine_amount = instalment['fine_amount']
            pay_date = instalment['pay_date']

            instalment_list_to_services.append(
                {
                    "payer_account_id": payer_account.id,
                    "external_operation_id": external_operation_id,
                    "instalment_id": instalment_id,
                    "instalment_amount": instalment_amount,
                    "fine_amount": fine_amount,
                    "pay_date": pay_date,
                    "asset_type": 1
                }
            )
        print("Flag 4")
        requester_payment_from_operation = InstalmentPayment.execute(
            {
                "instalment_list_to_pay": instalment_list_to_services,

            }
        )

        return requester_payment_from_operation


class PaymentToInvestor(serializers.Serializer):
    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    investor_account_id = serializers.IntegerField(required=True)
    investor_account_type = serializers.IntegerField(required=True)
    investment_id = serializers.IntegerField(required=True)
    total_amount = serializers.DecimalField(required=True, max_digits=20, decimal_places=5)
    investment_instalment_amount = serializers.DecimalField(required=True, max_digits=20, decimal_places=5)
    investment_instalment_cost = CostSerializer(many=True)


class JournalInvestorPaymentFromInstalmentOperationSerializer(serializers.Serializer):
    log = logging.getLogger("info_logger")

    def positive_number(value):
        if value < Decimal(0):
            raise serializers.ValidationError("Must be positive ")

    def validate_external_operation_id(self, value):
        """
               Check that the blog post is about Django.
               """

        print("validate_external_operation_id")
        print(value)
        operation = CreditOperation.objects.filter(external_account_id=value)
        if operation.exists():
            return value
        raise serializers.ValidationError("la operación no existe")

    instalment_id = serializers.IntegerField(required=True)
    instalment_amount = serializers.DecimalField(required=True, max_digits=20, decimal_places=2,
                                                 validators=[positive_number])
    external_operation_id = serializers.IntegerField(required=True, )
    investors = PaymentToInvestor(many=True, required=True)

    def create(self, validated_data):

        # requester_account = Account.objects.get(external_account_id=validated_data['requester_account_id'],
        #                                         external_account_type_id=validated_data['requester_account_type'])
        print("external_operation_id")
        print(str(validated_data['external_operation_id']))

        self.log.info("SEND TO InvestorPaymentFromOperation SERVICE" + str(validated_data['external_operation_id']))

        requester_payment_from_operation = InvestorPaymentFromOperation.execute(
            {
                "external_credit_operation_id": validated_data['external_operation_id'],
                "instalment_amount": validated_data['instalment_amount'],
                "instalment_id": validated_data['instalment_id'],
                "investors": validated_data['investors'],
                "asset_type": ASSET_TYPE
            }
        )

        return requester_payment_from_operation

    def update(self, instance, validated_data):
        pass
