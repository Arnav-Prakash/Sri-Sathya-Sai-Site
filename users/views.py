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
from home.models import Song, SongReview
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from .moderation_forms import SongModerationForm, ReviewModerationForm, UserModerationForm
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.contrib.auth import logout
from home.models import ContactMessage
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt


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


@login_required
def admin_menu(request):
    user = request.user
    # Advanced access for superusers
    if user.is_superuser:
        level = 'advanced'
    else:
        # Simple access for staff or Moderators group
        try:
            is_moderator = user.groups.filter(name='Moderators').exists()
        except Exception:
            is_moderator = False

        if user.is_staff or is_moderator:
            level = 'simple'
        else:
            return HttpResponseForbidden('You do not have access to the admin menu.')

    # Gather basic stats for the dashboard
    context = {
        'level': level,
        'song_count': Song.objects.count(),
        'user_count': get_user_model().objects.count(),
        'review_count': SongReview.objects.count(),
    }

    return render(request, 'admin_menu/dashboard.html', context)


def _is_moderator(user):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    try:
        return user.is_staff or user.groups.filter(name='Moderators').exists()
    except Exception:
        return False


@user_passes_test(lambda u: _is_moderator(u))
def mod_songs_list(request):
    songs = Song.objects.all().order_by('-id')
    paginator = Paginator(songs, 25)
    page = request.GET.get('page')
    songs_page = paginator.get_page(page)
    return render(request, 'admin_menu/songs_list.html', {'songs': songs_page})


@user_passes_test(lambda u: _is_moderator(u))
@require_http_methods(['GET', 'POST'])
def mod_song_create(request):
    if request.method == 'POST':
        form = SongModerationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('mod_songs_list')
    else:
        form = SongModerationForm()
    return render(request, 'admin_menu/song_create.html', {'form': form})


@user_passes_test(lambda u: _is_moderator(u))
@require_http_methods(['GET', 'POST'])
def mod_song_edit(request, pk):
    song = get_object_or_404(Song, pk=pk)
    if request.method == 'POST':
        form = SongModerationForm(request.POST, request.FILES, instance=song)
        if form.is_valid():
            form.save()
            return redirect('mod_songs_list')
    else:
        form = SongModerationForm(instance=song)
    return render(request, 'admin_menu/song_form.html', {'form': form, 'song': song})


@user_passes_test(lambda u: _is_moderator(u))
def mod_song_delete(request, pk):
    song = get_object_or_404(Song, pk=pk)
    if request.method == 'POST':
        song.delete()
        return redirect('mod_songs_list')
    return render(request, 'admin_menu/song_confirm_delete.html', {'song': song})


@user_passes_test(lambda u: _is_moderator(u))
def mod_reviews_list(request):
    reviews = SongReview.objects.select_related('song', 'user').all().order_by('-created_at')
    paginator = Paginator(reviews, 25)
    reviews_page = paginator.get_page(request.GET.get('page'))
    return render(request, 'admin_menu/reviews_list.html', {'reviews': reviews_page})


@user_passes_test(lambda u: _is_moderator(u))
@require_http_methods(['GET', 'POST'])
def mod_review_create(request):
    if request.method == 'POST':
        form = ReviewModerationForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            # moderator must select song and user in the form; ensure saved
            review.save()
            return redirect('mod_reviews_list')
    else:
        form = ReviewModerationForm()
    return render(request, 'admin_menu/review_create.html', {'form': form})


@user_passes_test(lambda u: _is_moderator(u))
def mod_review_delete(request, pk):
    review = get_object_or_404(SongReview, pk=pk)
    if request.method == 'POST':
        review.delete()
        return redirect('mod_reviews_list')
    return render(request, 'admin_menu/review_confirm_delete.html', {'review': review})


@user_passes_test(lambda u: _is_moderator(u))
def mod_users_list(request):
    users_qs = User.objects.order_by('-id')
    paginator = Paginator(users_qs, 25)
    users_page = paginator.get_page(request.GET.get('page'))
    return render(request, 'admin_menu/users_list.html', {'users': users_page})


@user_passes_test(lambda u: _is_moderator(u))
def mod_contacts_list(request):
    contacts = ContactMessage.objects.all().order_by('-created_at')
    paginator = Paginator(contacts, 25)
    contacts_page = paginator.get_page(request.GET.get('page'))
    return render(request, 'admin_menu/contacts_list.html', {'contacts': contacts_page})


@user_passes_test(lambda u: _is_moderator(u))
@require_http_methods(['POST'])
def mod_contact_mark_replied(request, pk):
    contact = get_object_or_404(ContactMessage, pk=pk)
    contact.status = ContactMessage.STATUS_REPLIED
    contact.replied_at = timezone.now()
    contact.save()
    return redirect('mod_contacts_list')


@user_passes_test(lambda u: _is_moderator(u))
@require_http_methods(['GET', 'POST'])
def mod_user_edit(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserModerationForm(request.POST, instance=user_obj)
        if form.is_valid():
            form.save()
            return redirect('mod_users_list')
    else:
        form = UserModerationForm(instance=user_obj)
    return render(request, 'admin_menu/user_form.html', {'form': form, 'user_obj': user_obj})


@user_passes_test(lambda u: _is_moderator(u))
def mod_user_toggle_active(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user_obj.is_active = not user_obj.is_active
        user_obj.save()
    return redirect('mod_users_list')


@login_required
def logout_view(request):
    # Prefer POST for logout; accept GET for convenience
    if request.method == 'POST' or request.method == 'GET':
        logout(request)
        return redirect('home')
    return redirect('home')