from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import Avg


class SortFilter(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(default="Sort Filter Desciption")

    def __str__(self):
        return self.name


class Raaga(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return self.name


class God(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to="god_images", default="default.png")

    def __str__(self):
        return self.name


class Song(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    Raaga = models.ForeignKey(Raaga, on_delete=models.CASCADE, default=1)
    sort_filter = models.ForeignKey(SortFilter, on_delete=models.CASCADE)
    audio_file = models.FileField(upload_to='media/songs', max_length=10000)
    god = models.ForeignKey(God, on_delete=models.CASCADE, default=1)
    lyrics_pdf = models.FileField(upload_to='lyrics', max_length=1000000000, default='lyrics/LYRIC_FILE_NOT_YET_UPLOADED.pdf')
    favourite = models.ManyToManyField(User, related_name='favourite', default=None, blank=True)

    def average_rating(self):
        result = self.reviews.aggregate(avg_rating=Avg('rating'))['avg_rating']
        return round(float(result), 1) if result is not None else 0.0

    def __str__(self):
        return self.name


class SongReview(models.Model):
    song = models.ForeignKey('Song', related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='song_reviews', on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('song', 'user')

    def __str__(self):
        return f'{self.user.username} reviewed {self.song.name} ({self.rating}/5)'


class ContactMessage(models.Model):
    STATUS_NEW = 'new'
    STATUS_REPLIED = 'replied'
    STATUS_CHOICES = [
        (STATUS_NEW, 'New'),
        (STATUS_REPLIED, 'Replied'),
    ]

    name = models.CharField(max_length=255)
    email = models.EmailField()
    subject = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW)
    created_at = models.DateTimeField(auto_now_add=True)
    replied_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} - {self.subject}'
