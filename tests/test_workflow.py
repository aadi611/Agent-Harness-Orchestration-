from harness.workflow import load_workflow


def test_example_workflow_loads():
    wf = load_workflow("workflows/market_research_report.yaml")
    assert wf.workflow == "market_research_report"
    assert wf.budget.max_replans == 2
    assert "reviewer" in wf.edges
