# MCP Server Usability

A MuleSoft API Governance ruleset (AMF Validation Profile 1.0) for **MCP server** assets. It checks that an MCP server's tools, resources and prompts are named and described well enough for an agent to pick the right one and call it correctly.

**Pairs with:**
- [MCP Server Safety](https://github.com/P4A-Policies-for-Agents/mcp-server-safety-ruleset) covers declared authentication, tool side effects and closed tool inputs.
- MuleSoft's **Agent Network Best Practices** ruleset covers MCP transport and protocol version, which this ruleset deliberately leaves out.

## Rules

| Rule | Severity | Why | Fix |
|---|---|---|---|
| `tool-description-required` | violation | Models choose tools from their descriptions. | Add a `description`. |
| `tool-name-format` | warning | Clients and LLM APIs reject or mangle unusual names. | Use lower snake_case, ≤ 64 chars. |
| `tool-description-substantive` | warning | One-word descriptions can't be told apart. | Write at least 20 characters. |
| `resource-described` | warning | Agents can't find or parse undescribed resources. | Add `description` and `mimeType`. |
| `prompt-described` | warning | Users can't tell what a prompt does. | Add a `description`. |
| `prompt-argument-described` | warning | Users and agents guess argument values. | Describe every argument. |
| `server-declares-capabilities` | warning | An empty manifest (what Exchange stores when there is no `mcp-metadata.json`) tells agents nothing. | List at least one tool, resource or prompt. |
| `tool-output-schema-declared` | info | Agents can't chain results of unknown shape. | Add an `outputSchema`. |

An empty string counts as missing for every `description` and `mimeType` check. An empty tool description is reported by both `tool-description-required` and `tool-description-substantive`.

Each rule's `documentation` and `examples` in [`ruleset.yaml`](ruleset.yaml) explain it in full. [`fixtures/`](fixtures) holds a compliant manifest (`good/`) and one failing manifest per rule (`bad/<rule>/`).

## Requirements

Governance plugin 1.1.4 or later (`anypoint-cli-v4 plugins --core`). Plugin 1.1.x names MCP element fields `mcp.*` (for example `mcp.description`); 1.0.x named them `core.*`, so this version does not work on 1.0.x. `scripts/check.sh` checks the plugin version.

## Deploy it to your org

This ruleset is published through the P4A catalog (https://www.p4a.ai). Open its catalog entry and use **Publish to Exchange** (or the P4A MCP server's `deploy_ruleset`) to publish it into your own Anypoint organization, then add it to a governance profile that targets your MCP server assets.

## Limitations

- **Tool parameters are not checked.** Rules like "every parameter has a description" or "every parameter has a type" need access to individual input-schema properties. In governance plugin 1.0.21 the MCP model exposes input `properties` only as an opaque value, and custom Rego rules are not supported for MCP assets.
- **Description quality is a length floor.** 20 characters can still be unhelpful; review descriptions as part of your API review.

## Known authoring error

`governance:ruleset:validate-authoring` reports one error: `server-declares-capabilities` uses `targetClass: core.encodes`, which the linter calls invalid. The linter's MCP metadata is out of date. It lists an `mcp.Server` class, but plugin 1.1.x never types the manifest root as `mcp:Server`, so a rule on `mcp.Server` would never run. The root is typed `core:encodes`, and the rule fires correctly on it (see `fixtures/bad/server-declares-capabilities.*`).

## Test on Exchange assets

To try the ruleset on real assets, publish the fixtures to a test business group, then attach
the ruleset to them, for example with a draft governance profile. Copy `.env.example` to `.env`
and fill in a connected app and business group ID; `.env` is gitignored.

```bash
scripts/publish-examples.sh --dry-run   # list the assets
scripts/publish-examples.sh             # <prefix>-ok plus one <prefix>-<rule-id> per rule
scripts/publish-examples.sh --all       # also every bad variant and the scope fixtures
scripts/cleanup-examples.sh             # soft-delete them all after testing (--hard, --yes)
```

`<prefix>-ok` should give 0 findings, and each `<prefix>-<rule-id>` exactly the finding named in
its description. Publishing skips versions that already exist; to republish changed fixtures,
clean up first or set `EXAMPLES_VERSION`.

## Development

```bash
python3 -I scripts/fixtures.py   # regenerate fixtures/ from scripts/fixtures.py
scripts/check.sh                 # lint + authoring + dialect + every fixture
```

Bump `version` in `exchange.json` for every rule change; Exchange versions are immutable. Design: [design spec](https://github.com/P4A-Policies-for-Agents/mcp-server-safety-ruleset/blob/main/docs/superpowers/specs/2026-10-08-mcp-server-rulesets-design.md) (in the Safety repo).

> Source Ref: [MuleSoft API Governance: custom rulesets](https://docs.mulesoft.com/api-governance/create-custom-rulesets), [MCP tools](https://modelcontextprotocol.io/specification/2025-06-18/server/tools), [MCP resources](https://modelcontextprotocol.io/specification/2025-06-18/server/resources), [MCP prompts](https://modelcontextprotocol.io/specification/2025-06-18/server/prompts). Snapshot 2026-10-09; validated with anypoint-cli-v4 1.6.25 / governance plugin 1.1.4.
