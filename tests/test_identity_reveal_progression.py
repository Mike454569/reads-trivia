"""The Who Am I reveal sequence must progress from background to signature achievement."""
from unittest.mock import patch
from tools.director_v05.lore_mechanics import compile_progressive_identity

class VerifiedEvents:
    def execute(self,sql,params=()):
        assert "universal_event_subject" in sql
        return self
    def fetchall(self):
        return [
          {"event_id":"milestone","title":"Jordan Example won the Super Bowl MVP after a four-touchdown performance."},
          {"event_id":"background","title":"Jordan Example transferred colleges before earning a starting opportunity."},
          {"event_id":"midcareer","title":"Jordan Example threw for 300 yards in a dramatic rivalry comeback."},
        ]

def test_signature_milestone_is_last_not_first():
    with patch("tools.director_v05.lore_mechanics._event",
               return_value=({"league":"NFL"},{"sensitive":False})), \
         patch("tools.director_v05.lore_mechanics._subjects",
               return_value=[{"subject_type":"NFL_PLAYER","subject_id":"jordan"}]), \
         patch("tools.director_v05.lore_mechanics.resolve_label",
               return_value="Jordan Example"), \
         patch("tools.director_v05.lore_mechanics._safe_clues",
               return_value=["League: NFL."]), \
         patch("tools.director_v05.lore_mechanics._prov",
               side_effect=lambda db,ids: {"provenance_complete":True,"event_ids":ids,"evidence":["source"]}):
        q=compile_progressive_identity(VerifiedEvents(),"anchor")
    clues=[c["text"] for c in q["clues"]]
    assert len(clues)==3
    assert "transferred colleges" in clues[0]
    assert "Super Bowl MVP" in clues[-1]
    assert len(q["provenance"]["event_ids"])==4
