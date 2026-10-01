from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CREATOR = (ROOT / "creator-ui.js").read_text(encoding="utf-8")
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")


def test_creator_workspace_has_clear_primary_navigation():
    assert "creator-topbar" in CREATOR
    assert "Reads Creator" in CREATOR
    assert "Engine Workspace" in CREATOR
    assert 'data-creator-nav="home"' in CREATOR
    assert 'data-creator-nav="queue"' in CREATOR
    assert 'data-creator-nav="capabilities"' in CREATOR


def test_creator_format_library_is_searchable_and_filterable():
    assert "formatQuery: ''" in CREATOR
    assert "formatCategory: 'All'" in CREATOR
    assert "function creatorFormatCategories()" in CREATOR
    assert "function creatorFormatMatches(entry, query, category)" in CREATOR
    assert "function creatorSetFormatQuery(query)" in CREATOR
    assert "function creatorSetFormatCategory(category)" in CREATOR
    assert 'id="creator-format-search"' in CREATOR
    assert "creator-category-strip" in CREATOR
    assert "creator-format-grid" in CREATOR
    assert "data-creator-format-category" in CREATOR
    assert "creatorSetFormatCategory(t.dataset.creatorFormatCategory)" in APP
    assert "creatorSetFormatQuery(e.target.value)" in APP


def test_creator_home_prioritizes_describe_or_proven_format_flow():
    assert "GAME FACTORY" in CREATOR
    assert "What do you want to build?" in CREATOR
    assert "Check & Build" in CREATOR
    assert "OR START FROM A PROVEN FORMAT" in CREATOR
    assert "Choose a proven mechanic" in CREATOR
    assert "DIRECT" in CREATOR
    assert "GUIDED" in CREATOR


def test_creator_auth_keeps_token_out_of_source():
    assert "OWNER WORKSPACE" in CREATOR
    assert "Gateway admin token" in CREATOR
    assert "type=\"password\"" in CREATOR
    assert "sessionStorage.setItem(CREATOR_TOKEN_STORAGE_KEY" in CREATOR
    # Never regress to a bundled secret/token value.
    assert "3dd68627d611b24bf1c527aab231fc1ca629d5915b3d97b418e27fe4c4197a54" not in CREATOR


def test_creator_redesign_is_responsive():
    for selector in [
        ".creator-workspace",
        ".creator-topbar",
        ".creator-hero",
        ".creator-compose-card",
        ".creator-format-grid",
        ".creator-auth-shell",
    ]:
        assert selector in CSS
    assert "@media(max-width:620px)" in CSS
