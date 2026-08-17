from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from django.urls import reverse

def AdminRestrictMiddleware(get_response):
    def middleware(request):
        path = request.path
        if path.startswith('/admin/'):
            user = getattr(request, 'user', None)
            # Allow superusers always
            if user and user.is_authenticated and user.is_superuser:
                return get_response(request)
            # Allow users in Developers group
            try:
                if user and user.is_authenticated and user.groups.filter(name='Developers').exists():
                    return get_response(request)
            except Exception:
                pass

            # Otherwise deny access to admin
            if user and user.is_authenticated:
                return HttpResponseForbidden('The admin site is restricted to developers.')
            else:
                return redirect(f"{reverse('login')}?next={request.path}")

        return get_response(request)

    return middleware
