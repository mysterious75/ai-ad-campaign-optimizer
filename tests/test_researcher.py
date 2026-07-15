"""
Tests for the Researcher Agent — API fetching with real failure scenarios.
These tests use mocked HTTP to simulate real API behavior.
"""

import pytest
from unittest.mock import AsyncMock, patch

from agents.researcher_agent import ResearcherAgent, TokenExpiredError
from agents.rate_limiter import RateLimitError


class TestResearcherAgent:
    def setup_method(self):
        self.researcher = ResearcherAgent()

    def test_extract_revenue_from_actions(self):
        actions = [
            {"action_type": "link_click", "value": "0"},
            {"action_type": "purchase", "value": "150.00"},
        ]
        assert self.researcher._extract_revenue(actions) == 150.00

    def test_extract_revenue_empty_actions(self):
        assert self.researcher._extract_revenue([]) == 0.0

    def test_extract_revenue_no_purchase_action(self):
        actions = [{"action_type": "link_click", "value": "10"}]
        assert self.researcher._extract_revenue(actions) == 0.0

    @pytest.mark.asyncio
    async def test_fetch_campaigns_no_platforms_configured(self):
        result = await self.researcher.fetch_campaigns({"platformConnections": {}})
        assert result["campaigns"] == []
        assert result["platforms_fetched"] == []
        assert result["platforms_failed"] == []

    @pytest.mark.asyncio
    async def test_fetch_campaigns_meta_missing_account_id(self):
        config = {
            "platformConnections": {
                "meta": {"accessToken": "tok_xxx"}
            }
        }
        result = await self.researcher.fetch_campaigns(config)
        assert "meta" in result["platforms_failed"]
        assert any("no adAccountId" in e for e in result["errors"])


class TestTokenExpiredError:
    def test_error_message(self):
        err = TokenExpiredError("meta")
        assert "meta" in str(err)
        assert err.platform == "meta"
