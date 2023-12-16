from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from recipes.models import Ingredient, IngredientInRecipe, Recipe, Tag, ShoppingCard, Favorite
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.fields import IntegerField, SerializerMethodField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework import status
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from users.models import Subscription, CustomUser


User = get_user_model()


class CustomUserCreateSerializer(UserCreateSerializer):
    """Создание пользователя."""

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'password',
            'username',
            'first_name',
            'last_name',
        )


class CustomUserSerializer(UserSerializer):
    """Получение списка пользователей."""

    is_subscribed = SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        """Проверка подписки пользователя."""

        user = self.context.get('request').user
        return (
            user.is_authenticated and obj.subscribing.filter(user=user).exists()
        )


class SubscriptionSerializer(CustomUserSerializer):
    """Подписки пользователя."""

    recipes = SerializerMethodField()
    recipes_count = SerializerMethodField()

    class Meta:
        model = CustomUser
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
                detail='Посмотрите внимательно, вы уже на него подписаны!',
                code=status.HTTP_400_BAD_REQUEST
            )
        if user == author:
            raise ValidationError(
                detail='Жаль, но вы не можете подписаться на самого себя!',
                code=status.HTTP_400_BAD_REQUEST
            )
        return data

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
        serializer = RecipeShortSerializer(queryset, many=True)
        return serializer.data


class IngredientSerializer(ModelSerializer):
    """Ингредиенты."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(ModelSerializer):
    """Теги."""

    class Meta:
        model = Tag
        fields = '__all__'


class RecipeReadSerializer(ModelSerializer):
    """Список рецептов."""

    tags = TagSerializer(
        many=True,
        read_only=True
    )
    author = CustomUserSerializer(read_only=True)
    ingredients = SerializerMethodField()
    image = Base64ImageField()
    is_favorited = SerializerMethodField(read_only=True)
    is_in_shopping_cart = SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_ingredients(self, obj):
        """Ингредиенты."""

        recipe = obj
        ingredients = recipe.ingredients.values(
            'id',
            'name',
            'measurement_unit',
            amount=F('ingredient_list__amount')
        )
        return ingredients

    def get_is_favorited(self, obj):
        """Проверка наличия рецепта в избранном."""

        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return user.favorites.filter(recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        """Проверка наличия рецепта в списке покупок."""

        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return user.shopping_cart.filter(recipe=obj).exists()


class IngredientInRecipeWriteSerializer(ModelSerializer):
    """Создание нгредиентов в рецепте."""

    id = IntegerField(write_only=True)
    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')


class RecipeWriteSerializer(ModelSerializer):
    """Создание, изменение и удаление рецепта."""

    tags = PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientInRecipeWriteSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def validate_ingredient(self, value):
        """Проверка наличия ингредиентов."""

        ingredients = value
        if not ingredients:
            raise ValidationError({
                'ingredients': 'Блюдо не может состоять из воздуха!'
            })

        for i in ingredients:
            try:
                ingredient = get_object_or_404(Ingredient, pk=i['id'])
            except:
                raise ValidationError(
                    detail='Пустой список ингредиентов',
                    code=status.HTTP_400_BAD_REQUEST
                )
            ingredient = ingredients.pop()
            if ingredient in ingredients:
                raise ValidationError(
                    detail='Вы пытаетесь добавить два одинаковых ингредиента!',
                    code=status.HTTP_400_BAD_REQUEST
                )

        if int(i['amount']) <= 0:
            raise ValidationError({
                'amount': 'Количество ингредиента должно быть больше 0!'
            })
        return value

    def validate_tags(self, value):
        """Проверка наличия тегов."""
        tags = value
        if not tags:
            raise ValidationError({'tags': 'Выберете хотя бы один тег!'})
        tags_list = []
        for tag in tags:
            if tag in tags_list:
                raise ValidationError({'tags': 'Теги должны быть уникальными!'})
            tags_list.append(tag)
        return value

    def validate_image(self, value):
        """Проверка наличия тегов."""
        image = value
        if not image:
            raise ValidationError({'image': 'Нехватает картинки!'})
        return value

    def create_ingredients_amounts(self, ingredients, recipe):
        """Создание колическво ингредиентов."""

        IngredientInRecipe.objects.bulk_create(
            [IngredientInRecipe(
                ingredient=Ingredient.objects.get(id=ingredient['id']),
                recipe=recipe,
                amount=ingredient['amount']
            ) for ingredient in ingredients]
        )

    def create(self, validated_data):
        """Создание рецепта."""

        tags = self.validate_tags(validated_data.pop('tags'))
        ingredients = self.validate_ingredient(validated_data.pop('ingredients'))
        image = self.validate_image(validated_data.pop('image'))
        recipe = Recipe.objects.create(image=image,**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients_amounts(recipe=recipe, ingredients=ingredients)
        return recipe

    def update(self, instance, validated_data):
        """Обновление рецепта."""

        instance.image = validated_data.get("image", instance.image)
        instance.name = validated_data.get("name", instance.name)
        instance.text = validated_data.get("text", instance.text)
        instance.cooking_time = validated_data.get(
            "cooking_time", instance.cooking_time
        )
        instance.tags.clear()
        tags_data = self.initial_data.get("tags")
        instance.tags.set(tags_data)
        IngredientInRecipe.objects.filter(recipes=instance).all().delete()
        self.create_ingredients(validated_data.get("ingredients"), instance)
        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(instance,
                                    context=self.context).data


class RecipeShortSerializer(ModelSerializer):
    """Краткоя информациея о рецепте."""

    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )
