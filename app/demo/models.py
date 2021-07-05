from django.db import models
from django.contrib.postgres.fields import ArrayField


class Actor(models.Model):
    first_name = models.CharField(blank=True, null=True, max_length=32)
    last_name = models.CharField(blank=True, null=True, max_length=64)
    nick_name = models.CharField(blank=True, null=True, max_length=64)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Movie(models.Model):
    title = models.CharField(max_length=255, blank=False, null=False)
    rating = models.FloatField(blank=True, null=True)
    year = models.PositiveSmallIntegerField(blank=True, null=True)
    genre = ArrayField(models.CharField(blank=True, max_length=255), size=16)
    actors = models.ManyToManyField(Actor)

    def __str__(self):
        return self.title
