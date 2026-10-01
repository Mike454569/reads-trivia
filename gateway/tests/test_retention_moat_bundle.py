from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")


def test_home_uses_priority_engine_instead_of_feature_dump():
    assert "function homePriorityFeedHtml()" in APP
    assert "homePriorityFeedHtml() +" in APP
    home = APP.split("function renderHome() {", 1)[1].split("/* ============================== NFL/CFB mode picker", 1)[0]
    assert "friendRivalAlertHtml() +" not in home
    assert "teamBattleHtml() +" not in home
    assert "retentionMissionHtml() +" not in home
    assert "weeklyPersonalGoalsHtml() +" not in home
    assert "weeklyRetentionGoalHtml() +" not in home


def test_football_dna_is_derived_from_real_mastery_and_rating():
    assert "function footballDNAData()" in APP
    assert "personalizationMasteryRows()" in APP
    assert "personalizationLeagueProfile()" in APP
    assert "var rating = getRating();" in APP
    assert "function footballDNAHtml(compact)" in APP
    profile = APP.split("function renderProfile() {", 1)[1].split("function profileModeCardsHtml()", 1)[0]
    assert "footballDNAHtml(false)" in profile
    assert "personalizationMasteryHtml()" in profile
    assert "weeklyPersonalGoalsHtml()" in profile


def test_format_collections_reduce_100_mode_choice_overload():
    assert "function formatCollectionsHtml()" in APP
    assert "New to You" in APP
    assert "Quick Hitters" in APP
    assert "Think You Know Ball?" in APP
    assert "formatCollectionsHtml() +" in APP
    assert ".format-collection-row" in CSS


def test_daily_summary_uses_live_rival_rows_for_social_proof():
    assert "function dailySocialProofHtml()" in APP
    assert "dailyRivalRows('today')" in APP
    assert "dailyRivalScopeRows(today,'friends')" in APP
    assert "dailyRivalScopeRows(today,'team')" in APP
    summary = APP.split("function renderDailySummary() {", 1)[1].split("function renderDailyScreen()", 1)[0]
    assert "dailySocialProofHtml()" in summary


def test_retention_moat_styles_are_mobile_safe():
    assert ".home-priority-stack{display:grid" in CSS
    assert ".football-dna-grid" in CSS
    assert ".format-collection-row" in CSS
    assert "@media(max-width:800px)" in CSS


def test_community_2_reactions_replies_and_challenges_are_wired():
    fb = (ROOT / "firebase-sync.js").read_text(encoding="utf-8")
    assert "reactCommunity: function" in fb
    assert "replyCommunity: function" in fb
    assert "window.__fbSync.reactCommunity" in fb
    assert "window.__fbSync.replyCommunity" in fb
    assert "function communityReactionCounts(row)" in APP
    assert "data-community-react" in APP
    assert "data-community-reply-toggle" in APP
    assert "data-community-reply-send" in APP
    assert "data-friend-challenge" in APP


def test_reads_arena_quick_match_uses_existing_h2h_pipeline():
    fb = (ROOT / "firebase-sync.js").read_text(encoding="utf-8")
    assert "window.__fbSync.findArenaMatch" in fb
    assert "window.__fbSync.watchArenaTicket" in fb
    assert "window.__fbSync.cancelArenaTicket" in fb
    assert "arenaModes=['quiz','cfbQuiz','grid','cfbGrid','silhouette','speed','cfbSpeed']" in fb
    assert "function arenaQuickMatchStart()" in APP
    assert "function arenaPanelHtml()" in APP
    assert "Find Ranked Match" in APP
    assert "h2hOpenExistingCode(code)" in APP
    assert ".arena-panel" in CSS
