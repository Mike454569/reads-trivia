from gateway.services import game_state, packages


def test_strategy_arcade_wave_package_ids_are_allowed():
    for prefix in ("GGP39", "GGP40", "GGP41"):
        value = f"{prefix}:" + ("a" * 24)
        assert packages.PACKAGE_ID_RE.fullmatch(value), value
        assert game_state.STATE_ID_RE.fullmatch(value), value


def test_future_unassigned_prefix_is_still_rejected():
    value = "GGP42:" + ("a" * 24)
    assert packages.PACKAGE_ID_RE.fullmatch(value) is None
    assert game_state.STATE_ID_RE.fullmatch(value) is None
