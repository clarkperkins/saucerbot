# -*- coding: utf-8 -*-

from abc import abstractmethod
from collections.abc import Callable
from typing import Type

from django.contrib.auth import models as auth_models
from django.core.exceptions import SuspiciousOperation
from django.db import models
from django.db.models.manager import EmptyManager
from django.http import HttpRequest


class BaseUser(models.Model):
    class Meta:
        abstract = True

    # User is always active
    is_active = True

    # Never staff or superuser
    is_staff = False
    is_superuser = False

    objects = models.Manager()
    _groups = EmptyManager(auth_models.Group)  # type: ignore
    _user_permissions = EmptyManager(auth_models.Permission)  # type: ignore

    @property
    @abstractmethod
    def username(self):
        raise NotImplementedError()

    def get_username(self):
        return self.username

    @property
    def groups(self):
        return self.__class__._groups  # pylint: disable=protected-access

    @property
    def user_permissions(self):
        return self.__class__._user_permissions  # pylint: disable=protected-access

    @property
    def is_anonymous(self):
        return False

    @property
    def is_authenticated(self):
        return True


class InvalidUser(SuspiciousOperation):
    pass


def get_user_builder(
    model_class: Type[models.Model], session_key: str
) -> Callable[[HttpRequest], BaseUser | None]:
    def get_user(request: HttpRequest) -> BaseUser | None:
        try:
            user_pk = model_class._meta.pk.to_python(  # type: ignore[union-attr]
                request.session[session_key]
            )
            return model_class.objects.get(pk=user_pk)  # type: ignore
        except KeyError:
            pass
        except model_class.DoesNotExist:  # type: ignore
            pass
        return None

    return get_user
