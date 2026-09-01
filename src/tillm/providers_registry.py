"""Built-in provider registry and lookup helpers."""

from __future__ import annotations

from tillm.providers_types import ProviderSpec, UnknownProviderError

_PROVIDERS: tuple[ProviderSpec, ...] = (
    ProviderSpec(
        id="anthropic",
        label="Anthropic (Claude)",
        kind="subscription",
        token_env="ANTHROPIC_API_KEY",
        docs_url="https://docs.anthropic.com",
        token_url="https://console.anthropic.com/settings/keys",
        anthropic_base_url=None,
        models=("sonnet", "opus", "haiku"),
        notes="claude-code native; subscription login or ANTHROPIC_API_KEY.",
    ),
    ProviderSpec(
        id="openai",
        label="OpenAI (GPT)",
        kind="api",
        token_env="OPENAI_API_KEY",
        docs_url="https://platform.openai.com/docs",
        token_url="https://platform.openai.com/api-keys",
        openai_base_url=None,
        models=("gpt-5.1", "gpt-5.1-codex", "gpt-5-mini"),
        notes="codex/aider native endpoint.",
    ),
    ProviderSpec(
        id="z.ai",
        label="Z.ai (GLM)",
        kind="api",
        token_env="ZAI_API_KEY",
        docs_url="https://docs.z.ai",
        token_url="https://z.ai/manage-apikey/apikey-list",
        anthropic_base_url="https://api.z.ai/api/anthropic",
        openai_base_url="https://api.z.ai/api/coding/paas/v4",
        probe_models=("glm-4.7", "glm-4.6", "glm-4.5"),
        default_model="glm-4.7",
        aliases=("zai", "z-ai", "glm", "zhipu"),
        models=("glm-4.7", "glm-4.6", "glm-4.5", "glm-4.5-air"),
        notes="GLM coding plan; Anthropic-compatible endpoint drives claude-code.",
    ),
    ProviderSpec(
        id="deepseek",
        label="DeepSeek",
        kind="api",
        token_env="DEEPSEEK_API_KEY",
        docs_url="https://api-docs.deepseek.com",
        token_url="https://platform.deepseek.com/api_keys",
        anthropic_base_url="https://api.deepseek.com/anthropic",
        openai_base_url="https://api.deepseek.com",
        probe_models=("deepseek-chat",),
        default_model="deepseek-chat",
        models=("deepseek-chat", "deepseek-reasoner"),
        notes="V3/R1; Anthropic-compatible endpoint drives claude-code.",
    ),
    ProviderSpec(
        id="google",
        label="Google (Gemini)",
        kind="api",
        token_env="GEMINI_API_KEY",
        docs_url="https://ai.google.dev/gemini-api/docs",
        token_url="https://aistudio.google.com/app/apikey",
        openai_base_url="https://generativelanguage.googleapis.com/v1beta/openai",
        aliases=("gemini",),
        models=("gemini-3-pro-preview", "gemini-2.5-pro", "gemini-2.5-flash"),
        notes="gemini-cli native; OpenAI-compatible endpoint for aider/codex.",
    ),
    ProviderSpec(
        id="openrouter",
        label="OpenRouter",
        kind="api",
        token_env="OPENROUTER_API_KEY",
        docs_url="https://openrouter.ai/docs",
        token_url="https://openrouter.ai/settings/keys",
        openai_base_url="https://openrouter.ai/api/v1",
        aliases=("or",),
        notes="Multi-model gateway; OpenAI-compatible (aider/codex lane).",
    ),
    ProviderSpec(
        id="moonshot",
        label="Moonshot (Kimi)",
        kind="api",
        token_env="MOONSHOT_API_KEY",
        docs_url="https://platform.moonshot.ai/docs",
        token_url="https://platform.moonshot.ai/console/api-keys",
        anthropic_base_url="https://api.moonshot.ai/anthropic",
        openai_base_url="https://api.moonshot.ai/v1",
        probe_models=("kimi-k2.5", "kimi-k2-turbo-preview", "kimi-k2"),
        default_model="kimi-k2.5",
        aliases=("kimi",),
        models=("kimi-k2.5", "kimi-k2-turbo-preview", "kimi-k2"),
        notes="Kimi K2; Anthropic-compatible endpoint drives claude-code.",
    ),
    ProviderSpec(
        id="xai",
        label="xAI (Grok)",
        kind="api",
        token_env="XAI_API_KEY",
        docs_url="https://docs.x.ai",
        token_url="https://console.x.ai",
        openai_base_url="https://api.x.ai/v1",
        aliases=("grok",),
        models=("grok-4.1", "grok-4", "grok-code-fast-1"),
        notes="Grok; OpenAI-compatible (aider/codex lane).",
    ),
    ProviderSpec(
        id="groq",
        label="Groq",
        kind="api",
        token_env="GROQ_API_KEY",
        docs_url="https://console.groq.com/docs",
        token_url="https://console.groq.com/keys",
        openai_base_url="https://api.groq.com/openai/v1",
        models=("llama-3.3-70b-versatile",),
        notes="Fast open-model inference; OpenAI-compatible.",
    ),
    ProviderSpec(
        id="mistral",
        label="Mistral",
        kind="api",
        token_env="MISTRAL_API_KEY",
        docs_url="https://docs.mistral.ai",
        token_url="https://console.mistral.ai/api-keys",
        openai_base_url="https://api.mistral.ai/v1",
        models=("mistral-large-latest", "codestral-latest", "devstral-medium-latest"),
        notes="OpenAI-compatible (aider/codex lane).",
    ),
    ProviderSpec(
        id="minimax",
        label="MiniMax (M2)",
        kind="api",
        token_env="MINIMAX_API_KEY",
        docs_url="https://platform.minimax.io/docs",
        token_url="https://platform.minimax.io/user-center/basic-information/interface-key",
        anthropic_base_url="https://api.minimax.io/anthropic",
        openai_base_url="https://api.minimax.io/v1",
        probe_models=("MiniMax-M2",),
        default_model="MiniMax-M2",
        models=("MiniMax-M2",),
        notes="M2; Anthropic-compatible endpoint drives claude-code.",
    ),
    ProviderSpec(
        id="qwen",
        label="Qwen (DashScope)",
        kind="api",
        token_env="DASHSCOPE_API_KEY",
        docs_url="https://www.alibabacloud.com/help/en/model-studio",
        token_url="https://bailian.console.aliyun.com/?apiKey=1",
        openai_base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        aliases=("dashscope",),
        models=("qwen3-coder-plus", "qwen3-max", "qwen-max"),
        notes="Qwen3 family; OpenAI-compatible; qwen-code client lane.",
    ),
    ProviderSpec(
        id="ollama",
        label="Ollama (local)",
        kind="local",
        token_env="OLLAMA_API_KEY",
        docs_url="https://docs.ollama.com",
        token_url="",
        openai_base_url="http://localhost:11434/v1",
        notes="Local models, no token needed; requires `ollama serve`.",
    ),
)


def normalize_provider_id(raw: str) -> str:
    token = (raw or "").strip().lower()
    for spec in _PROVIDERS:
        if token == spec.id or token in spec.aliases:
            return spec.id
    return token


def get_provider_spec(provider_id: str) -> ProviderSpec:
    normalized = normalize_provider_id(provider_id)
    for spec in _PROVIDERS:
        if spec.id == normalized:
            return spec
    known = ", ".join(s.id for s in _PROVIDERS)
    raise UnknownProviderError(f"unknown provider {provider_id!r} (known: {known})")


def iter_provider_specs() -> tuple[ProviderSpec, ...]:
    return _PROVIDERS
