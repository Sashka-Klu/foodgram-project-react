from rest_framework import serializers
from djoser.serializers import UserCreateSerializer, UserSerializer
from users.models import User, Subscription
from django.contrib.auth.password_validation import validate_password
from rest_framework.serializers import SerializerMethodField
from users.models import User, Subscription


class UserCreateSerializer(UserCreateSerializer):
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
        #extra_kwargs = {
        #    "email": {"required": True},
        #    "username": {"required": True},
        #    "password": {"required": True},
        #    "first_name": {"required": True},
        #    "last_name": {"required": True},
        #}


class UserSerializer(UserSerializer):
    """Получение списка пользователей."""

    is_subscribed= serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_follow'
        )

    def get_is_is_subscribed(self, obj):
        """Проверка подписки пользователя."""

        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return Subscription.objects.filter(user=user, author=obj.id).exists()


class SetPasswordSerializer(serializers.Serializer):
    """Изменение пароля пользователя."""
    
    current_password = serializers.CharField()
    new_password = serializers.CharField()

    def validate(self, obj):
        try:
            validate_password(obj['new_password'])
        except django_exceptions.ValidationError as e:
            raise serializers.ValidationError(
                {'new_password': list(e.messages)}
            )
        return super().validate(obj)

    def update(self, instance, validated_data):
        if not instance.check_password(validated_data['current_password']):
            raise serializers.ValidationError(
                {'current_password': 'Непверный пароль.'}
            )
        if (validated_data['current_password']
           == validated_data['new_password']):
            raise serializers.ValidationError(
                {'new_password': 'Новый пароль должен отличаться от текущего.'}
            )
        instance.set_password(validated_data['new_password'])
        instance.save()
        return validated_data
