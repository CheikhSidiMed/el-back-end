import django_filters
from .models import Utilisateur

class UtilisateurFilter(django_filters.FilterSet):
    exclude_roles = django_filters.CharFilter(method='filter_exclude_roles')

    class Meta:
        model = Utilisateur
        fields = []

    def filter_exclude_roles(self, queryset, name, value):
        roles = value.split(',')
        return queryset.exclude(role__title__in=roles)
import django_filters
from .models import Utilisateur

class UtilisateurFilter(django_filters.FilterSet):
    exclude_roles = django_filters.CharFilter(method='filter_exclude_roles')

    class Meta:
        model = Utilisateur
        fields = []

    def filter_exclude_roles(self, queryset, name, value):
        roles = value.split(',')
        return queryset.exclude(role__title__in=roles)
