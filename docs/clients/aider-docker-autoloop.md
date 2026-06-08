# Aider Docker Autoloop

This legacy workflow documents how to run a TestQL autoloop through an
`aider` container. It lives in tillm because Docker image setup, prompt-file
contracts, and shell-client execution are shell LLM control concerns.

Prefer the native tillm entrypoint when possible:

```bash
tillm drive --client aider \
  --prompt-file .aider/prompts/testql-autoloop.md \
  --extra-arg .windsurf/workflows/testql-autoloop.md \
  --extra-arg .testql/autoloop-state.json \
  --extra-arg .testql/schemas/llm-decision.schema.json \
  --execute
```

Legacy Docker flow:

1. Verify prerequisites.
   - `docker --version`
   - `docker compose version`
   - `test -n "$OPENROUTER_API_KEY"`

2. Validate compose file.
   - `docker compose -f .aider/docker-compose.yml config`

3. Build aider image.
   - `docker compose -f .aider/docker-compose.yml build`

4. Run one aider iteration for autoloop.
   - `docker compose -f .aider/docker-compose.yml run --rm aider /bin/sh -lc "aider --message-file .aider/prompts/testql-autoloop.md .windsurf/workflows/testql-autoloop.md .testql/autoloop-state.json .testql/schemas/llm-decision.schema.json"`

5. Verify output artifacts.
   - `test -f .testql/reports/llm-decision.json`
   - `python3 -m json.tool .testql/reports/llm-decision.json >/dev/null`

6. Continue or stop.
   - Continue loop if `decision` is not `stabilize_done` and max iterations not reached.
