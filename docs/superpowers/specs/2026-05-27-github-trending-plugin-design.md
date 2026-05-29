# GitHub Trending Plugin Design

## Overview

This repository will host an AstrBot plugin that fetches GitHub Trending data and exposes it through both a chat command and an AI-callable tool.

The first supported source is `github`, but the plugin must be structured so additional trending sources can be added later without changing the public interaction model.

Primary user-facing behavior:

- Chat command: `/trending github`
- AI-callable tool: a unified trending lookup tool that accepts `source=github`

The plugin fetches `https://github.com/trending`, extracts the current page items, and returns the following fields for each project:

- project name
- today stars
- project description
- programming language
- Chinese summary of the description

If a project has no description, the Chinese summary is left empty.

## Goals

- Build a minimal but production-structured AstrBot plugin from an empty repository
- Support both manual command invocation and AI tool invocation
- Use one shared service layer for command and tool paths
- Support two summary modes:
  - AstrBot default model
  - custom OpenAI-compatible model configured in plugin settings
- Return all entries currently shown on the GitHub Trending page
- Keep the design extensible for future trending sources

## Non-Goals

- Supporting multiple trending sources in this first implementation
- Implementing caching, rate limiting, or persistence in the first version
- Providing per-request custom model parameters in chat commands
- Building a generic scraping framework beyond what this plugin needs

## Repository Layout

The repository should mirror the plugin root structure expected by AstrBot.

Required root files:

- `main.py`
- `metadata.yaml`
- `requirements.txt`
- `_conf_schema.json`
- `README.md`

Implementation directories:

- `providers/`
- `services/`
- `summarizers/`
- `tools/`
- `models/`

Recommended layout:

```text
.
|-- main.py
|-- metadata.yaml
|-- requirements.txt
|-- _conf_schema.json
|-- README.md
|-- providers/
|   |-- __init__.py
|   `-- github_trending.py
|-- services/
|   |-- __init__.py
|   `-- trending_service.py
|-- summarizers/
|   |-- __init__.py
|   |-- astrbot_default.py
|   `-- custom_openai.py
|-- tools/
|   |-- __init__.py
|   `-- trending_tool.py
`-- models/
    |-- __init__.py
    `-- trending.py
```

## Public Behavior

### Chat Command

The plugin exposes:

- `/trending github`

Behavior:

- Fetch all entries shown on GitHub Trending
- Format the result into readable chat text
- Include project name, today stars, description, language, and Chinese summary
- Return a clear error message if fetching or parsing fails

### AI Tool

The plugin also exposes a unified AI tool through AstrBot's LLM tool registration flow.

Behavior:

- Accept at least one parameter: `source`
- Support `source=github` in the first version
- Return structured data suitable for AI consumption
- Reuse the same service logic as the chat command

## Internal Architecture

### `main.py`

Responsibilities:

- register the AstrBot plugin
- read plugin configuration
- construct shared service dependencies
- register `/trending` command
- register the LLM tool in `__init__()`

`main.py` should stay thin. It should not contain scraping logic or summary implementation details.

### `providers/github_trending.py`

Responsibilities:

- request `https://github.com/trending`
- parse the HTML page
- extract raw project fields
- normalize missing fields safely

This provider should only return structured raw data. It should not format chat output or call any LLM directly.

Expected extracted fields per item:

- `name`
- `url`
- `stars_today`
- `description`
- `language`

### `services/trending_service.py`

Responsibilities:

- route by `source`
- call the correct provider
- call the active summarizer
- assemble final response objects
- expose a single API used by command and AI tool paths

This is the core orchestration layer.

### `summarizers/astrbot_default.py`

Responsibilities:

- obtain the current AstrBot chat provider context
- use AstrBot's official LLM invocation path
- summarize each English description into concise Chinese

This mode is the default behavior.

### `summarizers/custom_openai.py`

Responsibilities:

- read plugin-configured `base_url`, `api_key`, `model`, and timeout
- call an OpenAI-compatible chat/completions endpoint
- produce concise Chinese summaries

If custom mode is selected but required config is missing, this module must return a clear configuration error instead of silently falling back.

### `tools/trending_tool.py`

Responsibilities:

- define the AI-callable tool entry
- validate tool arguments
- call the shared trending service
- return structured result objects

### `models/trending.py`

Responsibilities:

- define shared data structures for internal use
- keep shape consistent across provider, service, command, and tool layers

Suggested models:

- `TrendingItem`
- `TrendingResult`

## Configuration Design

Plugin configuration is stored in `_conf_schema.json` and injected into the plugin by AstrBot.

