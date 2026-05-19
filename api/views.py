from rest_framework.decorators import APIView
from rest_framework.response import Response
from .serialzers import AffialiatePackageSerializer
from rest_framework import status
from rest_framework import generics, mixins
from affiliation.models import AffiliatePackage
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser






class AffiliateListView(generics.ListAPIView):
    queryset = AffiliatePackage.objects.all()
    serializer_class = AffialiatePackageSerializer
    # permission_classes = [IsAuthenticatedOrReadOnly]





class AffiliateDetail(mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,generics.GenericAPIView):
    queryset = AffiliatePackage.objects.all()
    serializer_class = AffialiatePackageSerializer
    # permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)