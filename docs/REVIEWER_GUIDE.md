# Review evidence for semantic concurrency

Start with the scenario in LIVE_VALIDATION.md. The conflicting edits touch sections 0 and 1, so ordinary section-level conflict detection cannot reject their semantic combination.

## Key code paths

- `prepare_patch` freezes the base and exact replacements. There is no generated or caller-replaceable merge text.
- `assess` requires an editor and an explicit expected head. Same-section changes short-circuit before LLM execution.
- `_review` supplies every complete snapshot to each independent model execution. All three effect-bearing checks compare exactly.
- `commit` receives no text argument. It compares head number/digest and patch digest, checks status/expiry, then appends the immutable candidate.
- `cancel` cannot revive or overwrite an applied patch; expiry blocks existing SAFE assessments.

## Focused regression tests

Inspect `test_stale_safe_assessment_cannot_overwrite_new_head`, `test_cross_section_semantic_conflict_keeps_head_unchanged`, `test_outsider_cannot_exhaust_assessment_budget` and `test_all_27_semantic_check_vectors_have_exact_safe_boundary`.

The suite also explicitly executes captured validator closures with independent opposing judgments. Direct mode otherwise runs only the leader; that limitation is stated rather than hidden.

## Additional semantic evaluations

Try changing actors in one section while another patch introduces a pronoun; changing a monetary unit while another patch changes an amount; narrowing an exception while another patch expands a scope; or inserting a reference to a removed fact. Test both safe and unsafe pairs. A model's agreement on one workshop example is not a guarantee for these domains.

## Independent reproduction

CI runs pinned lint/direct tests and offline deployment-manifest integrity. The public read-only verifier re-fetches source, confirms every recorded receipt targets this deployment and finalized with successful execution, then compares the live head and revision history against state.json. No wallet is needed.

The optional mutating smoke script uses three distinct ephemeral accounts: owner, authorized editor/reviewer, and permissionless committer. It deploys a fresh StudioNet address and leaves the recorded deployment alone unless explicitly invoked with --record.
