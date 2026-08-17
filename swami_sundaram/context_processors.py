from django.contrib.auth.models import Group


def admin_menu(request):
    user = getattr(request, 'user', None)
    has_admin_menu = False
    admin_menu_level = None

    try:
        if user and user.is_authenticated:
            if user.is_superuser:
                has_admin_menu = True
                admin_menu_level = 'advanced'
            else:
                # Moderators: either staff or in 'Moderators' group
                in_mod_group = False
                try:
                    in_mod_group = user.groups.filter(name='Moderators').exists()
                except Exception:
                    in_mod_group = False

                if user.is_staff or in_mod_group:
                    has_admin_menu = True
                    admin_menu_level = 'simple'
    except Exception:
        has_admin_menu = False
        admin_menu_level = None

    return {
        'admin_menu_access': has_admin_menu,
        'admin_menu_level': admin_menu_level,
    }
