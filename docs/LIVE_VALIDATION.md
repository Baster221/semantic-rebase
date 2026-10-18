# A hidden cross-section conflict and a safe rebase

Network: **GenLayer StudioNet**, chain ID 61999. Validation date: 18 October 2026. This hosted GenVM deployment is not Bradbury.

Contract: [0x4a91b4f70AA847eD0d6c67D8F36b43B82E27538d](https://explorer-studio.genlayer.com/address/0x4a91b4f70AA847eD0d6c67D8F36b43B82E27538d).

Deployment transaction: `0x740078138b89d993e942c042f20092cccdd998073acf5f79549b0b14a207cce0`. [Manifest](../deployment.json) includes identical local/deployed source hashes and the pinned runner.

## Three branches, two commits

Revision 0 has three sections: online-only format, a requirement to register, and a 10:00 UTC start.

- Patch 1 changes section 0 to in-person-only attendance at Room A, with no online access.
- Patch 2 changes section 1 to registration for an online meeting link, explicitly forbidding travel to a physical venue.
- Patch 3 changes section 2 to an 11:00 UTC start.

All three patches use base revision 0 and fixed editor replacement text.

| Operation | Observed result |
|---|---|
| Assess time patch against head 0 | SAFE assessment 1 |
| Assess format patch against head 0 | SAFE assessment 2 |
| Permissionless commit of assessment 2 | Revision 1: in-person format |
| Assess old registration branch against revision 1 | SEMANTIC_CONFLICT assessment 3 |
| Reassess old time branch against revision 1 | SAFE assessment 4 |
| Permissionless commit of assessment 4 | Revision 2: in-person format and 11:00 start |

The online-only registration patch touches a different section from the format change. It reaches substantive model review, rather than deterministic same-section rejection. Its conflict does not change the head.

Assessment 1 remains an immutable SAFE record for head 0, but its head digest no longer matches. The successful commit uses fresh assessment 4. Direct tests explicitly attempt stale commit and confirm rejection; this live run does not count a failed write as a successful interaction.

Three distinct ephemeral addresses act as owner, editor/reviewer and permissionless committer. No signing keys were saved. The deployed contract can host new documents owned by other users.

## Evidence and an unfavorable pilot

The main run has 11 successful finalized transactions in [network.json](../evidence/network.json), with real leader outputs, nondeterministic judgments and votes. [state.json](../evidence/state.json) contains all three revisions, patches, assessments and participant roles.

The initial pilot used an indirect “access method in section 0” instruction. Consensus conservatively rejected the format edit on coherence, and the script stopped before any merge. [pilot-rejection.json](../evidence/pilot-rejection.json) retains that deployment, all seven finalized receipts and both assessments. Source was unchanged for the explicit-registration run. This result demonstrates possible false rejection and disagreement; it is not represented as a successful merge.

Normal validator consensus was used. Idle and disagree votes are retained rather than described as unanimous agreement. These focused examples do not establish universal semantic correctness.

## Verify without a wallet

```bash
npm ci --ignore-scripts
npm run verify
python scripts/check_manifest.py
```

Online verification compares deployed source bytes, every main/pilot receipt's target and FINALIZED/SUCCESS status, live document head and complete revision history, and the pilot's recorded assessments. Node.js 22+ and internet are required. The Python command checks local manifest consistency only.

`npm run smoke` performs a mutating demonstration at a new address. It does not overwrite supplied evidence unless --record is explicitly added.
