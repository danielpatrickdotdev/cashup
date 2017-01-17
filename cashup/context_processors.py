from .models import Outlet

def cashup(request):
    personnel = getattr(request.user, 'profile', None)
    extra_context = {
        'outlets': Outlet.objects.for_personnel(personnel),
        'business': getattr(personnel, 'business', None),
    }
    return extra_context
