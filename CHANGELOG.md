# Changelog

All notable changes to this repository are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.3.0] - 2026-11-17

### Added
- Growth and upload tooling, all driven by data files: `videoengine.hooks` (batch thumbnails, contact sheets),
  `videoengine.ab_thumbs` (A/B variants and comparison sheet), `videoengine.growth` (title checks with a rollback
  log, CTR two-proportion z-test, pinned comments), `videoengine.batch_shorts` (Short scripts from one JSON spec),
  `videoengine.upload_prep` (upload folder with per-Short metadata) and `videoengine.lessons` (Markdown lesson pages).
- `videoengine.config` and `channel.example.json`: playlist links, video ids and the episode map live in a
  git-ignored `channel.json`, never in code.
- Sample inputs: `examples/lessons/arch_evolution.py`, five Short scripts in `examples/shorts/`, and example CSV/JSON
  files for every tool.
- `docs/growth-tooling.md` and `tests/test_growth_tools.py`.

### Changed
- The Short-to-episode link is a data-driven lookup with a fallback, instead of a fixed map that only knew the
  first fifteen Shorts.

## [1.2.0] - 2026-11-15

### Added
- `docs/how-it-works.md`: a step-by-step walkthrough of both engines, with key concepts.

### Changed
- Docs: training-grade README and walkthrough. Added what problem this solves, what you will learn, key concepts,
  a mermaid diagram, the Shorts `--check` command, output locations, and an accurate repo layout.

### Fixed
- The Shorts engine did not run the banned-word check, although the README said every build does. `shorts.validate`
  now applies it, with a test.

## [1.1.0] - 2026-11-15

### Added
- `CHANGELOG.md`, `CONTRIBUTING.md` and a documentation index in `docs/README.md`.

## [1.0.0] - 2026-11-14

### Added
- First public release: the maintained code, documentation, tests and CI.
