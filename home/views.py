import builtins

import logging

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import Q
from .models import Song, SortFilter, SongReview, ContactMessage
from .forms import SongReviewForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


def index(request):
    return render(request, 'home/index.html')


def library(request):
    context = {
        'songs' : Song.objects.all()
    }
    return render(request, 'songs/all.html', context)


def review(request):
    context = {

    }
    return render(request, 'home/review.html', context)


class SongListView(ListView):
    model = Song
    template_name = 'songs/all.html'
    context_object_name = 'songs'


class SongDetailView(DetailView):
    model = Song
    template_name = 'songs/song-detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        song = self.object
        context['average_rating'] = song.average_rating()
        context['review_form'] = SongReviewForm()
        context['reviews'] = song.reviews.select_related('user').all()
        return context


def search(request):
    query = request.GET.get('query', '').strip()
    if not query:
        songs = Song.objects.none()
    elif len(query) > 78:
        songs = Song.objects.none()
    else:
        normalized = query.strip()
        special_prefix = None
        if ':' in normalized:
            prefix, value = normalized.split(':', 1)
            special_prefix = prefix.strip().lower()
            normalized = value.strip()

        if special_prefix == 'raga':
            songs = Song.objects.filter(Raaga__name__icontains=normalized)
        elif special_prefix == 'god':
            songs = Song.objects.filter(god__name__icontains=normalized)
        elif special_prefix == 'sort':
            songs = Song.objects.filter(sort_filter__name__icontains=normalized)
        else:
            songs = Song.objects.filter(
                Q(name__icontains=normalized)
                | Q(description__icontains=normalized)
                | Q(god__name__icontains=normalized)
                | Q(Raaga__name__icontains=normalized)
                | Q(sort_filter__name__icontains=normalized)
            ).distinct().order_by('name')

    if not query:
        messages.error(request, "Please enter a search term to find a song.", extra_tags="danger")
    elif songs.count() == 0:
        messages.error(request, "No search results found. Please refine your query.", extra_tags="danger")

    context = {
        'songs': songs,
        'query': query,
        }
    return render(request, 'songs/search.html', context)


def contact(request):
    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()
        email = (request.POST.get('email') or '').strip()
        subject = (request.POST.get('subject') or '').strip()
        message = (request.POST.get('message') or '').strip()

        if not builtins.all([name, email, subject, message]):
            messages.error(request, 'Please complete all fields before sending your message.', extra_tags='danger')
        else:
            ContactMessage.objects.create(
                name=name,
                email=email,
                subject=subject,
                message=message,
            )

            try:
                send_mail(
                    subject=f'Website inquiry: {subject}',
                    message=f'Name: {name}\nEmail: {email}\n\n{message}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.DEFAULT_FROM_EMAIL],
                    fail_silently=False,
                )
                messages.success(request, 'Thank you for reaching out. Your message has been received and we will be in touch soon.')
            except Exception:
                logger.exception('Failed to send contact email for: %s', email)
                messages.warning(
                    request,
                    'Your message was saved successfully, but the email notification could not be sent right now. The admin can still reply from the dashboard.',
                    extra_tags='warning',
                )
            return redirect('contact')

    return render(request, 'home/contact.html')


@login_required
def favourite_add(request, id):
    song = get_object_or_404(Song, id=id)
    if song.favourite.filter(id=request.user.id).exists():
        song.favourite.remove(request.user)
    else:
        song.favourite.add(request.user)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def song_review(request, pk):
    song = get_object_or_404(Song, pk=pk)
    if request.method == 'POST':
        form = SongReviewForm(request.POST)
        if form.is_valid():
            review, created = SongReview.objects.get_or_create(
                song=song,
                user=request.user,
                defaults={
                    'rating': form.cleaned_data['rating'],
                    'comment': form.cleaned_data['comment'],
                },
            )
            if not created:
                review.rating = form.cleaned_data['rating']
                review.comment = form.cleaned_data['comment']
                review.save()
            messages.success(request, 'Your review has been saved.')
    return redirect('song-detail', pk=song.pk)


def error_404(request, exception):
    return render(request, 'home/404.html')