from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.viewsets import ModelViewSet, ViewSet
from rest_framework.response import Response

from .models import InvestmentCreditOperation
from .serializers import InvestmentCreditOperationSerializer, JournalOperationInvestmentTransactionSerializer




class CreditsOperationViewSet(ViewSet):



    def list(self, request):

        queryset = InvestmentCreditOperation.objects.all()
        serializer = InvestmentCreditOperationSerializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = JournalOperationInvestmentTransactionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()

            return Response(serializer.validated_data)

        return Response({
            'status': 'Bad request',
            'message': serializer.errors
        }, )

    #
    # @action(detail=False, methods=['get'])
    # def positive_balance(self, request, pk=None):
    #     # investment = get_object_or_404(Account, id=pk)
    #     return Response({'status': 'password set'})
    #
    #
    #
    # @action(methods=['post'], detail=True)
    # def positive_balance2(self, request, pk=None):
    #     print("pk!!!!!!!")
    #     print(pk)
    #     # investment = get_object_or_404(Account, id=pk)
    #     # investment, confirmed = investment.confirm()
    #     # serializer = AccountSerializer(investment)  # DWHBalanceAccountSerializer(investment)
    #     return Response({'status': 'password set'})

