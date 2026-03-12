from django.forms import ModelForm
from authentication.models import User
from users.models import Withdrawal
from affiliation.models import Affiliate, AffiliatePackage, PropertyTransaction


class UserUpdateForm(ModelForm):
    class Meta:
        model = User
        fields = ['user_type', 'is_active']




class WithdrawUpdateForm(ModelForm):
    class Meta:
        model = Withdrawal
        fields = ['status']



class AffiliatePackageUpdateForm(ModelForm):
    class Meta:
        model = AffiliatePackage 
        fields = "__all__"
        exclude = ['commissions', 'generations']


class PropertyTransactionForm(ModelForm):
    class Meta:
        model = PropertyTransaction
        fields = "__all__"
        exclude = ['affiliate']


class AffilliateForm(ModelForm):
    class Meta:
        model = Affiliate
        fields = ['is_active']