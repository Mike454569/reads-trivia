"""Sourced story titles are not wrapped in robotic metadata copy."""
from tools.director_v05.lore_trivia import _safe_clues

def test_story_headline_precedes_generic_summary():
    event={"event_type":"OFF_FIELD_ODDITY","title":"An unusual draft phone call disrupted the first round",
           "neutral_summary":"The subject of a documented off-field football story was featured in coverage.",
           "league":"NFL","event_date":None}
    clues=_safe_clues(event)
    assert clues[0]=="An unusual draft phone call disrupted the first round."
    assert not any(c.startswith("Event label:") for c in clues)
