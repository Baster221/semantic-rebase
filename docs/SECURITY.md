# Threat model

## Editor authority

Editors are authorized content authors. The contract does not determine whether an edit is desirable, legally valid or aligned with unstated preferences. A compromised editor can propose harmful but coherent text. Editorial governance belongs in a separate authorization layer. Editor membership is fixed; migrating to a new document is required for rotation.

Initial content is stored without semantic review. Assessments concern the supplied candidate and exact head, rather than certifying historical versions or external facts. Missing context should yield UNKNOWN.

Only editors can prepare patches or consume assessment history. Outsiders can commit an already-safe result but cannot change its text, revive a cancelled patch, or spend review capacity. Trusted editors can exhaust bounded capacity; the design assumes their cooperation for availability.

## Adversarial text and model limits

Prompt injection, broad wording, negation and hidden cross-references are treated as untrusted content. Validators derive all substantive checks independently. A correlated model error or malicious majority can still approve a bad merge. No quote-only, format-only or leader-self-explanation check stands in for semantic evidence.

Live scenarios are focused demonstrations, not an adversarial-model benchmark or formal semantic proof. Sensitive uses require an appropriate evaluation corpus and human editorial process.

The first live pilot rejected an indirect “access method in section 0” reference after an event-format change. The unchanged source was then exercised with an explicit registration section. The pilot's conservative rejection and actual votes are retained in [pilot-rejection.json](../evidence/pilot-rejection.json), rather than being counted as a successful merge. Model disagreement can reduce availability even when no harmful state is committed.

## Race protection

SAFE does not reserve the head. Another commit makes the assessment stale. Commit checks exact head number/digest, immutable patch digest, open status, expiry and capacity before mutation. The caller supplies only document and assessment IDs.

There are no external messages, assets or callback hooks. External consumers wait for finalized revision state; an assessment alone cannot authorize publication.

## Expiry, history and privacy

Only author/owner may cancel before expiry. At the exact expiry timestamp, assessment/commit stop and anyone can mark EXPIRED. Old assessments remain audit records and cannot revive a closed patch.

Fixed section, text, edit and history bounds limit each model task and storage operation. No global scan occurs. All revisions, pending and cancelled edits remain public. No confidential-document or deletion guarantee is made. The supplied deployment is StudioNet, not Bradbury.
