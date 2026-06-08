"""Throwaway sample for aider refactor smoke test."""


def multiply_by_repeat(x, y):
    if x < 0:
        return 0
    return x * y


def format_greeting(name):
    return f"Hello, {name}!" if name else "Hello, world!"
