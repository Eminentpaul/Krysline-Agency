from django.shortcuts import render
from affiliation.models import AffiliatePackage

# Create your views here.
def package(request):
    packages = AffiliatePackage.objects.all().order_by('price')


    context = {
        "packages": packages
    }

    return render(request, 'base/plans.html', context)


def _404(request, exception):
    return render(request, '404.html', {})