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

class Country(models.Model):
    name = models.CharField(blank=False, null=False, max_length=255)


class State(models.Model):
    name = models.CharField(blank=False, null=False, max_length=255)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)


class City(models.Model):
    name = models.CharField(blank=False, null=False, max_length=255)
    state = models.ForeignKey(State, on_delete=models.CASCADE)
