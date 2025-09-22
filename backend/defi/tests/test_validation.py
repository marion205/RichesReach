from django.test import TestCase, override_settings
from django.urls import reverse
from unittest.mock import patch
from rest_framework.test import APIClient

class ValidationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch("defi.views.POOL")
    def test_borrow_blocked_when_hf_below_one(self, mock_pool):
        # hf just below 1e18 (i.e., < 1.0)
        mock_pool.functions.getUserAccountData.return_value.call.return_value = (
            0,  # total_collateral
            100,  # total_debt
            0,  # available_borrows
            0,  # clt
            0,  # ltv
            999_999_999_999_999_999  # hf
        )
        payload = {
            "type":"borrow",
            "wallet_address":"0x0000000000000000000000000000000000000001",
            "data":{"symbol":"USDC","amountHuman":"100","rateMode":2}
        }
        resp = self.client.post("/defi/validate-transaction/", payload, format="json")
        body = resp.json()
        assert resp.status_code == 200
        assert body["isValid"] is False
        assert "Health Factor" in body["reason"]

    @patch("defi.views.POOL")
    def test_borrow_allowed_when_hf_above_one(self, mock_pool):
        # hf above 1e18 (i.e., > 1.0)
        mock_pool.functions.getUserAccountData.return_value.call.return_value = (
            1000,  # total_collateral
            100,  # total_debt
            500,  # available_borrows
            8000,  # clt
            7000,  # ltv
            1_500_000_000_000_000_000  # hf = 1.5
        )
        payload = {
            "type":"borrow",
            "wallet_address":"0x0000000000000000000000000000000000000001",
            "data":{"symbol":"USDC","amountHuman":"100","rateMode":2}
        }
        resp = self.client.post("/defi/validate-transaction/", payload, format="json")
        body = resp.json()
        assert resp.status_code == 200
        assert body["isValid"] is True
        assert "riskData" in body

    def test_invalid_asset_rejected(self):
        payload = {
            "type":"borrow",
            "wallet_address":"0x0000000000000000000000000000000000000001",
            "data":{"symbol":"INVALID","amountHuman":"100","rateMode":2}
        }
        resp = self.client.post("/defi/validate-transaction/", payload, format="json")
        body = resp.json()
        assert resp.status_code == 200
        assert body["isValid"] is False
        assert "Asset not allowed" in str(body["reason"])

    def test_invalid_wallet_address_rejected(self):
        payload = {
            "type":"borrow",
            "wallet_address":"invalid_address",
            "data":{"symbol":"USDC","amountHuman":"100","rateMode":2}
        }
        resp = self.client.post("/defi/validate-transaction/", payload, format="json")
        body = resp.json()
        assert resp.status_code == 200
        assert body["isValid"] is False
        assert "wallet_address" in str(body["reason"])

    def test_negative_amount_rejected(self):
        payload = {
            "type":"deposit",
            "wallet_address":"0x0000000000000000000000000000000000000001",
            "data":{"symbol":"USDC","amountHuman":"-100"}
        }
        resp = self.client.post("/defi/validate-transaction/", payload, format="json")
        body = resp.json()
        assert resp.status_code == 200
        assert body["isValid"] is False
        assert "Amount must be > 0" in str(body["reason"])
