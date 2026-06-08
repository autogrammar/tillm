"""Small fixture for examples/aider/refactor.sh."""


def say_hello(name: str) -> str:
    return "hello " + name


def say_hello_formal(name: str) -> str:
    return "hello " + name + ", welcome"
