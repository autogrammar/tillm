"""dsl2tillm — control DSL bus for tillm."""

from dsl2tillm.bus import dispatch, execute_dsl, execute_dsl_line
from dsl2tillm.result import DslResult

__all__ = ["DslResult", "dispatch", "execute_dsl", "execute_dsl_line"]
