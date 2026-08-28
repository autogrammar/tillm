# mcp2tillm

MCP stdio server exposing `dsl2tillm` tools.

```bash
mcp2tillm serve
```

Tools: `tillm_run_command`, `tillm_run_dsl`, `tillm_to_dsl`, `tillm_health`, `tillm_clients`.

Commands remain dry-run unless `EXECUTE true` is requested. Live execution over
MCP additionally requires `TILLM_MCP_ALLOW_EXECUTE=1`. Project paths are
confined to the current directory by default; set `TILLM_MCP_PROJECT_ROOT` to
select another allowed root.
