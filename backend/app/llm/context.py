from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator

_llm_user_id: ContextVar[str | None] = ContextVar("llm_user_id", default=None)
_llm_route: ContextVar[str | None] = ContextVar("llm_route", default=None)


def get_llm_user_id() -> str | None:
    return _llm_user_id.get()


def get_llm_route() -> str | None:
    return _llm_route.get()


@contextmanager
def set_llm_context(user_id: str | None = None, route: str | None = None) -> Iterator[None]:
    user_token = None
    route_token = None
    if user_id:
        user_token = _llm_user_id.set(user_id)
    if route:
        route_token = _llm_route.set(route)
    try:
        yield
    finally:
        if route_token is not None:
            _llm_route.reset(route_token)
        if user_token is not None:
            _llm_user_id.reset(user_token)
