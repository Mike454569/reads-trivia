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


def test_creator_guided_builder_is_wired_to_real_feasibility_flow():
    assert "function creatorGuidedPrompt()" in CREATOR
    assert "function creatorGuidedBuild()" in CREATOR
    assert "creatorCheckFeasibility(s.requestText)" in CREATOR
    assert "creator-guided-card" in CREATOR
    assert 'data-creator-guided="league"' in CREATOR
    assert 'data-creator-guided="topic"' in CREATOR
    assert 'data-creator-guided="difficulty"' in CREATOR
    assert 'data-creator-guided="count"' in CREATOR
    assert "creatorSetGuided(e.target.dataset.creatorGuided, e.target.value)" in APP


def test_creator_player_preview_reuses_real_player_renderers():
    assert "function creatorDirectPlayerPreviewHtml(rg)" in CREATOR
    assert "renderMechanicPilotBody" in CREATOR
    assert "renderEnginePilotPromptHtml" in CREATOR
    assert 'data-creator-preview-mode="player"' in CREATOR
    assert 'data-creator-preview-mode="admin"' in CREATOR
    assert ".creator-player-preview" in CSS


def test_creator_question_edits_create_new_immutable_versions():
    models = (ROOT / "gateway" / "models.py").read_text(encoding="utf-8")
    service = (ROOT / "gateway" / "services" / "creator.py").read_text(encoding="utf-8")
    packages = (ROOT / "gateway" / "services" / "packages.py").read_text(encoding="utf-8")
    gateway = (ROOT / "gateway" / "app.py").read_text(encoding="utf-8")
    assert "class CreatorQuestionRevisionRequest" in models
    assert "def create_question_revision(package_id: str, question_index: int, replacement: dict)" in packages
    assert 'revised["revision_of"] = package_id' in packages
    assert 'return save_package(revised)' in packages
    assert "def revise_question(" in service
    assert '@app.post("/v1/creator/question/revise")' in gateway
    assert "creatorSaveQuestionRevision" in CREATOR
    assert "Save as New Version" in CREATOR
    assert "The original package stays untouched" in CREATOR


def test_creator_regenerate_creates_fresh_version_instead_of_mutating():
    assert "function creatorRegeneratePackage()" in CREATOR
    assert "creator-refresh-" in CREATOR
    assert "Regenerate Fresh Version" in CREATOR


def test_creator_recent_creations_and_clone_workflow_are_wired():
    assert "function creatorLoadRecent()" in CREATOR
    assert "function creatorOpenPackage(packageId)" in CREATOR
    assert "function creatorClonePackage(packageId)" in CREATOR
    assert "function creatorRecentHtml()" in CREATOR
    assert 'data-creator-open-package' in CREATOR
    assert 'data-creator-clone-package' in CREATOR
    assert "creatorLoadRecent();" in APP
    assert ".creator-recent-grid" in CSS


def test_creator_bulk_factory_runs_sequential_real_generation_requests():
    assert "function creatorBulkGenerate()" in CREATOR
    assert "chain=chain.then" in CREATOR
    assert "'/v1/creator/generate'" in CREATOR
    assert "bulkCount" in CREATOR
    assert "bulkResults" in CREATOR
    assert "Generate Content Pack" in CREATOR
    assert "creatorBulkSet(e.target.dataset.creatorBulk, e.target.value)" in APP
    assert ".creator-bulk-card" in CSS


def test_creator_bootstrap_uses_canonical_state_initializer():
    assert "state.creator = creatorInitialState();" in APP


def test_creator_saved_recipes_are_local_and_reusable():
    assert "var CREATOR_RECIPES_KEY='reads_creator_recipes_v1'" in CREATOR
    assert "function creatorSaveRecipe()" in CREATOR
    assert "function creatorRunRecipe(id)" in CREATOR
    assert "function creatorDeleteRecipe(id)" in CREATOR
    assert "localStorage.setItem(CREATOR_RECIPES_KEY" in CREATOR
    assert "creatorRecipesHtml()" in CREATOR
    assert 'data-creator-save-recipe' in CREATOR
    assert 'data-creator-run-recipe' in CREATOR


def test_creator_quality_scorecard_uses_real_package_fields():
    assert "function creatorQualityScorecardHtml(p)" in CREATOR
    assert "p.qa_status==='PASSED'" in CREATOR
    assert "p.question_count||p.puzzle_count" in CREATOR
    assert "p.review_status" in CREATOR
    assert "p.requested_description" in CREATOR
    assert "p.package_id" in CREATOR
    assert ".creator-quality-grid" in CSS


