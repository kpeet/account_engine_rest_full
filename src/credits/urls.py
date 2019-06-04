from rest_framework.routers import DefaultRouter

# from .views import (BankViewSet, BankAccountTypeViewSet, UserBankAccountViewSet,
#                     EnterpriseBankAccountViewSet, UserViewSet, EnterpriseViewSet)

from account_engine.views import (AccountViewSet, OperationAccountViewSet, AccountTypeViewSet, JournalViewSet, JournalTransactionTypeViewSet, PostingViewSet, JournalTransactionViewSet, BalanceAccountViewSet, BankRegistryViewSet, PositiveBalanceViewSet, VirtualAccountDepositViewSet)
from .views import (CreditsOperationViewSet,InvestmentCostViewSet, CreditsOperationViewSet)
router = DefaultRouter()

# CAPA DE DATOS MOTOR DE CUENTAS

router.register(r'cost', InvestmentCostViewSet, basename='cost')
router.register(r'credit_operation', CreditsOperationViewSet, basename='credit_operation2')

urlpatterns = router.urls