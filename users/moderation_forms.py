from django import forms
from home.models import Song, SongReview
from django.contrib.auth.models import User


class SongModerationForm(forms.ModelForm):
    class Meta:
        model = Song
        fields = ['name', 'description', 'Raaga', 'sort_filter', 'god', 'audio_file', 'lyrics_pdf']


class ReviewModerationForm(forms.ModelForm):
    song = forms.ModelChoiceField(queryset=Song.objects.all(), required=True)
    user = forms.ModelChoiceField(queryset=User.objects.all(), required=True)

    class Meta:
        model = SongReview
        fields = ['song', 'user', 'rating', 'comment']


class UserModerationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['is_active', 'is_staff']
