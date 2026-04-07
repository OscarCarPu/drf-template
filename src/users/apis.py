from api.mixins import ApiAuthMixin
from api.pagination import LimitOffsetPagination
from api.utils import get_paginated_response
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import User
from users.selectors import user_get, user_list
from users.services import user_create, user_deactivate, user_update


class UserListApi(ApiAuthMixin, APIView):
    class FilterSerializer(serializers.Serializer):
        email = serializers.CharField(required=False)
        first_name = serializers.CharField(required=False)
        last_name = serializers.CharField(required=False)
        is_active = serializers.BooleanField(required=False, allow_null=True, default=None)

    class OutputSerializer(serializers.ModelSerializer):
        class Meta:
            model = User
            fields = ("id", "email", "first_name", "last_name", "is_active", "created_at")

    @extend_schema(
        parameters=[FilterSerializer],
        responses=OutputSerializer(many=True),
    )
    def get(self, request):
        filter_serializer = self.FilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)

        users = user_list(filters=filter_serializer.validated_data)

        return get_paginated_response(
            pagination_class=LimitOffsetPagination,
            serializer_class=self.OutputSerializer,
            queryset=users,
            request=request,
            view=self,
        )


class UserDetailApi(ApiAuthMixin, APIView):
    class OutputSerializer(serializers.ModelSerializer):
        class Meta:
            model = User
            fields = ("id", "email", "first_name", "last_name", "is_active", "created_at", "updated_at")

    @extend_schema(responses=OutputSerializer)
    def get(self, request, user_id):
        user = user_get(user_id=user_id)

        if user is None:
            return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.OutputSerializer(user)
        return Response(serializer.data)


class UserCreateApi(ApiAuthMixin, APIView):
    class InputSerializer(serializers.Serializer):
        email = serializers.EmailField()
        password = serializers.CharField(min_length=8)
        first_name = serializers.CharField(max_length=150, required=False, default="")
        last_name = serializers.CharField(max_length=150, required=False, default="")

    class OutputSerializer(serializers.ModelSerializer):
        class Meta:
            model = User
            fields = ("id", "email", "first_name", "last_name", "is_active", "created_at")

    @extend_schema(request=InputSerializer, responses={201: OutputSerializer})
    def post(self, request):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = user_create(**serializer.validated_data)

        output = self.OutputSerializer(user)
        return Response(output.data, status=status.HTTP_201_CREATED)


class UserUpdateApi(ApiAuthMixin, APIView):
    class InputSerializer(serializers.Serializer):
        first_name = serializers.CharField(max_length=150, required=False)
        last_name = serializers.CharField(max_length=150, required=False)

    class OutputSerializer(serializers.ModelSerializer):
        class Meta:
            model = User
            fields = ("id", "email", "first_name", "last_name", "is_active", "updated_at")

    @extend_schema(request=InputSerializer, responses=OutputSerializer)
    def patch(self, request, user_id):
        user = user_get(user_id=user_id)

        if user is None:
            return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.InputSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        user = user_update(user=user, data=serializer.validated_data)

        output = self.OutputSerializer(user)
        return Response(output.data)


class UserDeactivateApi(ApiAuthMixin, APIView):
    @extend_schema(request=None, responses={200: None})
    def post(self, request, user_id):
        user = user_get(user_id=user_id)

        if user is None:
            return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        user_deactivate(user=user)

        return Response({"message": "User deactivated."})
