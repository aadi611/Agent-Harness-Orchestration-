from harness.budget import Budget


def test_budget_trips_on_usd():
    b = Budget(max_usd=1.0)
    assert b.ok()
    b.charge(usd=1.0)
    assert not b.ok()


def test_budget_trips_on_replans():
    b = Budget(max_replans=1)
    b.record_replan()
    assert b.ok()
    b.record_replan()
    assert not b.ok()
