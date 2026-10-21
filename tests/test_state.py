from harness.state import PlanDAG, Step


def _dag() -> PlanDAG:
    d = PlanDAG()
    d.add(Step(id="a", tool="search"))
    d.add(Step(id="b", tool="fetch", deps=["a"]))
    d.add(Step(id="c", tool="fetch", deps=["a"]))
    d.add(Step(id="d", tool="write", deps=["b", "c"]))
    return d


def test_frontier_advances_with_deps():
    d = _dag()
    assert [s.id for s in d.ready_steps()] == ["a"]
    d.mark_done("a")
    assert {s.id for s in d.ready_steps()} == {"b", "c"}


def test_subtree_includes_transitive_dependents():
    assert _dag().subtree("b") == {"b", "d"}


def test_done():
    d = _dag()
    for i in "abcd":
        d.mark_done(i)
    assert d.done
