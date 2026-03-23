from rest_framework import serializers

from apps.users.models import User

MIN_PASSWORD_LENGTH = 8


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        min_length=MIN_PASSWORD_LENGTH,
        write_only=True,
    )
    password_confirm = serializers.CharField(
        write_only=True,
    )
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    patronymic = serializers.CharField(
        max_length=100,
        required=False,
        default="",
    )

    def validate(self, attrs: dict) -> dict:
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )
        return attrs


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "patronymic",
            "full_name",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "email",
            "created_at",
            "updated_at",
        )


class UpdateProfileSerializer(serializers.Serializer):
    first_name = serializers.CharField(
        max_length=100,
        required=False,
    )
    last_name = serializers.CharField(
        max_length=100,
        required=False,
    )
    patronymic = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
    )


class RefreshTokenSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()
