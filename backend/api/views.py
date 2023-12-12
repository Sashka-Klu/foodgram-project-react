from users.models import Subscription, User
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from users.serializers import UserCreateSerializer, UserSerializer, SetPasswordSerializer
from rest_framework.response import Response
from djoser.views import UserViewSet
from rest_framework import filters, status, viewsets, mixins
from .permissions import IsAdminOrReadOnly, IsAuthorReadOnly
from .serializers import (
    IngredientSerializer,
    TagSerializer,
    IngredientRecipesSerializer,
    RecipeSerializer,
    RecipeCreateSerializer,
    RecipeSmallSerializer,
    SubscriptionSerializer,
    ShoppingListSerializer,
    RecipeFavoriteSerializer,
)
from .pagination import CustomPagination
from recipes.models import (
    Tag,
    Ingredient,
    Recipe,
    IngredientRecipes,
    ShoppingList,
    Favorite,
)

class UserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return UserSerializer
        return UserCreateSerializer

    @action(detail=False, methods=['get'],
            pagination_class=None,
            permission_classes=(IsAuthenticated,))
    def me(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data,
                        status=status.HTTP_200_OK)


    @action(detail=False,
            methods=['post'],
            permission_classes=(IsAuthenticated,))
    def set_password(self, request):
        serializer = SetPasswordSerializer(request.user, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        return Response({'detail': 'Пароль успешно изменен!'},
                        status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'],
            permission_classes=(IsAuthenticated,),
            pagination_class=CustomPagination)
    def subscriptions(self, request):
        queryset = User.objects.filter(subscribing__user=request.user)
        page = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(page, many=True,
                                             context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, **kwargs):
        author = get_object_or_404(User, id=kwargs['pk'])

        if request.method == 'POST':
            serializer = SubscriptionSerializer(
                author, data=request.data, context={"request": request})
            serializer.is_valid(raise_exception=True)
            Subscription.objects.create(user=request.user, author=author)
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            get_object_or_404(Subscription, user=request.user,
                              author=author).delete()
            return Response({'detail': 'Успешная отписка'},
                            status=status.HTTP_204_NO_CONTENT)



class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Получение информации о тегах."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny, )
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Получение информации об ингредиентах."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny, )
    #filter_backends = (DjangoFilterBackend, )
    #filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Для работы с рецептами"""

    queryset = Recipe.objects.all()
    pagination_class = CustomPagination
    permission_classes = (IsAuthorReadOnly, )
    #filter_backends = (DjangoFilterBackend, )
    #filterset_class = RecipeFilter
    http_method_names = ['get', 'post', 'patch', 'create', 'delete']

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeSerializer
        return RecipeCreateSerializer

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeSerializer
        return RecipeCreateSerializer
 
    @action(detail=True,methods=['post', 'delete'],
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, **kwargs):
        recipe = get_object_or_404(Recipe, id=kwargs['pk'])

        if request.method == 'POST':
            serializer = RecipeSerializer(recipe, data=request.data,
                                          context={"request": request})
            serializer.is_valid(raise_exception=True)
            if not Favorite.objects.filter(user=request.user,
                                           recipe=recipe).exists():
                Favorite.objects.create(user=request.user, recipe=recipe)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response({'errors': 'Рецепт уже в избранном.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            get_object_or_404(Favorite, user=request.user,
                              recipe=recipe).delete()
            return Response({'detail': 'Рецепт успешно удален из избранного.'},
                            status=status.HTTP_204_NO_CONTENT)
        
    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(IsAuthenticated,),
            pagination_class=None)
    def shopping_cart(self, request, **kwargs):
        recipe = get_object_or_404(Recipe, id=kwargs['pk'])

        if request.method == 'POST':
            serializer = RecipeSerializer(recipe, data=request.data,
                                          context={"request": request})
            serializer.is_valid(raise_exception=True)
            if not ShoppingList.objects.filter(user=request.user,
                                                recipe=recipe).exists():
                ShoppingList.objects.create(user=request.user, recipe=recipe)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response({'errors': 'Рецепт уже в списке покупок.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            get_object_or_404(ShoppingList, user=request.user,
                              recipe=recipe).delete()
            return Response(
                {'detail': 'Рецепт успешно удален из списка покупок.'},
                status=status.HTTP_204_NO_CONTENT
            )
        
    @action(detail=False, methods=['get'],
            permission_classes=(IsAuthenticated,))
    def download_shopping_list(self, request):
        shopping_list_result = {}
        ingredients = IngredientRecipes.objects.filter(
            recipes__shoppinglist__user=request.user
        ).values_list('ingredients__name',
                      'ingredients__unit',
                      'amount')
        
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
