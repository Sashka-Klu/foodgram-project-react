from django.contrib import admin
from recipes.models import (
    Ingredient,
    IngredientRecipes,
    Recipe,
    Favorite, 
    ShoppingList,
    Tag
)


class TagAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'color', 'slug')
    list_editable = ('name', 'color', 'slug')
    empty_value_display = '-пусто-'


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'unit')
    list_editable = ('name', 'unit')
    list_filter = ('name',)
    search_fields = ('name', )


class IngredientsInline(admin.TabularInline):
   model = IngredientRecipes


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'author', 'count_favorited', 'cooking_time', 'image', 'text',)
    list_filter = ('name', 'author', 'tag')
    list_editable = ('name', 'cooking_time', 'text', 'image', 'author')
    empty_value_display = '-пусто-'
    inlines = (IngredientsInline,)

    def count_favorited(self, obj):
        return obj.obj.favorites.count()


class ShoppingListAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe')
    list_editable = ('user', 'recipe')


class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe')
    list_editable = ('user', 'recipe')


admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(ShoppingList, ShoppingListAdmin)
admin.site.register(Favorite, FavoriteAdmin)