# Documentation

Project-bound knowledge (docs-as-code). The *build/operate* layer lives here, versioned with the code and readable by any agent in-context.

- [`adr/`](adr/) — Architecture Decision Records
- [`troubleshooting/`](troubleshooting/) — known issues & fixes
- [`lessons.md`](lessons.md) — accumulated gotchas & post-mortems
- [`audit-pre-implementation.md`](audit-pre-implementation.md) — pre-implementation security audit

The *decide/position* layer (roadmap, prestudy, strategy) and session memory live in the maintainer's cross-project knowledge store, not committed here. Per-feature specs, when a feature is in flight, live in a top-level `specs/` folder (none open at the moment); task tracking lives on the bitácora GitHub Project.
