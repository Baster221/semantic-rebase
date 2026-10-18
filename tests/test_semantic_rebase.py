import copy
import itertools
import json
import pytest


BASE = [
    "Event format: This workshop is held online only.",
    "Registration: Participants must register before attending the workshop.",
    "Session time: Starts at 10:00 UTC.",
]
SAFE = {"patch_intent": "PRESERVED", "concurrent_intent": "PRESERVED", "coherence": "PRESERVED"}


def mock(vm, checks=SAFE):
    vm.clear_mocks()
    vm.mock_llm(r"SEMANTIC_REBASE_REVIEW_V1", json.dumps(checks))


@pytest.fixture
def setup(direct_vm, direct_deploy, direct_alice, direct_bob):
    direct_vm.warp("2026-10-18T00:00:00Z")
    direct_vm.sender = direct_alice
    c = direct_deploy("contracts/semantic_rebase.py", sdk_version="v0.2.12")
    from genlayer import Address
    d = c.create_document("Workshop instructions", json.dumps(BASE), json.dumps([str(Address(direct_bob))]))
    mock(direct_vm)
    return c, d


def patch(c, d, section=2, text="Session time: Starts at 11:00 UTC.", base=0, lifetime=3600):
    return c.prepare_patch(d, base, json.dumps([{"section": section, "text": text}]), lifetime)


def assess(c, d, p):
    return c.assess(d, p, c.get_document(d)["head_digest"])


def test_complete_prepare_assess_commit_is_snapshot_bound(setup, direct_vm, direct_bob, direct_charlie):
    c, d = setup
    p = patch(c, d)
    direct_vm.sender = direct_bob
    a = assess(c, d, p)
    assert direct_vm.run_validator() is True
    assert c.get_document(d)["head"] == 0  # no head mutation during assessment
    direct_vm.sender = direct_charlie  # commit cannot alter the assessed patch
    assert c.commit(d, a) == 1
    assert c.get_revision(d, 1)["payload"]["sections"] == [BASE[0], BASE[1], "Session time: Starts at 11:00 UTC."]
    assert c.get_patch(d, p)["status"] == "APPLIED"
    with direct_vm.expect_revert("closed"):
        c.commit(d, a)


@pytest.mark.parametrize("field,label", list(itertools.product(SAFE, ("CONFLICT", "UNKNOWN"))))
def test_validator_binds_every_effect_bearing_check(setup, direct_vm, field, label):
    c, d = setup
    assess(c, d, patch(c, d))
    mock(direct_vm, {**SAFE, field: label})
    assert direct_vm.run_validator() is False


@pytest.mark.parametrize("field", SAFE)
def test_unknown_and_conflict_cannot_commit(setup, direct_vm, field):
    c, d = setup
    mock(direct_vm, {**SAFE, field: "UNKNOWN"})
    a = assess(c, d, patch(c, d))
    assert c.get_assessment(d, a)["payload"]["status"] == "SEMANTIC_CONFLICT"
    with direct_vm.expect_revert("does not permit"):
        c.commit(d, a)
    assert c.get_document(d)["head"] == 0


def test_stale_safe_assessment_cannot_overwrite_new_head(setup, direct_vm):
    c, d = setup
    p1 = patch(c, d, 0, "Event format: This workshop is in person only at Room A.")
    p2 = patch(c, d)
    a1, a2 = assess(c, d, p1), assess(c, d, p2)
    c.commit(d, a1)
    with direct_vm.expect_revert("Stale assessment"):
        c.commit(d, a2)
    new_assessment = assess(c, d, p2)
    c.commit(d, new_assessment)
    final = c.get_revision(d, 2)["payload"]["sections"]
    assert final[0] == "Event format: This workshop is in person only at Room A."
    assert final[2] == "Session time: Starts at 11:00 UTC."
    assert c.get_revision(d, 2)["payload"]["parent"] == c.get_revision(d, 1)["digest"]


