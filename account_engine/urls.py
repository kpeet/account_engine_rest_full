from rest_framework.routers import DefaultRouter
from credits.urls import router as credits_router

from .views import (AccountViewSet, OperationAccountViewSet, AccountTypeViewSet, JournalViewSet, JournalTransactionTypeViewSet, PostingViewSet, JournalTransactionViewSet, BalanceAccountViewSet, BankRegistryViewSet, PositiveBalanceViewSet, VirtualAccountDepositViewSet)

router = DefaultRouter()

# CAPA DE DATOS MOTOR DE CUENTAS
router.register(r'accounts', AccountViewSet)

#router.register(r'operation_account', OperationAccountViewSet)
router.register(r'account_type', AccountTypeViewSet)
router.register(r'journals', JournalViewSet)
router.register(r'journal_transaction_type', JournalTransactionTypeViewSet)
router.register(r'postings', PostingViewSet, basename='posting')


router.register(r'journal_transactions', JournalTransactionViewSet,basename='journal_transaction')

router.register(r'balance_account', BalanceAccountViewSet)

router.register(r'positive_balances', PositiveBalanceViewSet, base_name="positive_balance")
#path('account/positive_balance/external_account_type/<int:entity_type>/', PositiveBalanceAccount.as_view()),

router.register(r'virtual_account_deposits', VirtualAccountDepositViewSet,base_name="virtual_account_deposit")
#path('virtual_account_deposit/', VirtualAccountDeposit.as_view(), name='virtual-account-deposit'),

# Bank Registry
router.register(r'bank', BankRegistryViewSet)#path('account/bank_registry/', BankRegistry.as_view())

router.registry.extend(credits_router.registry)





urlpatterns = router.urls