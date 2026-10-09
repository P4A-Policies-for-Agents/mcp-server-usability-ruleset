# Changelog

## 1.0.0 (2026-10-08)

- Initial release: `tool-description-required` (violation); `tool-name-format`, `tool-description-substantive`, `resource-described`, `prompt-described`, `prompt-argument-described` (warning); `tool-output-schema-declared` (info). Empty-string descriptions and mimeTypes count as missing.
- Fix false findings on governance plugin 1.1.x, which hosted Anypoint governance runs: element paths now use `mcp.*` (plugin 1.1.x renamed them from `core.*`). Needs plugin 1.1.4 or later.
- Add `server-declares-capabilities` (warning): the manifest must list at least one tool, resource or prompt. Catches MCP assets published without an `mcp-metadata.json`, for which Exchange stores a transport-only stub.
