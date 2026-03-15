"""
Conftest for behavioral ML unit tests.

These modules are pure Python (no Django ORM/models).  We still need Django
minimally set up so that management-command tests can call call_command().
We stub out graphql_jwt before settings load to avoid its circular-import bug
(it reads django.conf.settings.SECRET_KEY during its own module init, which
happens while settings.py is still being evaluated).
"""
import sys
import types

# ---------------------------------------------------------------------------
# Stub graphql_jwt so settings.py doesn't hit its circular-import bug.
# The behavioral ML modules don't use graphql_jwt at all.
# ---------------------------------------------------------------------------
_gj = types.ModuleType("graphql_jwt")
_gj.middleware = types.ModuleType("graphql_jwt.middleware")
_gj.middleware.JSONWebTokenMiddleware = object
_gj.backends = types.ModuleType("graphql_jwt.backends")
_gj.backends.JSONWebTokenBackend = object
sys.modules.setdefault("graphql_jwt", _gj)
sys.modules.setdefault("graphql_jwt.middleware", _gj.middleware)
sys.modules.setdefault("graphql_jwt.backends", _gj.backends)

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "richesreach.settings_test")

import django
django.setup()

import pytest


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests():
    """Override parent conftest's db-requiring fixture: behavioral ML tests don't need the DB."""
    pass