def test_creator_review_queue_has_search_filter_and_sort():
    assert "queueSearch" in CREATOR
    assert "queueLeague" in CREATOR
    assert "queueSort" in CREATOR
    assert "function creatorQueueRows()" in CREATOR
    assert "function creatorQueueControlsHtml()" in CREATOR
    assert 'id="creator-queue-search"' in CREATOR
    assert "data-creator-queue-league" in CREATOR
    assert "data-creator-queue-sort" in CREATOR
    assert "state.creator.queueSearch = e.target.value" in APP
    assert "state.creator.queueLeague = e.target.value" in APP
    assert "state.creator.queueSort = e.target.value" in APP


def test_creator_duplicate_intelligence_is_real_and_actionable():
    packages = (ROOT / "gateway" / "services" / "packages.py").read_text(encoding="utf-8")
    service = (ROOT / "gateway" / "services" / "creator.py").read_text(encoding="utf-8")
    gateway = (ROOT / "gateway" / "app.py").read_text(encoding="utf-8")
    assert "def analyze_creator_duplicates(package_id: str" in packages
    assert "duplicate_risk" in packages
    assert "similarity" in packages
    assert "def analyze_duplicates(package_id: str)" in service
    assert '@app.get("/v1/creator/duplicates/{package_id}")' in gateway
    assert "function creatorLoadDuplicateReport(packageId)" in CREATOR
    assert "creatorDuplicateReportHtml" in CREATOR
    assert "data-creator-check-duplicates" in CREATOR


def test_creator_can_replace_one_question_without_mutating_original():
    assert "function creatorReplaceQuestion(index)" in CREATOR
    assert "creator-slot-" in CREATOR
    assert "'/v1/creator/generate'" in CREATOR
    assert "'/v1/creator/question/revise'" in CREATOR
    assert "data-creator-replace-question" in CREATOR
    assert "creatorReplaceQuestion(parseInt(t.dataset.creatorReplaceQuestion" in APP


def test_creator_batch_review_supports_multi_select_approve_and_reject():
    assert "selectedPackages" in CREATOR
    assert "function creatorTogglePackageSelection(packageId)" in CREATOR
    assert "function creatorSelectVisiblePackages()" in CREATOR
    assert "function creatorBatchReview(status)" in CREATOR
    assert "Approve Selected" in CREATOR
    assert "Reject Selected" in CREATOR
    assert "data-creator-batch-review" in CREATOR
    assert "creatorBatchReview(t.dataset.creatorBatchReview)" in APP
    assert ".creator-batch-bar" in CSS


def test_creator_direct_route_loads_saved_recipes_and_recent_creations():
    assert "creatorLoadRecipes(); creatorLoadRecent();" in APP


def test_creator_command_center_wave_is_wired():
    assert "function creatorDashboardHtml()" in CREATOR
    assert "Open Smart Review Queue" in CREATOR
    assert "function creatorQuestionQaFlags(g)" in CREATOR
    assert "function creatorFixFlaggedQuestions()" in CREATOR
    assert "Fix Flagged Questions" in CREATOR
    assert "function creatorCollectionsHtml()" in CREATOR
    assert "CREATOR_COLLECTIONS_KEY" in CREATOR
    assert "function creatorPreviewMatrixHtml()" in CREATOR
    assert "Daily Reads" in CREATOR
    assert "Homepage Card" in CREATOR
    assert "function creatorPublishReadinessHtml(g)" in CREATOR
    assert "PUBLISH READINESS" in CREATOR
    assert "function creatorVersionHistoryHtml(g)" in CREATOR
    assert "data-creator-restore-version" in CREATOR
    assert "Smart Priority" in CREATOR
    assert "revision_of" in (ROOT / "gateway" / "services" / "packages.py").read_text(encoding="utf-8")
    assert "data-creator-dashboard-filter" in APP
    assert "data-creator-fix-issues" in APP
    assert "data-creator-preview-surface" in APP
    assert ".creator-command-center" in CSS


def test_creator_bulk_factory_v2_supports_25_and_quality_buckets():
    assert "[5,10,15,20,25]" in CREATOR
    assert "Math.min(25" in CREATOR
    assert "passed · " in CREATOR
    assert "needs review · " in CREATOR
    assert "failed · " in CREATOR


def test_creator_search_covers_package_status_dates_and_lineage():
    assert "p.package_id" in CREATOR
    assert "p.review_status" in CREATOR
    assert "p.gateway_stored_at" in CREATOR
    assert "p.reviewed_at" in CREATOR
    assert "p.revision_of" in CREATOR
