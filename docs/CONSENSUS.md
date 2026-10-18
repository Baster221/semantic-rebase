# Review the meaning of four exact snapshots

The author submits replacements. Deterministic code constructs:

- BASE: the author's immutable original revision.
- INTENDED: BASE with exact author replacements.
- CURRENT: complete current document head.
- MERGED: CURRENT with those same replacements.

Every validator independently derives the complete judgment from all four inputs. It does not ask whether the leader's labels merely have valid formatting.

| Check | Substantive task |
|---|---|
| patch_intent | BASE→INTENDED change retains its effect in CURRENT→MERGED |
| concurrent_intent | BASE→CURRENT changes retain their effect in INTENDED→MERGED |
| coherence | MERGED has no incompatible obligations/facts or broken references |

Each field is PRESERVED, CONFLICT or UNKNOWN. Exact dictionary equality binds all fields; order may differ but no field can be omitted or added. Only all-PRESERVED permits commit. Even non-promoting results compare exactly. There is no confidence tolerance, risk tier, quote substring or similarity prefilter.

Review must preserve actors, scope, qualifiers, negation, exceptions, dates and units across sections. Different character ranges do not establish independent meaning. Unavailable external context should produce UNKNOWN.

Leader errors, malformed results and validator exceptions disagree. Network retry/rotation governs unavailable consensus; the contract cannot create a safe fallback.

The assessment binds exact head and patch digests, candidate and all checks. Commit is deterministic, has no caller-supplied candidate argument, and cannot generate or modify prose.

## Evidence

Tests explicitly execute captured validators, not just leader mocks. The suite covers all 27 judgment combinations, stale-safe assessments, cancellation, exact expiry, immutable history, editor roles, outsider assessment-budget protection and deterministic same-section rejection.

The unmocked live script reviews a direct format change, a time change, a hidden cross-section conflict and a safe rebase over the new format. Recorded votes preserve disagreements and idle states. Finalization is not described as unanimity.

These tests and examples demonstrate protocol behavior. Semantic model agreement is not a formal proof of safety for every interpretation or independent verification of the document's claims.

Primary references: [equivalence principle](https://docs.genlayer.com/developers/intelligent-contracts/equivalence-principle), [nondeterministic isolation](https://docs.genlayer.com/developers/intelligent-contracts/features/non-determinism), [finalized reads](https://docs.genlayer.com/developers/decentralized-applications/reading-data).
