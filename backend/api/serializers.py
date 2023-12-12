from rest_framework import serializers
from drf_base64.fields import Base64ImageField
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from django.core.exceptions import ValidationError
from users.serializers import UserSerializer
from recipes.models import (
    Ingredient,
    IngredientRecipes,
    Recipe,
    ShoppingList,
    Tag,
    Favorite
)
from users.models import User, Subscription

from recipes.models import (
    Ingredient,
    Recipe,
    Tag,
    IngredientRecipes,
    ShoppingList,
    Favorite,
)
from rest_framework import status


class IngredientSerializer(serializers.ModelSerializer):
    """Ингредиенты."""

    class Meta:
        model = Ingredient
        fields = "__all__"


class TagSerializer(serializers.ModelSerializer):
    """Теги."""

    class Meta:
        model = Tag
        read_only_fields = ("__all__",)
        fields = "__all__"


class IngredientRecipesSerializer(serializers.ModelSerializer):
    """Ингредиенты в рецепте."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    name = serializers.CharField(
        source='ingredient.name',
        read_only=True
    )
    unit = serializers.CharField(
        source='ingredient.unit',
        read_only=True
    )
    class Meta:
        model = IngredientRecipes
        fields = (
            'id',
            'name',
            'unit',
            'amount',
        )


class RecipeSerializer(serializers.ModelSerializer):
    """Список рецептов."""

    tag = TagSerializer(
        many=True,
        read_only=True
    )
    author = UserSerializer(read_only=True)
    ingredient = IngredientRecipesSerializer(
        many=True,
        read_only=True,
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tag',
            'author',
            'ingredient',
            'name',
            'image',
            'text',
            'cooking_time',
        )
    
    def get_is_favorited(self, obj):
        """Проверка наличия рецепта в избранном."""

        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return Favorite.objects.filter(favorite__user=user,
                                     id=obj.id).exists()
    
    def get_is_in_shopping_cart(self, obj):
        """Проверка наличия рецепта в списке покупок"""
        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return Recipe.objects.filter(shoppinglist__user=user,
                                     id=obj.id).exists()


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Создание, изменение и удаление рецепта."""
    tag = TagSerializer(
        many=True,
        read_only=True
    )
    author = UserSerializer(read_only=True)
    ingredient = IngredientRecipesSerializer(
        many=True,
        read_only=True,
        source='ingredientrecipes'
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tag',
            'author',
            'ingredient',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def validate(self, data):
        ingredient_list = []
        for ingredient in data.get('ingredientrecipes'):#не тот список
            if ingredient.get('amount') <= 0:
                raise serializers.ValidationError(
                    'Количество не может быть меньше 1'
                )
            ingredient_list.append(ingredient.get('id'))

        if len(set(ingredient_list)) != len(ingredient_list):
            raise serializers.ValidationError(
                'Вы пытаетесь добавить в рецепт два одинаковых ингредиента'
            )
        return data

    def tag_and_ingredient_set(self, recipe, tag, ingredients):
        recipe.tag.set(tag)
        IngredientRecipes.objects.bulk_create(
            [IngredientRecipes(
                recipe=recipe,
                ingredient=Ingredient.objects.get(pk=ingredient['id']),
                amount=ingredient['amount']
            ) for ingredient in ingredients]
        )

    def create(self, validated_data):
        """Создание рецепта."""

        tag = validated_data.pop('tag')
        ingredient = validated_data.pop('ingredient')
        recipe = Recipe.objects.create(author=self.context['request'].user,
                                       **validated_data)
        self.tag_and_ingredient_set(recipe, tag, ingredient)
        return recipe

    def update(self, instance, validated_data):
        """Обновление рецепта."""
        
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get('cooking_time', instance.cooking_time)
        tag = validated_data.pop('tag')
        ingredient = validated_data.pop('ingredient')
        IngredientRecipes.objects.filter(
            recipe=instance,
            ingredient__in=instance.ingredient.all()).delete()
        self.tag_and_ingredient_set(instance, tag, ingredient)
        instance.save()
        return instance


class RecipeSmallSerializer(serializers.ModelSerializer):
    """Краткоя информациея о рецепте."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(serializers.ModelSerializer):
    """Подписоки пользователя."""

    is_subscribed = serializers.SerializerMethodField()
    recipes = RecipeSerializer(many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        read_only_fields = ('email', 'username')
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )
    
    def validate(self, data):
        author = self.instance
        user = self.context.get('request').user
        if Subscription.objects.filter(author=author, user=user).exists():
            raise ValidationError(
                detail='Вы уже подписаны на этого пользователя!',
                code=status.HTTP_400_BAD_REQUEST
            )
        if user == author:
            raise ValidationError(
                detail='Вы не можете подписаться на самого себя!',
                code=status.HTTP_400_BAD_REQUEST
            )
        return data

    def get_is_subscribed(self, obj):
        """Проверка подписки на автора."""

        return Subscription.objects.filter(user=obj.user, author=obj.author).exists()
    
    def get_recipes_count(self, obj):
        """Количество рецептов."""

        return Recipe.objects.filter(author=obj.author).count()

    def get_recipes(self, obj):
        """Список всех рецептов автора."""

        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        queryset = Recipe.objects.filter(author=obj.author)
        if limit:
            queryset = queryset[:int(limit)]
        serializer = SubscriptionSerializer(queryset, many=True)
        return serializer.data


class ShoppingListSerializer(serializers.ModelSerializer):
    """Список покупок."""

    id = serializers.IntegerField()
    name = serializers.CharField()
    image = Base64ImageField(max_length=None, use_url=False)
    cooking_time = serializers.IntegerField()
    
    class Meta:
        model = ShoppingList
        fields = ('id', 'name', 'image', 'cooking_time')
        validators = UniqueTogetherValidator(
            queryset=ShoppingList.objects.all(),
            fields=('user', 'recipe'),
            message='Рецепт уже есть в списке покупок'
        )
    
    #def to_representation(self, instance):
    #    request = self.context.get('request')
    #    return RecipeSmallSerializer(
    #        instance.recipe,
    #        context={'request': request}
    #    ).data


class RecipeFavoriteSerializer(serializers.ModelSerializer):
    """Список избранных рецептов."""

    id = serializers.IntegerField()
    name = serializers.CharField()
    image = Base64ImageField(
        max_length=None,
        use_url=False,
    )
    cooking_time = serializers.IntegerField()
    
    class Meta:
        model = Favorite
        fields = ('id', 'name', 'image', 'cooking_time')
        validators = UniqueTogetherValidator(
            queryset=Favorite.objects.all(),
            fields=('user', 'recipe')
        )

