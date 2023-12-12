from django.contrib.auth import get_user_model
from django.db import models
from django.core.validators import MinValueValidator, RegexValidator


User = get_user_model()


class Tag(models.Model):
    """Модель Тег."""

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Название тега',
    )
    color = models.CharField(
        max_length=7,
        validators=[
            RegexValidator(
                regex='^#[0-9A-Fa-f]{3}|[0-9A-Fa-f]{6}',
                message='Проверьте, что ввели корректное значение HEX-цвета!'
            )
        ],
        verbose_name='Цвет для тега',
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name='Идентификатор тега',
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель Ингредиент."""

    name = models.CharField(
        max_length=100,
        verbose_name='Название ингредиента',
    )
    unit = models.CharField(
        max_length=15,
        verbose_name='Единица измерения',
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'

    def __str__(self):
        return f'{self.name}, {self.unit}'


class Recipe(models.Model):
    """Модель Рецепт."""

    name = models.CharField(
        max_length=100,
        verbose_name='Название рецепта',
    )
    text = models.TextField(
        verbose_name='Текст рецепта',
    )
    ingredient = models.ManyToManyField(
        Ingredient,
        through='IngredientRecipes',
        related_name='recipes',
        verbose_name='Игредиенты для рецепта',
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(
                1, 'Время приготовления не должно быть меньше 1 минуты'
            )
        ],
        verbose_name='Время приготовления в минутах',
    )
    image = models.ImageField(
        upload_to='recipes/',
        verbose_name='Изображение рецепта',
    )
    tag = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Тег рецепта',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации',
    )

    class Meta:
        ordering = ["-pub_date"]
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return f'Рецепт {self.name} | Составил: {self.author}'


class IngredientRecipes(models.Model):
    """Модель для связи рецептов и ингредиентов."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredientrecipes',
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.PROTECT,
        related_name='ingredientrecipes',
        verbose_name='Ингредиент',
    )
    amount = models.PositiveSmallIntegerField(
        validators=(MinValueValidator(1, 'Не может быть менее 1'),),
        verbose_name='Количество',
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return (
            f'{self.recipe.name}:{self.ingredient.name}'
        )


class ShoppingList(models.Model):
    """Модель Список покупок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'


class Favorite(models.Model):
    """Модель Избранные рецепты."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Избранный рецепт',
    )

    class Meta:
        verbose_name = 'Список избранного'
        verbose_name_plural = 'Списки избранного'

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'
