from django_filters.rest_framework import FilterSet, filters
from recipes.models import Recipe, Tag
from users.models import User
from rest_framework.filters import SearchFilter

class IngredientSearchFilter(SearchFilter):
    """Поиск по названию."""

    search_param = "name"


class RecipeFilter(FilterSet):
    """Фильтр рецептов."""

    tag = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_list = filters.BooleanFilter(
        method='filter_is_in_shopping_list'
    )

    class Meta:
        model = Recipe
        fields = ('author', 'tags')

    def filter_is_favorited(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def filter_is_in_shopping_list(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(shopping_list__user=self.request.user)
        return queryset