Required config keys:

- `summary_mode`
  - allowed values:
    - `astrbot_default`
    - `custom_openai_compatible`
- `custom_base_url`
- `custom_api_key`
- `custom_model`
- `custom_timeout_seconds`
- `request_timeout_seconds`
- `user_agent`

Behavior rules:

- If `summary_mode=astrbot_default`, use AstrBot's current configured model path
- If `summary_mode=custom_openai_compatible`, use plugin-managed OpenAI-compatible requests
- If custom mode is selected and required config is incomplete, fail clearly
- Do not place secrets in source files

## Data Flow

End-to-end flow:

1. User invokes `/trending github` or AI invokes the trending tool with `source=github`
2. Entry layer calls `TrendingService`
3. `TrendingService` routes to `GitHubTrendingProvider`
4. Provider fetches and parses the GitHub Trending page
5. Service selects summarizer based on plugin config
6. Summarizer generates Chinese summaries for descriptions that are not empty
7. Service assembles final result
8. Command path formats readable text output
9. Tool path returns structured data

## Error Handling

The plugin must degrade cleanly.

### Fetch failure

If the GitHub Trending page cannot be fetched:

- command path returns a clear user-readable error
- tool path returns a structured error payload

### Parse failure

If page fetch succeeds but no items can be parsed:

- return a clear message that page structure may have changed
- do not crash the plugin

### Summary failure

If Chinese summary generation fails:

- do not discard the trending items
- keep returning the main ranking data
- set `summary_zh` to empty or a failure-safe value chosen in implementation

Implementation should prefer empty output over noisy placeholder text where possible.

### Invalid custom model config

If custom model mode is selected but `base_url`, `api_key`, or `model` is missing:

- return a configuration error
- do not silently fall back to AstrBot default mode

## Output Design

### Internal result shape

Top-level result:

- `source`
- `fetched_at`
- `items`

Each item:

- `name`
- `url`
- `stars_today`
- `description`
- `language`
- `summary_zh`

### Command output

Command output should be compact and readable in chat.

Suggested per-item rendering:

- project name
- today stars
- language
- description
- Chinese summary
- project URL

Avoid excessive debug text in normal responses.

## Networking And Dependency Rules

The plugin should prefer async networking and avoid blocking handlers.

Implementation guidance:

- use an async HTTP client for GitHub page fetches
- use the same style for custom OpenAI-compatible requests
- record runtime dependencies in `requirements.txt`
- keep dependencies minimal

## Extensibility Strategy

The public interaction model must stay stable while new sources are added.

Future sources should only require:

- a new provider module
- service routing extension
- optional source-specific formatting adjustments

The command should remain `/trending <source>`.

The AI tool should remain a unified trending lookup tool with `source` as the selector.

## Testing And Verification Strategy

### Static verification

- imports resolve
- required plugin files exist
- config schema matches code expectations
- `requirements.txt` covers actual runtime imports

### Runtime verification

- `/trending github` returns all page items
- AI tool works with `source=github`
- AstrBot default summary path works
- custom OpenAI-compatible summary path works

### Regression checks

- missing language field
- missing description field
- summary generation failure
- GitHub request timeout
- GitHub page structure change

## Documentation Requirements

`README.md` must include:

- installation steps
- command usage
- config explanation
- summary mode explanation
- local AstrBot integration instructions

It should also explain that runtime mutable data must stay outside the plugin source directory under AstrBot's plugin data path.

## Local Integration Requirements

The repository is the source of truth. Runtime testing should happen through an AstrBot plugin installation path such as:

- `AstrBot/data/plugins/astrbot_plugin_<plugin_name>/`

Runtime mutable data must be stored under:

- `AstrBot/data/plugin_data/<plugin_name>/`

Recommended local validation:

1. sync this repository into the AstrBot plugin directory
2. install dependencies in the AstrBot runtime environment
3. restart AstrBot
4. verify plugin loads successfully
5. test `/trending github`
6. test AI tool invocation

## Implementation Notes

- Code should include useful comments around parsing logic, summary mode switching, and AstrBot integration points
- Comments should explain why the code works a certain way, not restate obvious syntax
- The initial implementation should optimize for correctness and maintainability over feature breadth

## Open Decisions Resolved

The following decisions are fixed for the first implementation:

- architecture: layered approach with command, tool, service, provider, summarizer separation
- command format: `/trending github`
- default result count: all entries on the page
- missing description summary: leave empty
- custom model parameters: plugin config only, not command arguments
- custom config failure: explicit error, no silent fallback
