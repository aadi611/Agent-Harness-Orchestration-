from harness.router import Action, LoopDetector, Verdict, VerdictKind, route


def test_routes():
    assert route(Verdict(kind=VerdictKind.PASS)) is Action.ACCEPT
    assert route(Verdict(kind=VerdictKind.TOOL_ERROR)) is Action.RETRY_STEP
    assert route(Verdict(kind=VerdictKind.BAD_OUTPUT)) is Action.RERUN_STEP
    assert route(Verdict(kind=VerdictKind.BAD_PLAN)) is Action.REPLAN_SUBTREE
    assert route(Verdict(kind=VerdictKind.BUDGET_EXHAUSTED)) is Action.ESCALATE


def test_loop_detected_on_second_identical_failure():
    ld = LoopDetector()
    assert ld.check("s1", {"q": 1}, "timeout") is False
    assert ld.check("s1", {"q": 1}, "timeout") is True
    assert ld.check("s1", {"q": 2}, "timeout") is False
