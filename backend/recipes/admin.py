from django.contrib import admin
from django.contrib.admin import display
from recipes.models import (
    Ingredient,
    IngredientInRecipe,
    Recipe,
    Favorite,
    ShoppingCard,
    Tag
)


class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'color', 'slug')
    list_editable = ('name', 'color', 'slug')


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    list_editable = ('name', 'measurement_unit')
    list_filter = ('name',)
    search_fields = ('name', )


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author', 'count_favorited', 'cooking_time')
    list_editable = ('name', 'author')
    list_filter = ('name', 'author', 'tags')
    readonly_fields = ('count_favorited',)

    @display(description='Количество в избранных')
    def count_favorited(self, obj):
        return obj.favorites.count()


class ShoppingListAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    list_editable = ('user', 'recipe')


class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    list_editable = ('user', 'recipe')


class IngredientInRecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount',)
    list_editable = ('recipe', 'ingredient', 'amount')


admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(ShoppingCard, ShoppingListAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(IngredientInRecipe, IngredientInRecipeAdmin)
