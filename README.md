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
| `tool-output-schema-declared` | info | Agents can't chain results of unknown shape. | Add an `outputSchema`. |

Each rule's `documentation` and `examples` in [`ruleset.yaml`](ruleset.yaml) explain it in full. [`fixtures/`](fixtures) holds a compliant manifest (`good/`) and one failing manifest per rule (`bad/<rule>/`).

## Deploy it to your org

This ruleset is published through the P4A catalog (https://www.p4a.ai). Open its catalog entry and use **Publish to Exchange** (or the P4A MCP server's `deploy_ruleset`) to publish it into your own Anypoint organization, then add it to a governance profile that targets your MCP server assets.

## Limitations

- **Tool parameters are not checked.** Rules like "every parameter has a description" or "every parameter has a type" need access to individual input-schema properties. In governance-ruleset-tools 1.0.21 the MCP model exposes input `properties` only as an opaque value, and custom Rego rules are not supported for MCP assets.
- **Description quality is a length floor.** 20 characters can still be unhelpful; review descriptions as part of your API review.

## Development

```bash
python3 -I scripts/fixtures.py   # regenerate fixtures/ from scripts/fixtures.py
scripts/check.sh                 # lint + authoring + dialect + every fixture
```

Bump `version` in `exchange.json` for every rule change; Exchange versions are immutable. Design: [design spec](https://github.com/P4A-Policies-for-Agents/mcp-server-safety-ruleset/blob/main/docs/superpowers/specs/2026-10-08-mcp-server-rulesets-design.md) (in the Safety repo).

> Source Ref: [MuleSoft API Governance: custom rulesets](https://docs.mulesoft.com/api-governance/create-custom-rulesets), [MCP tools](https://modelcontextprotocol.io/specification/2025-06-18/server/tools), [MCP resources](https://modelcontextprotocol.io/specification/2025-06-18/server/resources), [MCP prompts](https://modelcontextprotocol.io/specification/2025-06-18/server/prompts). Snapshot 2026-10-08; validated with anypoint-cli-v4 1.6.25 / governance plugin 1.0.21.
