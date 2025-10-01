"""Streamlit compatibility shim for backend contexts.

This module exposes a ``st`` object with a handful of no-op behaviours so that
legacy modules originally written for Streamlit can be imported without the
actual dependency. When Streamlit is available the real module is used.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Iterable

try:  # pragma: no cover - actual dependency available
    import streamlit as st  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - provide shim instead
    def _noop(*_: Any, **__: Any) -> None:
        return None

    class _ContextManager:
        """Basic context manager that swallows all operations."""

        def __init__(self, return_value: Any | None = None) -> None:
            self._return_value = return_value if return_value is not None else self

        def __enter__(self) -> Any:
            return self._return_value

        def __exit__(self, *args: Any) -> bool:
            return False

        def __call__(self, *args: Any, **kwargs: Any) -> "_ContextManager":
            return self

        def __getattr__(self, _: str) -> Callable[..., None]:
            return _noop

    class _SessionState(dict):
        """Minimal dictionary-backed session state implementation."""

        def clear(self) -> None:  # type: ignore[override]
            super().clear()

    class _StreamlitShim:
        """Subset of Streamlit's API used in legacy helpers."""

        def __init__(self) -> None:
            self.session_state: _SessionState = _SessionState()
            self.query_params: Dict[str, Iterable[str]] = {}
            self.sidebar = _ContextManager()

        # Simple UI helpers -------------------------------------------------
        def error(self, *args: Any, **kwargs: Any) -> None:
            _noop(*args, **kwargs)

        warning = error
        info = error
        success = error
        write = error
        subheader = error
        header = error
        title = error
        markdown = error
        text = error
        image = error

        def spinner(self, *args: Any, **kwargs: Any) -> _ContextManager:
            return _ContextManager()

        def expander(self, *args: Any, **kwargs: Any) -> _ContextManager:
            return _ContextManager()

        def chat_message(self, *args: Any, **kwargs: Any) -> _ContextManager:
            return _ContextManager()

        def button(self, *args: Any, **kwargs: Any) -> bool:
            return False

        # Session/query helpers --------------------------------------------
        def experimental_get_query_params(self) -> Dict[str, Iterable[str]]:
            return dict(self.query_params)

        def experimental_set_query_params(self, **kwargs: Any) -> None:
            self.query_params.update({k: (v if isinstance(v, list) else [v]) for k, v in kwargs.items()})

        @property
        def query_params_map(self) -> Dict[str, Iterable[str]]:
            return self.query_params

        def rerun(self) -> None:
            return None

        def __getattr__(self, _: str) -> Callable[..., None]:
            return _noop

    st = _StreamlitShim()

__all__ = ["st"]
