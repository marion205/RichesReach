from schema import schema

def test_ai_recs_fields():
    query = """{ aiRecommendations { schemaVersion portfolioAnalysis { expectedImpact { evPct } } } }"""
    res = schema.execute(query, context_value={"user":{"incomeProfile":{}, "liquidCashUSD":5000}})
    assert not res.errors
    assert "aiRecommendations" in res.data
    assert res.data["aiRecommendations"]["schemaVersion"] == "2025-01-01"
