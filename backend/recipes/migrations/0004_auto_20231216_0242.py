# Generated by Django 3.2.3 on 2023-12-15 23:42

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('recipes', '0003_auto_20231215_1905'),
    ]

    operations = [
        migrations.RenameField(
            model_name='ingredient',
            old_name='unit',
            new_name='measurement_unit',
        ),
        migrations.AlterField(
            model_name='shoppinglist',
            name='recipe',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shopping_cart', to='recipes.recipe', verbose_name='Рецепт'),
        ),
        migrations.AlterField(
            model_name='shoppinglist',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shopping_cart', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь'),
        ),
    ]