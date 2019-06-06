from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import get_object_or_404
from rest_framework.viewsets import ModelViewSet, ViewSet
from rest_framework.response import Response
from rest_framework import status
from django.db.models import F
from .models import Account, OperationAccount, AccountType, Journal, JournalTransactionType, Posting, DWHBalanceAccount, \
    BankAccount,VirtualAccountDeposit
from .serializers import AccountSerializer, OperationAccountSerializer, AccountTypeSerializer, JournalSerializer, \
    JournalTransactionTypeSerializer, PostingSerializer, JournalOperationInvestmentTransactionSerializer, \
    DWHBalanceAccountSerializer, BankRegistrySerializer,BankRegistrySerializer2, VirtualAccountDepositSerializer, \
    VirtualAccountDepositFormatSerializer


class AccountViewSet(ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer

    @action(detail=True, )
    def posting_history(self, request, pk=None):
        queryset = Posting.objects.select_related('journal').values('journal__batch__batch_transaction__description',
                                                                    'journal__gloss',
                                                                    'amount',
                                                                    'journal__batch__batch_transaction',
                                                                    'created_at').filter(account_id=pk).order_by('-created_at')
        return Response(queryset)


class OperationAccountViewSet(ModelViewSet):
    queryset = OperationAccount.objects.all()
    serializer_class = OperationAccountSerializer


class AccountTypeViewSet(ModelViewSet):
    queryset = AccountType.objects.all()
    serializer_class = AccountTypeSerializer

    @action(detail=True, )
    def positive_balance(self, request, pk=None):
        positive_balance_accounts = DWHBalanceAccount.objects.values('account__name', ).filter(
            balance_account_amount__gt=0, account__external_account_type=pk).annotate(
            account_id=F('account__external_account_id'), account_type=F('account__external_account_type'),
            balance_account=F('balance_account_amount'))

        return Response(positive_balance_accounts)


class JournalViewSet(ModelViewSet):
    queryset = Journal.objects.all()
    serializer_class = JournalSerializer


class JournalTransactionTypeViewSet(ModelViewSet):
    queryset = JournalTransactionType.objects.all()
    serializer_class = JournalTransactionTypeSerializer


class PostingViewSet(ModelViewSet):
    queryset = Posting.objects.all()
    serializer_class = PostingSerializer


class JournalTransactionViewSet(ModelViewSet):
    queryset = Posting.objects.all()
    serializer_class = JournalOperationInvestmentTransactionSerializer


class BalanceAccountViewSet(ModelViewSet):
    queryset = DWHBalanceAccount.objects.all()
    serializer_class = DWHBalanceAccountSerializer


class BankRegistryViewSet(ViewSet):
    def list(self, request):

        queryset = BankAccount.objects.all()
        serializer_class = BankRegistrySerializer(queryset, many=True)
        return Response(serializer_class.data)

    def create(self, request):
        serializer = BankRegistrySerializer2(data=request.data)
        if serializer.is_valid():
            serializer.save()

            return Response(serializer.validated_data,status=status.HTTP_201_CREATED)

        return Response({
            'status': 'Bad request',
            'message': serializer.errors
        }, )


class PositiveBalanceViewSet(ModelViewSet):
    queryset = DWHBalanceAccount.objects.all()
    serializer_class = DWHBalanceAccountSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('account__external_account_type',)


class VirtualAccountDepositViewSet(ViewSet):

    def list(self, request):
        queryset = VirtualAccountDeposit.objects.all()
        serializer = VirtualAccountDepositFormatSerializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = VirtualAccountDepositSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()

            return Response(serializer.validated_data)

        return Response({
            'status': 'Bad request',
            'message': serializer.errors
        }, )
