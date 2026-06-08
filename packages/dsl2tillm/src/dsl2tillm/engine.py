"""Backward-compatible shim — re-export dispatch from bus."""

from dsl2tillm.bus import dispatch, execute_dsl, execute_dsl_line

__all__ = ["dispatch", "execute_dsl", "execute_dsl_line"]
