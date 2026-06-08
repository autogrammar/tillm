"""Throwaway sample for aider refactor smoke test."""


def calc(x, y):
    r = 0
    for i in range(x):
        r = r + y
    return r


def greet(name):
    if name == "":
        return "Hello, world!"
    else:
        return "Hello, " + name + "!"
