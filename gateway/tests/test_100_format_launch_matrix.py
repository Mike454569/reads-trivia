from tools.director_v02.format_launch_matrix import validate_format_launch_matrix


def test_all_100_distinct_formats_have_real_launch_targets_and_ui_proof():
    result = validate_format_launch_matrix()
    assert result["distinct_format_count"] == 100
    assert result["resolved_launch_count"] == 100, result["unresolved"]
    assert result["ui_proven_count"] == 100, result["missing_ui_proof"]
    assert result["mobile_unverified"] == []
