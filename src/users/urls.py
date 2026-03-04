from django.urls import path

from users.apis import UserCreateApi, UserDeactivateApi, UserDetailApi, UserListApi, UserUpdateApi

urlpatterns = [
    path("", UserListApi.as_view(), name="user-list"),
    path("create/", UserCreateApi.as_view(), name="user-create"),
    path("<int:user_id>/", UserDetailApi.as_view(), name="user-detail"),
    path("<int:user_id>/update/", UserUpdateApi.as_view(), name="user-update"),
    path("<int:user_id>/deactivate/", UserDeactivateApi.as_view(), name="user-deactivate"),
]
