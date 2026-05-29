# AGENTS.md

## Purpose

This repository is the source repository for an AstrBot plugin. All future development, maintenance, and AI-assisted edits in this repository must follow AstrBot's official plugin development rules first, then the repository rules in this file.

If this file conflicts with AstrBot official documentation, the official documentation wins.

Primary references:

- https://docs.astrbot.app/dev/star/plugin-new.html
- https://docs.astrbot.app/dev/star/guides/simple.html
- https://docs.astrbot.app/dev/star/guides/plugin-config.html
- https://docs.astrbot.app/dev/star/guides/storage.html

## Scope

This file applies to:

- Creating a new AstrBot plugin from an empty repository
- Modifying an existing plugin in this repository
- Local integration and debugging against a real AstrBot runtime
- Preparing the plugin for packaging, installation, and release

This repository is not the AstrBot core repository. Do not place AstrBot framework code, runtime data, or unrelated services here.

## Required Plugin Layout

The plugin directory name should use the AstrBot convention:

- `astrbot_plugin_<plugin_name>`

At plugin root, keep these files aligned with official expectations:

- `main.py`: plugin entrypoint
- `metadata.yaml`: plugin metadata
- `requirements.txt`: Python dependencies

Optional but standard files:

- `_conf_schema.json`: plugin config schema shown in AstrBot management UI
- `logo.png`: plugin icon
- `skills/`: plugin skill definitions if the plugin exposes skills
- `README.md`: usage, configuration, and development notes

Do not invent alternative entrypoint names or move required files into nested directories unless AstrBot official documentation explicitly supports it.

## Source Of Truth

The repository root should mirror the actual plugin root layout as closely as possible.

Preferred model:

- This repository stores the plugin source
- The AstrBot runtime loads the plugin from `AstrBot/data/plugins/astrbot_plugin_<plugin_name>/`
- Local development should sync this repository into that runtime plugin directory by copy, symlink, or junction

The source of truth is this repository, not a manually edited runtime copy.

## Implementation Rules

All code changes must follow these rules:

- Prefer asynchronous implementations for network and I/O work.
- Do not introduce blocking network calls in plugin handlers.
- Do not use `requests` for new network work when an async client is appropriate.
- Keep dependencies minimal and record every runtime dependency in `requirements.txt`.
- Keep plugin startup lightweight. Expensive initialization should be deferred where possible.
- Preserve backward compatibility for existing config fields unless the user explicitly approves a breaking change.
- Keep command names, event handlers, and public behavior stable unless the task requires a deliberate change.
- Add brief comments only where logic is genuinely non-obvious.

## Configuration Rules

If the plugin needs user-configurable settings:

- Define them in `_conf_schema.json`
- Keep defaults conservative and safe
- Keep schema keys stable once released
- Reflect any config changes in `README.md`
- Ensure code handles missing or older config values gracefully

Do not hardcode secrets, tokens, or user-specific local paths into source files.

## Data Storage Rules

Runtime data must not be written into the plugin source directory.

Use AstrBot's plugin data area:

- `data/plugin_data/<plugin_name>/`

Store caches, generated files, state snapshots, and other mutable runtime artifacts there. Source-controlled files in this repository should remain deterministic and reviewable.

## Development Workflow

When building from zero:

1. Create the plugin root using the `astrbot_plugin_<plugin_name>` naming convention.
2. Add `main.py`, `metadata.yaml`, and `requirements.txt` first.
3. Add `_conf_schema.json` if the plugin needs configurable behavior.
4. Implement the smallest runnable version before expanding features.
5. Verify the plugin can be discovered and loaded by AstrBot before adding complexity.

When modifying an existing plugin:

1. Read `metadata.yaml`, `main.py`, `requirements.txt`, and `_conf_schema.json` before editing.
2. Identify whether the change affects public behavior, configuration, storage, or dependency surface.
3. Preserve compatibility unless the requested task explicitly authorizes a break.
4. Update docs and schema together with code when behavior changes.
5. Re-run local integration checks after each meaningful change.

## Local Integration Workflow

Use this repository as the editable source and validate changes inside a real AstrBot runtime.

Recommended local layout:

- Source repo: this repository
- Runtime plugin path: `AstrBot/data/plugins/astrbot_plugin_<plugin_name>/`
- Runtime data path: `AstrBot/data/plugin_data/<plugin_name>/`

Recommended integration steps:

1. Ensure the runtime plugin directory name exactly matches the plugin naming convention.
2. Sync repository contents into `AstrBot/data/plugins/astrbot_plugin_<plugin_name>/`.
3. Install dependencies required by `requirements.txt` in the AstrBot runtime environment.
4. Start or restart AstrBot.
5. Confirm the plugin is discovered and loaded without import or metadata errors.
6. Validate the plugin's core command, event hook, or primary user flow.
7. Confirm mutable files are written only under `data/plugin_data/<plugin_name>/`.

If hot reload is unavailable or unreliable, prefer a clean restart for verification.

## Change Discipline

Before making changes, always check:

- Does the plugin entrypoint remain valid?
- Does `metadata.yaml` still describe the actual plugin behavior and version?
- Does `_conf_schema.json` still match the code?
- Are new dependencies declared?
- Is runtime state still stored outside the source directory?
- Will this change break existing users, commands, or config?

Avoid unrelated refactors during feature work unless they are required to safely implement the task.

## Quality Bar

Before considering work complete, verify at minimum:

- Imports resolve successfully
- Required plugin files exist in the expected locations
- `requirements.txt` matches actual imports
- Config schema and code agree
- No runtime data is written into the plugin source tree
- Basic AstrBot loading succeeds in a local runtime
- Core plugin behavior is manually smoke-tested

If formatting or lint tooling is present, run it before finishing. If the repository later adds tests, run the relevant tests for any touched behavior.

## Documentation Rules

Keep documentation aligned with behavior:

- Update `README.md` when installation, commands, config, or permissions change
- Update examples when request or response formats change
- Document any required environment variables, API credentials, or external services
- Record any manual integration steps needed for AstrBot runtime testing

## Release And Versioning

For release-oriented changes:

- Keep `metadata.yaml` version information in sync with the actual change scope
- Treat config key renames, command renames, and storage migrations as release-sensitive changes
- Document any migration steps if old runtime data or config needs adaptation

## Rules For Future AI Agents

Any agent editing this repository must:

- Read this `AGENTS.md` before making changes
- Follow AstrBot official plugin documentation first
- Preserve required file layout
- Prefer minimal, reversible changes
- Verify local runtime integration, not just static edits
- Avoid writing runtime artifacts into the repository

When uncertain, choose the approach that is most compatible with AstrBot's documented plugin structure and least disruptive to existing users.