def test_cross_section_semantic_conflict_keeps_head_unchanged(setup, direct_vm):
    c, d = setup
    stale = patch(c, d, 1, "Registration: Register to join online; do not travel to any physical venue.")
    concurrent = patch(c, d, 0, "Event format: This workshop is in person only at Room A; no online access.")
    c.commit(d, assess(c, d, concurrent))
    before = copy.deepcopy(c.get_document(d))
    mock(direct_vm, {"patch_intent": "CONFLICT", "concurrent_intent": "CONFLICT", "coherence": "CONFLICT"})
    a = assess(c, d, stale)
    assert direct_vm.run_validator() is True
    assert c.get_assessment(d, a)["payload"]["status"] == "SEMANTIC_CONFLICT"
    with direct_vm.expect_revert("does not permit"):
        c.commit(d, a)
    assert c.get_document(d)["head_digest"] == before["head_digest"]


def test_same_section_conflict_short_circuits_model(setup, direct_vm):
    c, d = setup
    first, stale = patch(c, d), patch(c, d, text="Session time: Starts at 12:00 UTC.")
    c.commit(d, assess(c, d, first))
    direct_vm.clear_mocks()  # a model invocation here would fail
    a = assess(c, d, stale)
    assert c.get_assessment(d, a)["payload"]["status"] == "TEXT_CONFLICT"
    with direct_vm.expect_revert("does not permit"):
        c.commit(d, a)


def test_assessment_requires_explicit_current_head(setup, direct_vm):
    c, d = setup
    p = patch(c, d)
    with direct_vm.expect_revert("Head changed"):
        c.assess(d, p, "0" * 64)
    assert c.get_document(d)["assessments"] == 0


def test_only_configured_editors_can_prepare(setup, direct_vm, direct_bob, direct_charlie):
    c, d = setup
    direct_vm.sender = direct_charlie
    with direct_vm.expect_revert("Only document editor"):
        patch(c, d)
    direct_vm.sender = direct_bob
    assert patch(c, d) == 1


def test_outsider_cannot_exhaust_assessment_budget(setup, direct_vm, direct_charlie):
    c, d = setup
    p = patch(c, d)
    direct_vm.sender = direct_charlie
    with direct_vm.expect_revert("Only document editor"):
        assess(c, d, p)
    assert c.get_document(d)["assessments"] == 0


def test_cancel_is_bound_to_author_owner_or_timeout(setup, direct_vm, direct_bob, direct_charlie):
    c, d = setup
    direct_vm.sender = direct_bob
    p = patch(c, d, lifetime=60)
    direct_vm.sender = direct_charlie
    with direct_vm.expect_revert("Only author or owner"):
        c.cancel(d, p)
    direct_vm.warp("2026-10-18T00:01:00Z")
    c.cancel(d, p)
    assert c.get_patch(d, p)["status"] == "EXPIRED"
    with direct_vm.expect_revert("already closed"):
        c.cancel(d, p)


def test_expiry_blocks_previously_safe_assessment_at_exact_boundary(setup, direct_vm):
    c, d = setup
    p = patch(c, d, lifetime=60)
    a = assess(c, d, p)
    direct_vm.warp("2026-10-18T00:01:00Z")
    with direct_vm.expect_revert("expired"):
        c.commit(d, a)
    with direct_vm.expect_revert("expired"):
        assess(c, d, p)


def test_cancellation_disables_outstanding_safe_assessment(setup, direct_vm):
    c, d = setup
    p = patch(c, d)
    a = assess(c, d, p)
    c.cancel(d, p)
    with direct_vm.expect_revert("closed"):
        c.commit(d, a)


@pytest.mark.parametrize("changes", [[], [{"section": True, "text": "Other"}], [{"section": 8, "text": "Other"}],
    [{"section": 0, "text": "Other"}, {"section": 0, "text": "Duplicate"}],
    [{"section": 0, "text": BASE[0]}], [{"section": 0, "text": "x" * 801}],
    [{"section": 0, "text": "Other", "hidden": "bypass"}]])
