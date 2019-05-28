from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.viewsets import ModelViewSet, ViewSet
from rest_framework.response import Response
from rest_framework import status
from service_objects.errors import InvalidInputsError

from .models import InvestmentCreditOperation, CreditsCost, CreditOperation
from .serializers import InvestmentCreditOperationSerializer, FinancingCreditOperationSerializer, CostSerializer, Cost2Serializer, CreditOperationSerializer,CreditOperationSerializer2, RequestorPaymentSerializer, InstalmentPaymentSerializer, InvestorPaymentFromOperation

class InvestmentCostViewSet(ModelViewSet):
    queryset = CreditsCost.objects.all()
    serializer_class = Cost2Serializer


class CreditsOperationViewSet(ViewSet):
    def list(self, request):

        queryset = CreditOperation.objects.all()
        serializer_class = CreditOperationSerializer(queryset, many=True)
        return Response(serializer_class.data)

    def create(self, request):
        serializer = CreditOperationSerializer2(data=request.data)
        if serializer.is_valid():
            serializer.save()

            return Response(serializer.validated_data)

        return Response({
            'status': 'Bad request',
            'message': serializer.errors
        }, )

    def retrieve(self, request, pk=None):
        queryset = CreditOperation.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        serializer = CreditOperationSerializer(user)
        return Response(serializer.data)

    @action(detail=False,methods=['post'] )
    def financing_credit_operation(self, request):
        like_api = True
        PROCESS_DATA_OK_FOR_SNS = "OK"
        serializer = FinancingCreditOperationSerializer(data=request.data)
        try:
            if serializer.is_valid():
                serializer.save()

                return Response(serializer.validated_data)
            else:
                return Response({
                    'status': 'Bad request',
                    'message': serializer.errors
                }, )

        except InvalidInputsError as e:
            if like_api:
                return Response(e.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(PROCESS_DATA_OK_FOR_SNS, status=status.HTTP_200_OK)

        except Exception as e:
            if like_api:
                return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(PROCESS_DATA_OK_FOR_SNS, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def requestor_payment(self, request):
        like_api = True
        PROCESS_DATA_OK_FOR_SNS = "OK"
        serializer = RequestorPaymentSerializer(data=request.data)
        try:
            if serializer.is_valid():
                serializer.save()

                return Response(serializer.validated_data)
            else:
                return Response({
                    'status': 'Bad request',
                    'message': serializer.errors
                }, )

        except InvalidInputsError as e:
            if like_api:
                return Response(e.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(PROCESS_DATA_OK_FOR_SNS, status=status.HTTP_200_OK)

        except Exception as e:
            if like_api:
                return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(PROCESS_DATA_OK_FOR_SNS, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def payment_instalment(self, request):
        like_api = True
        PROCESS_DATA_OK_FOR_SNS = "OK"
        serializer = InstalmentPaymentSerializer(data=request.data)
        try:
            if serializer.is_valid():
                serializer.save()

                return Response(serializer.validated_data)
            else:
                return Response({
                    'status': 'Bad request',
                    'message': serializer.errors
                }, )

        except InvalidInputsError as e:
            if like_api:
                return Response(e.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(PROCESS_DATA_OK_FOR_SNS, status=status.HTTP_200_OK)

        except Exception as e:
            if like_api:
                return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(PROCESS_DATA_OK_FOR_SNS, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def investor_payment_from_instalment(self, request):
        like_api = True
        PROCESS_DATA_OK_FOR_SNS = "OK"
        serializer = InvestorPaymentFromOperation(data=request.data)
        try:
            if serializer.is_valid():
                serializer.save()

                return Response(serializer.validated_data)
            else:
                return Response({
                    'status': 'Bad request',
                    'message': serializer.errors
                }, )

        except InvalidInputsError as e:
            if like_api:
                return Response(e.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(PROCESS_DATA_OK_FOR_SNS, status=status.HTTP_200_OK)

        except Exception as e:
            if like_api:
                return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(PROCESS_DATA_OK_FOR_SNS, status=status.HTTP_200_OK)