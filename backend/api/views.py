from django.db.models import Sum
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from recipes.models import (Ingredient, IngredientInRecipe, Recipe,
                            ShoppingList, Tag, Favorite)
from users.models import Subscription

from rest_framework import status
from djoser.views import UserViewSet
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from .filters import RecipeFilter
from .pagination import CustomPagination
from .permissions import IsAdminOrReadOnly, IsAuthorOrReadOnly
from .serializers import (
    IngredientSerializer,
    TagSerializer,
    RecipeReadSerializer,
    IngredientInRecipeWriteSerializer,
    RecipeWriteSerializer,
    RecipeShortSerializer,
    CustomUserSerializer,
    SubscriptionSerializer,
)

User = get_user_model()


class CustomUserViewSet(UserViewSet):
    """ViewSet пользователя."""

    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomPagination

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def subscription(self, request, **kwargs):
        """Создание/удаление подписки на автора."""

        author_id = self.kwargs.get('id')
        author = get_object_or_404(User, id=author_id)

        if request.method == 'POST':
            serializer = SubscriptionSerializer(
                author, data=request.data, context={"request": request})
            serializer.is_valid(raise_exception=True)
            Subscription.objects.create(user=request.user, author=author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            get_object_or_404(
                Subscription, user=request.user, author=author).delete()
            return Response({'detail': 'Успешная отписка'},
                            status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        """Просмотр подписок пользователя."""

        queryset = User.objects.filter(subscribing__user=request.user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            pages, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)


class TagViewSet(ReadOnlyModelViewSet):
    """Получение информации о тегах."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAdminOrReadOnly,)


class IngredientViewSet(ReadOnlyModelViewSet):
    """Получение информации об ингредиентах."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (SearchFilter,)
    search_fields = ('name',)


class RecipeViewSet(ModelViewSet):
    """Для работы с рецептами"""

    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly | IsAdminOrReadOnly,)
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend, )
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, id):
        if request.method == 'POST':
            return self.add_to(Favorite, request.user, id)
        else:
            return self.delete_from(Favorite, request.user, id)
  
    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def shopping_list(self, request, id):
        if request.method == 'POST':
            return self.add_to(ShoppingList, request.user, id)
        else:
            return self.delete_from(ShoppingList, request.user, id)

    def add_to(self, model, user, id):
        if model.objects.filter(user=user, recipe__id=id).exists():
            return Response({'errors': 'Рецепт уже добавлен!'}, status=status.HTTP_400_BAD_REQUEST)
        recipe = get_object_or_404(Recipe, id=id)
        model.objects.create(user=user, recipe=recipe)
        serializer = RecipeShortSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_from(self, model, user, id):
        obj = model.objects.filter(user=user, recipe__id=id)
        if obj.exists():
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'errors': 'Рецепт уже удален!'}, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_list(self, request):
        if not request.user.shopping_list.exists():
            return Response(status=HTTP_400_BAD_REQUEST)

        shopping_list_result = {}
        ingredients = IngredientInRecipe.objects.filter(
            recipe__shopping_list__user=request.user
        ).values_list(
            'ingredients__name',
            'ingredients__unit',
            'amount'
        )

        for ingredient in ingredients:
            name = ingredient[0]
            if name not in shopping_list_result:
                shopping_list_result[name] = {
                    'unit': ingredient[1],
                    'amount': ingredient[2],
                }
            else:
                shopping_list_result[name]['amount'] += ingredient[2]

        shopping_list_itog = (
            f'{name} - {value("amount")} ' f'{value("unit")}\n'
            for name, value in shopping_list_result.items()
        )

        filename = f'{user.username}_shoppinglist.txt'
        response = HttpResponse(shopping_list_itog, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
