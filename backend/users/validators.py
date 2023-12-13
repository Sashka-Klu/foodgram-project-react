import re

from django.core.exceptions import ValidationError


def validate_username(value):
    """Проверка логина."""

    if value.lower() == 'me':
        raise ValidationError(
            'Недопустимое имя пользователя!'
        )
    if not bool(re.match(r'^[\w.@+-]+$', value)):
        raise ValidationError(
            'Введены недопустимые символы!.'
        )
    return value
