# Changelog

All notable changes to this repository are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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
