"""Certification rules for the v0.5 production stress harness."""
from __future__ import annotations

DEFAULT_THRESHOLDS={
 "min_ready_bridge_adapters":10,
 "min_discovered_chains":25,
 "min_eligible_chains":10,
 "min_passed_questions":10,
 "max_bridge_errors":0,
}

def certify(report,thresholds=None):
    t={**DEFAULT_THRESHOLDS,**(thresholds or {})}
    bridge=report.get("bridge",{})
    facts=report.get("facts",{})
    chains=report.get("chains",{})
    questions=report.get("questions",{})
    ready=sum(1 for v in bridge.values() if v.get("status")=="READY")
    bridge_errors=sum(1 for v in facts.values() if v.get("status")=="ERROR")
    passed=sum(v for k,v in questions.items() if k.endswith(":PASSED"))
    checks={
      "ready_bridge_adapters":{"actual":ready,"required":t["min_ready_bridge_adapters"],"pass":ready>=t["min_ready_bridge_adapters"]},
      "bridge_errors":{"actual":bridge_errors,"required_max":t["max_bridge_errors"],"pass":bridge_errors<=t["max_bridge_errors"]},
      "discovered_chains":{"actual":chains.get("discovered",0),"required":t["min_discovered_chains"],"pass":chains.get("discovered",0)>=t["min_discovered_chains"]},
      "eligible_chains":{"actual":chains.get("eligible",0),"required":t["min_eligible_chains"],"pass":chains.get("eligible",0)>=t["min_eligible_chains"]},
      "passed_questions":{"actual":passed,"required":t["min_passed_questions"],"pass":passed>=t["min_passed_questions"]},
    }
    return {"status":"PASSED" if all(x["pass"] for x in checks.values()) else "FAILED","checks":checks}

def assert_certified(report,thresholds=None):
    result=certify(report,thresholds)
    if result["status"]!="PASSED":
        failed=[k for k,v in result["checks"].items() if not v["pass"]]
        raise RuntimeError("V05_STRESS_CERTIFICATION_FAILED:"+",".join(failed))
    return result
