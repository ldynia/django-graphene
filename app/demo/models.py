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


class Continent(models.Model):
    name = models.CharField(blank=False, null=False, max_length=255)


class Country(models.Model):
    continent = models.ForeignKey(Continent, on_delete=models.CASCADE)
    name = models.CharField(blank=False, null=False, max_length=255)


class State(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    name = models.CharField(blank=False, null=False, max_length=255)


class City(models.Model):
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    name = models.CharField(blank=False, null=False, max_length=255)


class District(models.Model):
    city = models.ForeignKey(City, related_name='district', on_delete=models.CASCADE)
    name = models.CharField(blank=False, null=False, max_length=255)


class Mayor(models.Model):
    city = models.OneToOneField(City, primary_key=True, related_name='mayor', on_delete=models.CASCADE)
    first_name = models.CharField(blank=False, null=False, max_length=32)
    last_name = models.CharField(blank=False, null=False, max_length=32)

    @property
    def full_name(self):
        return self.first_name + ' ' + self.last_name
