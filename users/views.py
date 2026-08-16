from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from .forms import UserRegisterForm, UserUpdateForm, ProfilePictureForm
from .models import AdminProfile
from home.models import Song


def register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            verification_url = request.build_absolute_uri(
                f"/activate/{uid}/{token}/"
            )
            send_mail(
                subject='Verify your Sri Sathya Sai Bhajans account',
                message=(
                    f'Hello {user.username},\n\n'
                    'Thanks for creating your account. Please verify your email by visiting:\n'
                    f'{verification_url}\n\n'
                    'Once verified, you can sign in and begin exploring the library.'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            messages.success(request, 'Your account has been created. Please check your email to verify it before signing in.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})


def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = get_user_model().objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save(update_fields=['is_active'])
        messages.success(request, 'Your email has been verified successfully. You can now sign in.')
        return redirect('login')

    messages.error(request, 'This verification link is invalid or expired.')
    return redirect('register')


@login_required
def profile(request):
    profile_obj = getattr(request.user, 'admin_profile', None)
    if profile_obj is None:
        profile_obj = AdminProfile.objects.create(user=request.user)

    context = {
        'favourite_count': request.user.favourite.count(),
        'library_count': Song.objects.count(),
        'profile': profile_obj,
    }
    return render(request, 'users/profile.html', context)


@login_required
def profile_update(request):
    profile_obj = getattr(request.user, 'admin_profile', None)
    if profile_obj is None:
        profile_obj = AdminProfile.objects.create(user=request.user)

    if request.method == "POST":
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfilePictureForm(request.POST, request.FILES, instance=profile_obj)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfilePictureForm(instance=profile_obj)

    context = {
        'u_form': u_form,
        'p_form': p_form,
    }

    return render(request, 'users/profile_update.html', context)


@login_required
def favourite_list(request):
    new = Song.objects.filter(favourite=request.user)
    return render(request, 'users/favourites.html', {'new': new})