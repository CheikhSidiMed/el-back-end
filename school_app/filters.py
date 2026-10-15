import django_filters
from .models import Utilisateur

class UtilisateurFilter(django_filters.FilterSet):
    exclude_roles = django_filters.CharFilter(method='filter_exclude_roles')

    class Meta:
        model = Utilisateur
        fields = []

    def filter_exclude_roles(self, queryset, name, value):
        roles = [r.strip() for r in value.split(',')]
        return queryset.exclude(role__title__in=roles).exclude(extra_roles__title__in=roles)