def test_patch_schema_rejects_ambiguous_or_unbounded_edits(setup, direct_vm, changes):
    c, d = setup
    before = c.get_document(d)
    with direct_vm.expect_revert():
        c.prepare_patch(d, 0, json.dumps(changes), 3600)
    assert c.get_document(d) == before


@pytest.mark.parametrize("bad", [{}, {**SAFE, "confidence": "high"}, {**SAFE, "coherence": True}, {**SAFE, "patch_intent": "SAFE"}])
def test_malformed_consensus_cannot_prepare_commit(setup, direct_vm, bad):
    c, d = setup
    p = patch(c, d)
    before = c.get_document(d)
    mock(direct_vm, bad)
    with direct_vm.expect_revert("LLM_ERROR"):
        assess(c, d, p)
    assert c.get_document(d) == before


def test_error_and_missing_check_leader_disagree(setup, direct_vm):
    c, d = setup
    assess(c, d, patch(c, d))
    assert direct_vm.run_validator(leader_result={"coherence": "PRESERVED"}) is False
    assert direct_vm.run_validator(leader_error=RuntimeError("timeout")) is False


def test_patch_order_normalization_preserves_exact_bytes(setup, direct_vm):
    c, d = setup
    changes = [{"section": 2, "text": "Session time: Starts at 11:00 UTC."}, {"section": 0, "text": "Event format: Online only, using Zoom."}]
    p = c.prepare_patch(d, 0, json.dumps(changes), 3600)
    assert [row["section"] for row in c.get_patch(d, p)["payload"]["changes"]] == [0, 2]
    a = assess(c, d, p)
    candidate = c.get_assessment(d, a)["payload"]["candidate"]
    assert candidate == [changes[1]["text"], BASE[1], changes[0]["text"]]


def test_revision_history_and_domain_commitments_are_immutable(setup, direct_vm):
    c, d = setup
    original = copy.deepcopy(c.get_revision(d, 0))
    p = patch(c, d)
    patch_record = c.get_patch(d, p)
    a = assess(c, d, p)
    c.commit(d, a)
    assert c.get_revision(d, 0) == original
    assert c.get_patch(d, p)["payload"] == patch_record["payload"]
    other = c.create_document("Other document", json.dumps(BASE), "[]")
    assert c.get_revision(other, 0)["digest"] != original["digest"]
    payload = c.get_assessment(d, a)["payload"]
    assert all(key in payload for key in ("chain_id", "contract", "document", "head_digest", "patch_digest", "candidate"))


def test_all_27_semantic_check_vectors_have_exact_safe_boundary(setup, direct_vm):
    c, d = setup
    p = patch(c, d)
    for labels in itertools.product(("PRESERVED", "CONFLICT", "UNKNOWN"), repeat=3):
        checks = dict(zip(SAFE, labels))
        mock(direct_vm, checks)
        a = assess(c, d, p)
        result = c.get_assessment(d, a)["payload"]
        assert (result["status"] == "SAFE") == all(label == "PRESERVED" for label in labels)
        assert result["checks"] == checks


def test_patch_and_assessment_history_bounds(setup, direct_vm):
    c, d = setup
    p = patch(c, d)
    for _ in range(63):
        patch(c, d)
    with direct_vm.expect_revert("capacity"):
        patch(c, d)
    for _ in range(128):
        assess(c, d, p)
    with direct_vm.expect_revert("capacity"):
        assess(c, d, p)
    assert c.get_document(d)["patches"] == 64
    assert c.get_document(d)["assessments"] == 128


def test_revision_capacity_has_no_review_or_commit_bypass(setup, direct_vm):
    c, d = setup
    for revision in range(32):
        p = patch(c, d, text=f"Session time: Starts at {revision + 11}:00 UTC.", base=revision)
        c.commit(d, assess(c, d, p))
    assert c.get_document(d)["head"] == 32
    with direct_vm.expect_revert("capacity"):
        patch(c, d, base=32)
