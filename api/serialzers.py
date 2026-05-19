from rest_framework import serializers
from affiliation.models import AffiliatePackage, Affiliate, UserInvoice




class AffialiatePackageSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = AffiliatePackage
        exclude = ['commissions']