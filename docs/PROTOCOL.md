# Four snapshots and a transactional head

## Contract boundary

Section non-overlap does not imply semantic independence. Changed actors, event formats, exceptions, units and cross-references can affect another section. Validators compare complete documents. The contract deterministically composes candidate bytes and enforces the versioned transition.

An editor fixes replacements. The contract owns revision history, roles, evidence inputs, assessment identity, stale-head protection and expiry. A frontend can preview diffs; there is no authoritative off-chain decision service.

## State

| Record | Immutable data | Mutable state |
|---|---|---|
| Document | Title, owner, fixed editor set | Head number/digest, counters |
| Revision | Number, parent digest, originating patch, sections | None |
| Patch | Author, base revision/digest, replacements, expiry | OPEN/APPLIED/CANCELLED/EXPIRED, applied revision |
| Assessment | Head, patch digest, candidate, checks and result | None |

Typed persistent TreeMaps store canonical JSON under document:id. Commitments bind protocol, chain, contract and document.

## Lifecycle

1. Create document with 2–6 sections and fixed editors. Owner is included. Section positions are stable: no insertion, deletion or reordering.
2. An editor prepares 1–3 exact replacements against an existing base. Duplicate, empty, unchanged and invalid edits are rejected.
3. An editor requests assessment with the expected current head digest. A touched section changed since base yields TEXT_CONFLICT without a model call. Otherwise all four complete snapshots undergo semantic consensus.
4. Anyone may commit a SAFE assessment only if its head number/digest and patch digest still match, patch remains OPEN/unexpired, and revision capacity remains.
5. Author or owner may cancel before expiry; anyone may close the patch at/after expiry.

There is no “latest assessment” pointer or implicit approval. Callers choose an exact assessment ID. Applied patches cannot be replayed. Cancellation and expiry disable every existing assessment for that patch.

## Race example

```text
head 0: time 10:00, format online
assess A (time 11:00) against head 0 -> SAFE X
assess B (format in-person) against head 0 -> SAFE Y
commit Y -> head 1
commit X -> REVERT: stale assessment
reassess A against head 1 -> SAFE Z
commit Z -> head 2: time 11:00, format in-person
```

Even disjoint edits require fresh review after another commit. A hidden dependency may change the judgment. The compare-and-swap check prevents time-of-check/time-of-use substitution.

## API

```python
d = merge.create_document("Workshop", json.dumps(sections), json.dumps([editor]))
p = merge.prepare_patch(d, 0, '[{"section":2,"text":"Session starts at 11:00 UTC."}]', 3600)
head = merge.get_document(d)["head_digest"]
a = merge.assess(d, p, head)
if merge.get_assessment(d, a)["payload"]["status"] == "SAFE":
    merge.commit(d, a)
```

Wait for finality before external publication. A finalized assessment alone is not a committed revision. On stale-head failure, inspect the new head and reassess.

## Limits and distinct purpose

2–6 sections of 800 characters, up to 8 editors including owner, 64 patches, 128 assessments, 32 committed revisions, 1–3 replacements per patch, lifetime 60 seconds to seven days. History is immutable; use a new document once capacity is reached.

This is versioned document merging. It does not consume action permits, allocate counterparties, infer identity, classify governance risk or settle escrow.
