## Summary

- Issue: #
- Makes A→B faster or more honest because:

## North star

- [ ] This change helps session A hand work to session B (or reports idle honestly)
- [ ] Not a chat-room / cloud / fake-wake / unbounded-relay feature
- [ ] README interop table still true (or this PR updates the lying cell)

## How tested

- [ ] Layer 1 fake peers (`python -m unittest discover -s tests -v`)
- [ ] Layer 3 latency (included in the same command)
- [ ] Layer 4 live vendor matrix (optional; describe which pair)
- [ ] `sesstalk demo --json` still reproduces the README story

## Notes

Default CI has no LLM. If this change needs a corpus fixture, add it under `tests/corpus/`.
See [CONTRIBUTING.md](../CONTRIBUTING.md).
