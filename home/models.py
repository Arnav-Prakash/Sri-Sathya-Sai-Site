from django.db import models
from django.contrib.auth.models import User


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

    def __str__(self):
        return self.name
