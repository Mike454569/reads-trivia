from tools.director_v05.capability_compiler import compile_capabilities, eligible_event_where

def test_missing_family_blocks_concept():
    cov={"families":{"culture_story":{"status":"MISSING"},"off_field":{"status":"PRESENT"}}}
    assert compile_capabilities(cov)["FUNNY_MOMENTS"]["status"]=="UNSUPPORTED"

def test_partial_family_limits_concept():
    cov={"families":{"draft":{"status":"PRESENT"},"derived":{"status":"PARTIAL"}}}
    assert compile_capabilities(cov)["DRAFT_BUSTS"]["status"]=="SUPPORTED_WITH_LIMITATIONS"

def test_sensitive_events_require_verified_evidence():
    where,args=eligible_event_where("LEGAL_HISTORY")
    assert "verification_status='VERIFIED'" in where
    assert "evidence_tier IN" in where
    assert "legal" in args
