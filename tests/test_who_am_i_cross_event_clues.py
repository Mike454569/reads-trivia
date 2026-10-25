"""Who Am I requires several verified football facts, never metadata padding."""
from unittest.mock import patch
import pytest
from tools.director_v05.lore_mechanics import compile_progressive_identity

class DB:
    def execute(self, query, params=()):
        assert "universal_event_subject" in query
        return self
    def fetchall(self):
        return [{"event_id": "second", "title": "Player A returned to win the rivalry game in overtime."},
                {"event_id": "third", "title": "Player A threw the decisive touchdown during the bowl win."}]

def test_identity_enriches_with_verified_other_events():
    event={"event_id":"first","league":"CFB"}
    with patch("tools.director_v05.lore_mechanics._event",return_value=(event,{"sensitive":False})), \
         patch("tools.director_v05.lore_mechanics._subjects",return_value=[{"subject_type":"CFB_PLAYER","subject_id":"p1"}]), \
         patch("tools.director_v05.lore_mechanics.resolve_label",return_value="Player A"), \
         patch("tools.director_v05.lore_mechanics._safe_clues",return_value=["League: CFB."]), \
         patch("tools.director_v05.lore_mechanics._prov",side_effect=lambda db, ids: {"provenance_complete":True,"event_ids":ids,"evidence":["verified"]}):
        result=compile_progressive_identity(DB(),"first")
    clues=[x["text"] for x in result["clues"]]
    assert len(clues)==3
    assert all("Player A" not in clue for clue in clues)
    assert any("rivalry game" in clue for clue in clues)
    assert any("bowl win" in clue for clue in clues)
    # The answer must cite the separate events supporting its clues.
    assert result["provenance"]["event_ids"] == ["first", "second", "third"]

def test_identity_rejects_metadata_only():
    class EmptyDB(DB):
        def fetchall(self): return []
    with patch("tools.director_v05.lore_mechanics._event",return_value=({"league":"NFL"},{"sensitive":False})), \
         patch("tools.director_v05.lore_mechanics._subjects",return_value=[{"subject_type":"NFL_PLAYER","subject_id":"p1"}]), \
         patch("tools.director_v05.lore_mechanics.resolve_label",return_value="Player A"), \
         patch("tools.director_v05.lore_mechanics._safe_clues",return_value=["League: NFL.","Season: 2025."]):
        with pytest.raises(ValueError,match="INSUFFICIENT_DISTINCT_IDENTITY_FACTS"):
            compile_progressive_identity(EmptyDB(),"first")
