from django import forms

from .models import SongReview


class SongReviewForm(forms.ModelForm):
    rating = forms.ChoiceField(
        choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')],
        label='Rating',
        widget=forms.Select(attrs={'class': 'rating-select'}),
    )

    class Meta:
        model = SongReview
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Share your thoughts about this bhajan...',
            })
        }
        labels = {
            'comment': 'Review',
        }
