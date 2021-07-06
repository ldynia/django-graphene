# Description

Demo project for testing GraphQL v2 and v3 along with related packages.

# Instructions

```bash
$ docker-compose up
$ docker exec django-demo-app python manage.py seed
```

# Links

- [Cities](https://gist.githubusercontent.com/Lwdthe1/81818d30d23f012628aac1cdf672627d/raw/45dc8bee7b4fc349ec87931100e0f258bb59f8ea/usaCities.js)
- [Movies](https://github.com/hjorturlarsen/IMDB-top-100/blob/master/data/movies.json)

# Requirements

Depending what version of Graphine you want to work with comment/uncomment libraries in `requirements.txt`

**requirements.txt**
```bash
# # Graphene 2
# django-debug-toolbar==3.2.1
# git+https://github.com/jazzband/django-silk@master
# Django==3.2
# graphene-django-optimizer==0.8.0
# graphene-django==2.15.0
# psycopg2-binary==2.9.1
# requests==2.25.1

# Graphene 3
django-debug-toolbar==3.2.1
git+https://github.com/jazzband/django-silk@master
Django==3.2
git+https://github.com/sebsasto/graphene-django-optimizer@master
graphene-django==3.0.0b7
psycopg2-binary==2.9.1
requests==2.25.1
```

# Benchmarking

### Query  1

```graphql
{
  allCities{
    name
    state {
      name
      country {
        name
      }
    }
  }
}
```

```python
import graphene_django_optimizer as gql_optimizer

from demo.models import City

# Cities > State > Country
>>> City.objects.all()[:50]
>>> City.objects.all().select_related('state__country')
>>> City.objects.all().prefetch_related('state__country')
>>> gql_optimizer.query(City.objects.all(), info)
```

| # | Graphene | Optimization |  GQL | #SQL | Time Min | Time Max | #Joins |
|-|-|-|-|-|-|-|-|
| 1 | v2 | - | Q1 | n+1 | timeout | timeout | 0 |
| 2 | v2 | prefetch_related | Q1 | 3 | 24 ms | 79 ms | 0 |
| 3 | v2 | select_related | Q1 | 1 | 12 ms | 18 ms | 2 |
| 4 | v2 | gql_optimizer.query | Q1 | 1 | 12 ms | 20 ms | 2 |
|-|-|-|-|-|-|-|-|
| 5 | v3 | - | Q1 | n+1 | timeout | timeout | 0 |
| 6 | v3 | prefetch_related | Q1 | 3 | 17 ms | 79 ms | 0 |
| 7 | v3 | select_related | Q1 | 1 | 12 ms | 17 ms | 2 |
| 8 | v3 | gql_optimizer.query | Q1 | 1 | 11 ms | 19 ms | 2 |
