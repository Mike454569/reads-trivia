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


def test_progression_road_unifies_rank_frame_and_share_unlocks():
    assert "function progressionRoadHtml()" in APP
    assert "ROAD TO LEGEND" in APP
    assert "PROFILE_COSMETICS" in APP
    assert "SHARE_CARD_DESIGNS" in APP
    profile = APP.split("function renderProfile() {", 1)[1].split("function profileModeCardsHtml()", 1)[0]
    assert "progressionRoadHtml()" in profile
    assert ".progression-road" in CSS


def test_social_proof_uses_real_aggregate_play_counts():
    assert "function globalModePlayCount(mode)" in APP
    assert "window.__fbSync.playCounts" in APP
    assert "function socialProofModeHtml(mode, compact)" in APP
    assert "socialProofModeHtml(m.id, true)" in APP
    assert "state.screen === 'stats' || state.screen === 'home'" in APP


def test_live_football_favorite_context_never_invents_scores():
    live = (ROOT / "live-football-ui.js").read_text(encoding="utf-8")
    assert "function liveFootballFavoriteOpenGames()" in live
    assert "function liveFootballFavoriteContextHtml()" in live
    assert "g.status !== 'FINAL' && g.status !== 'CANCELED'" in live
    context = live.split("function liveFootballFavoriteContextHtml()", 1)[1].split("function liveFootballHomeHtml()", 1)[0]
    assert "away_score" not in context
    assert "home_score" not in context
    assert ".live-favorite-context" in CSS


def test_daily_reads_v3_adds_freshness_and_one_more_hooks():
    assert "YOUR DAILY 5 · V3" in APP
    assert "Daily Reads v3" in APP
    assert "function dailyTomorrowPlanHtml()" in APP
    assert "function dailyOneMoreHtml()" in APP
    summary = APP.split("function renderDailySummary() {", 1)[1].split("function renderDailyScreen()", 1)[0]
    assert "dailyTomorrowPlanHtml()" in summary
    assert "dailyOneMoreHtml()" in summary
    assert ".daily-tomorrow-plan" in CSS
    assert ".daily-one-more" in CSS


def test_football_dna_2_has_real_trait_levels_and_career_identity():
    assert "function footballDNATraitLevel(row)" in APP
    assert "function footballDNATraits()" in APP
    assert "function footballDNACareerStage()" in APP
    assert "Career identity" in APP
    assert "footballDNATraits().map" in APP
    assert ".football-dna-traits" in CSS


def test_seasonal_progression_has_missions_without_replacing_career_rank():
    assert "function seasonalMilestones()" in APP
    assert "function seasonalMissionHtml()" in APP
    assert "Career stays permanent" in APP
    dashboard = APP.split("function personalDashboardHtml()", 1)[1].split("function renderHome()", 1)[0]
    assert "seasonalMissionHtml()" in dashboard
    assert "rankCard('Career Rank', career, 'Permanent')" in dashboard


def test_community_v2_has_weekly_real_activity_pulse():
    assert "function communityWeeklyPulseHtml(league,team)" in APP
    assert "communityRows||[]" in APP
    assert "dailyRivalRows('week')" in APP
    community = APP.split("function renderCommunityScreen()", 1)[1].split("function switchCommunityLeague", 1)[0]
    assert "communityWeeklyPulseHtml(league, team)" in community
    assert ".community-weekly-pulse" in CSS


def test_recommendation_v2_explains_personalized_reasons():
    assert "Because '+weak.category+' is a weak spot" in APP
    assert "Because you follow '+fav.name" in APP
    assert "New format for you" in APP
    assert "Picked from your play history" in APP


def test_reward_overhaul_adds_rarity_and_team_dna_achievements():
    assert "teamCommunityRegular" in APP
    assert "balancedBallKnower" in APP
    assert "dnaEliteTrait" in APP
    assert "seasonGrinder" in APP
    assert "function achievementRarity(b)" in APP
    assert "'Legendary'" in APP
    assert "'Epic'" in APP


def test_share_v2_adds_real_identity_context():
    share = APP.split("function shareResultCard(mode)", 1)[1].split("var shareTriggerEl", 1)[0]
    assert "footballDNAData()" in share
    assert "progressionRankFor" in share
    assert "getStreak()" in share
    assert "dna.archetype" in share


def test_personalized_home_2_changes_primary_action_after_daily():
    home = APP.split("function renderHome() {", 1)[1].split("/* ============================== NFL/CFB mode picker", 1)[0]
    assert "personalized-home-2" in home
    assert "dailyDone&&homeRec" in home
    assert "View My Football DNA" in home
    assert "footballDNAHtml(true)" in home
