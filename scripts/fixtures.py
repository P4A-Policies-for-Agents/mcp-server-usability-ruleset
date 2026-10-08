"""Generate fixtures/ from GOOD plus one mutation per bad fixture.

Run from the repo root:  python3 -I scripts/fixtures.py
This deletes and rewrites fixtures/. Never edit fixtures/ by hand.

Bad fixture names are <rule-id> or <rule-id>.<variant>. scripts/check.sh expects
each one to produce exactly one finding, for <rule-id>, unless EXPECTED lists the
findings (written to the fixture's `expected` file).
"""
import copy
import json
import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent / "fixtures"

# Compliant with BOTH the MCP Server Safety and MCP Server Usability rulesets.
# Keep this dict identical in both repos.
GOOD = {
    "protocolVersion": "2025-06-18",
    "transport": {"kind": "streamableHttp", "path": "/mcp"},
    "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
    "securitySchemes": {"bearer": {"type": "http", "scheme": "bearer"}},
    "tools": [
        {
            "name": "get_weather",
            "description": "Gets the current weather for a city.",
            "annotations": {"readOnlyHint": True, "openWorldHint": True},
            "inputSchema": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "location": {"type": "string", "description": "City name", "maxLength": 100}
                },
                "required": ["location"],
            },
            "outputSchema": {
                "type": "object",
                "properties": {
                    "temperatureC": {"type": "number", "description": "Temperature in Celsius"}
                },
            },
        },
        {
            # destructiveHint: false (no readOnlyHint) is an explicit declaration.
            "name": "set_alert_threshold",
            "description": "Sets the temperature that triggers a weather alert for a city.",
            "annotations": {"destructiveHint": False, "openWorldHint": False},
            "inputSchema": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "location": {"type": "string", "description": "City name", "maxLength": 100},
                    "thresholdC": {"type": "number", "description": "Alert threshold in Celsius"},
                },
                "required": ["location", "thresholdC"],
            },
            "outputSchema": {
                "type": "object",
                "properties": {"ok": {"type": "boolean", "description": "Whether the threshold was saved"}},
            },
        },
    ],
    "resources": [
        {
            "uri": "weather://cities",
            "name": "cities",
            "description": "List of supported cities.",
            "mimeType": "application/json",
        }
    ],
    "prompts": [
        {
            "name": "weather_report",
            "description": "Writes a short weather report for a city.",
            "arguments": [
                {"name": "location", "description": "City name", "required": True},
                {"name": "tone", "description": "Writing tone, e.g. formal or casual", "required": False},
            ],
        },
        {
            # A prompt without arguments must not trip prompt-argument-described.
            "name": "daily_summary",
            "description": "Summarizes today's weather for all supported cities.",
        },
    ],
}


def tool(d, i=0):
    return d["tools"][i]


BAD = {
    "tool-description-required": lambda d: tool(d).pop("description"),
    # An empty string is no description; it is also shorter than 20 characters.
    "tool-description-required.empty-string": lambda d: tool(d).__setitem__("description", ""),
    "tool-name-format": lambda d: tool(d).__setitem__("name", "GetWeather"),
    "tool-name-format.too-long": lambda d: tool(d).__setitem__("name", "a" * 65),
    "tool-description-substantive": lambda d: tool(d).__setitem__("description", "Weather."),
    # 19 characters: one below the minimum.
    "tool-description-substantive.19-chars": lambda d: tool(d).__setitem__("description", "Gets city weather!!"),
    "resource-described.no-description": lambda d: d["resources"][0].pop("description"),
    "resource-described.no-mime-type": lambda d: d["resources"][0].pop("mimeType"),
    "resource-described.empty-description": lambda d: d["resources"][0].__setitem__("description", ""),
    "resource-described.empty-mime-type": lambda d: d["resources"][0].__setitem__("mimeType", ""),
    "prompt-described": lambda d: d["prompts"][1].pop("description"),
    "prompt-described.empty-string": lambda d: d["prompts"][1].__setitem__("description", ""),
    "prompt-argument-described": lambda d: d["prompts"][0]["arguments"][0].pop("description"),
    "prompt-argument-described.empty-string": lambda d: d["prompts"][0]["arguments"][0].__setitem__("description", ""),
    # Review Focus 4: only the second argument is undescribed.
    "prompt-argument-described.second-argument": lambda d: d["prompts"][0]["arguments"][1].pop("description"),
    "tool-output-schema-declared": lambda d: tool(d).pop("outputSchema"),
}

# Bad fixtures that legitimately produce more than one finding ("<rule-id>:<Severity>").
EXPECTED = {
    "tool-description-required.empty-string": [
        "tool-description-required:Violation",
        "tool-description-substantive:Warning",
    ],
}


def write(name, doc, expected=None):
    path = ROOT / name
    path.mkdir(parents=True)
    (path / "mcp-metadata.json").write_text(json.dumps(doc, indent=2) + "\n")
    asset = name.replace("/", "-").replace(".", "-")
    exchange = {
        "main": "mcp-metadata.json",
        "name": asset,
        "groupId": "p4a-fixtures",
        "assetId": asset,
        "version": "1.0.0",
        "classifier": "mcp-metadata",
        "descriptorVersion": "1.0.0",
    }
    (path / "exchange.json").write_text(json.dumps(exchange, indent=2) + "\n")
    if expected:
        (path / "expected").write_text("".join(f"{e}\n" for e in sorted(expected)))


def main():
    shutil.rmtree(ROOT, ignore_errors=True)
    write("good", GOOD)
    for name, mutate in BAD.items():
        doc = copy.deepcopy(GOOD)
        mutate(doc)
        write(f"bad/{name}", doc, EXPECTED.get(name))


if __name__ == "__main__":
    main()
