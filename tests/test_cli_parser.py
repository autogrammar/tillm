"""Regression tests for the CLI argument-parser helpers.

Lock in current behaviour of ``_build_parser`` and
``_normalize_extra_arg_tokens`` so the parser layer can be moved into a cohesive
submodule without changing the accepted invocations.
"""

from __future__ import annotations

import pytest

from tillm.cli import _EXTRA_ARG_OPTION, _build_parser, _normalize_extra_arg_tokens


# ---------------------------------------------------------------------------
# _normalize_extra_arg_tokens
# ---------------------------------------------------------------------------


def test_normalize_combines_space_form_option_followed_by_dash_flag() -> None:
    # `--extra-arg --dangerously-skip-permissions` -> `--extra-arg=--dangerously-skip-permissions`
    argv = ["--extra-arg", "--dangerously-skip-permissions", "--client", "aider"]
    assert _normalize_extra_arg_tokens(argv) == [
        "--extra-arg=--dangerously-skip-permissions",
        "--client",
        "aider",
    ]


def test_normalize_leaves_option_followed_by_plain_value_as_is() -> None:
    # A non-dash value after --extra-arg is a normal positional pairing -> untouched.
    argv = ["--extra-arg", "plainvalue", "--client", "aider"]
    assert _normalize_extra_arg_tokens(argv) == argv


def test_normalize_leaves_equals_form_as_is() -> None:
    argv = ["--extra-arg=--flag", "--client", "aider"]
    assert _normalize_extra_arg_tokens(argv) == argv


def test_normalize_leaves_trailing_option_without_value_as_is() -> None:
    # --extra-arg is the final token -> nothing to pair with -> untouched.
    assert _normalize_extra_arg_tokens(["--client", "aider", "--extra-arg"]) == [
        "--client",
        "aider",
        "--extra-arg",
    ]


def test_normalize_empty_argv_is_empty() -> None:
    assert _normalize_extra_arg_tokens([]) == []


def test_extra_arg_option_constant_is_stable() -> None:
    assert _EXTRA_ARG_OPTION == "--extra-arg"


# ---------------------------------------------------------------------------
# _build_parser
# ---------------------------------------------------------------------------


def _parse(*argv: str):
    return _build_parser().parse_args(list(argv))


def test_parser_requires_a_subcommand() -> None:
    with pytest.raises(SystemExit):
        _build_parser().parse_args([])


def test_parser_clients_format_defaults_to_text() -> None:
    args = _parse("clients")
    assert args.action == "clients"
    assert args.format == "text"


def test_parser_clients_accepts_json_format() -> None:
    assert _parse("clients", "--format", "json").format == "json"


def test_parser_drive_requires_exactly_one_target() -> None:
    with pytest.raises(SystemExit):
        _parse("drive")  # no target in the required mutually-exclusive group


def test_parser_drive_targets_are_mutually_exclusive() -> None:
    with pytest.raises(SystemExit):
        _parse("drive", "--client", "aider", "--clients", "codex")


def test_parser_drive_single_client_target() -> None:
    args = _parse("drive", "--client", "aider")
    assert args.action == "drive"
    assert args.client == "aider"
    assert args.clients is None
    assert args.all is False
    # drive --format defaults to json.
    assert args.format == "json"


def test_parser_drive_all_flag() -> None:
    args = _parse("drive", "--all")
    assert args.all is True


def test_parser_drive_format_choices_include_summary() -> None:
    assert _parse("drive", "--all", "--format", "summary").format == "summary"
    with pytest.raises(SystemExit):
        _parse("drive", "--all", "--format", "xml")


def test_parser_drive_extra_arg_appends() -> None:
    args = _parse(
        "drive",
        "--client",
        "aider",
        "--extra-arg",
        "alpha",
        "--extra-arg",
        "beta",
    )
    assert args.extra_arg == ["alpha", "beta"]


def test_normalize_then_parse_accepts_space_form_dash_flags() -> None:
    # The real main() runs _normalize_extra_arg_tokens before _build_parser;
    # this confirms the two cooperate so `--extra-arg --flag` reaches the parser
    # as `--extra-arg=--flag` and is appended as a value.
    raw = ["drive", "--client", "aider", "--extra-arg", "--no-show-model-warnings"]
    args = _build_parser().parse_args(_normalize_extra_arg_tokens(raw))
    assert args.extra_arg == ["--no-show-model-warnings"]


def test_parser_drive_available_only_default_true_and_negatable() -> None:
    assert _parse("drive", "--all").available_only is True
    assert _parse("drive", "--all", "--no-available-only").available_only is False


def test_parser_nlp_text_nargs_plus() -> None:
    args = _parse("nlp", "fix", "the", "tests")
    assert args.action == "nlp"
    assert args.text == ["fix", "the", "tests"]


def test_parser_nlp_requires_at_least_one_text_token() -> None:
    with pytest.raises(SystemExit):
        _parse("nlp")


def test_parser_provider_requires_subaction() -> None:
    with pytest.raises(SystemExit):
        _parse("provider")  # provider_action is required
    args = _parse("provider", "set", "z.ai", "--token", "abc")
    assert args.provider_action == "set"
    assert args.provider_id == "z.ai"


def test_parser_provider_supports_test_models_doctor() -> None:
    for sub in ("test", "models", "doctor"):
        args = _parse("provider", sub, "z.ai")
        assert args.provider_action == sub
