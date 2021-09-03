from django.contrib import admin

from demo.models import Actor
from demo.models import City
from demo.models import Continent
from demo.models import Country
from demo.models import District
from demo.models import Governor
from demo.models import Mayor
from demo.models import Movie
from demo.models import State


class MovieAdmin(admin.ModelAdmin):

    def get_queryset(self, request):
        qs = super().get_queryset(request).order_by('id')
        return qs.prefetch_related('actors')


class CompanyInline(admin.TabularInline):

    model = Movie.actors.through


class ActorAdmin(admin.ModelAdmin):

    inlines = [CompanyInline]

    def get_queryset(self, request):
        return super().get_queryset(request).order_by('id')


class CityAdmin(admin.ModelAdmin):

    def get_queryset(self, request):
        qs = super().get_queryset(request).order_by('id')
        return qs.select_related('state__country__continent', 'mayor').prefetch_related('district__city')

# Film domain
admin.site.register(Actor, ActorAdmin)
admin.site.register(Movie, MovieAdmin)

# City domain
admin.site.register(City, CityAdmin)
admin.site.register(Continent)
admin.site.register(Country)
admin.site.register(District)
admin.site.register(Governor)
admin.site.register(Mayor)
admin.site.register(State)