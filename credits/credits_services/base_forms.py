from django import forms
from service_objects.fields import MultipleFormField
from ..models import CreditOperation, Instalment



class BillinPropertiesForm(forms.Field):
    billable = forms.BooleanField(required=True)
    billing_entity = forms.CharField(required=False)

    def clean(self, value):
        return value


class DestinationAccountForm(forms.Field):
    account_type = forms.IntegerField(required=True)
    account_name = forms.CharField(required=True)


class AccountEnginePropertiesForm(forms.Field):
    destination_account = DestinationAccountForm()

    def clean(self, value):
        return value


class CostForm(forms.Form):
    billing_properties = BillinPropertiesForm(required=True)
    account_engine_properties = AccountEnginePropertiesForm(required=True)
    amount = forms.DecimalField(required=True)

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data




class InstalmentsForms(forms.Form):

    def validate_unique_instalment(self, value):

        operation = Instalment.objects.filter(external_instalment_id=value)
        if operation.exists():
            return value
            raise forms.ValidationError("la operación no existe")


    def validate_external_operation_id(self, value):
        """
               Check that the blog post is about Django.
               """
        operation = CreditOperation.objects.filter(external_account_id=value)
        if operation.exists():
            return value
            raise forms.ValidationError("la operación no existe")

    payer_account_id = forms.IntegerField(required=True)
    external_operation_id = forms.IntegerField(required=True)
    instalment_id = forms.IntegerField(required=True,)# validators=[validate_unique_instalment])
    instalment_amount = forms.DecimalField(required=True)  # Capital más interés
    fine_amount = forms.DecimalField(required=True)  # Multa
    pay_date = forms.DateField(required=True)
    asset_type = forms.IntegerField(required=True)

    def clean(self):
        pass


class PaymentToInvestorForm(forms.Form):
    investor_account_id = forms.IntegerField(required=True)
    investor_account_type = forms.IntegerField(required=True)

    investment_id = forms.IntegerField(required=True)
    total_amount = forms.DecimalField(required=True)
    investment_instalment_amount = forms.DecimalField(required=True)
    investment_instalment_cost = MultipleFormField(CostForm, required=False)

    def clean(self):
        pass
