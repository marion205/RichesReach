# richesreach/schema.py
import graphene
from core.types import AIScanType, PlaybookType, AIScanFilters
# from marketdata.schema import MarketDataQuery, MarketDataMutation

class Query(graphene.ObjectType):
    # AI Scans and Playbooks
    aiScans = graphene.List(AIScanType, filters=graphene.Argument(AIScanFilters, required=False))
    playbooks = graphene.List(PlaybookType)
    
    def resolve_aiScans(self, info, filters=None):
        """Resolve AI Scans with optional filters - return mock data"""
        print("🔍 DEBUG: resolve_aiScans called in main schema")
        # Return mock data directly for now
        mock_scans = [
            {
                "id": "scan_1",
                "name": "Momentum Breakout Scanner",
                "description": "Identifies stocks breaking out of consolidation patterns with strong volume",
                "category": "TECHNICAL",
                "riskLevel": "MEDIUM",
                "timeHorizon": "SHORT_TERM",
                "isActive": True,
                "lastRun": "2024-01-15T10:30:00Z",
                "results": [],
                "playbook": None
            },
            {
                "id": "scan_2",
                "name": "Value Opportunity Finder",
                "description": "Discovers undervalued stocks with strong fundamentals",
                "category": "FUNDAMENTAL",
                "riskLevel": "LOW",
                "timeHorizon": "LONG_TERM",
                "isActive": True,
                "lastRun": "2024-01-15T09:15:00Z",
                "results": [],
                "playbook": None
            }
        ]
        print(f"🔍 DEBUG: Returning {len(mock_scans)} scans from main schema")
        return mock_scans

    def resolve_playbooks(self, info):
        """Resolve available playbooks - return mock data"""
        print("🔍 DEBUG: resolve_playbooks called in main schema")
        # Return mock data directly for now
        return [
            {
                "id": "playbook_1",
                "name": "Momentum Strategy",
                "author": "AI System",
                "riskLevel": "MEDIUM",
                "performance": {
                    "successRate": 0.75,
                    "averageReturn": 0.12
                },
                "tags": ["momentum", "short-term", "technical"]
            },
            {
                "id": "playbook_2", 
                "name": "Value Hunter",
                "author": "AI System",
                "riskLevel": "LOW",
                "performance": {
                    "successRate": 0.68,
                    "averageReturn": 0.08
                },
                "tags": ["value", "long-term", "fundamental"]
            },
            {
                "id": "playbook_3",
                "name": "Growth Accelerator",
                "author": "AI System",
                "riskLevel": "HIGH",
                "performance": {
                    "successRate": 0.82,
                    "averageReturn": 0.18
                },
                "tags": ["growth", "medium-term", "fundamental"]
            }
        ]

# Import the complete Mutation class from core.schema
from core.schema import Mutation
from core.alpaca_mutations import AlpacaMutation, AlpacaQuery
from core.alpaca_crypto_mutations import AlpacaCryptoMutation, AlpacaCryptoQuery
from core.kyc_mutations import KYCMutation, KYCQuery

# Combine all mutations and queries
class CombinedQuery(Query, AlpacaQuery, AlpacaCryptoQuery, KYCQuery):
    pass

class CombinedMutation(Mutation, AlpacaMutation, AlpacaCryptoMutation, KYCMutation):
    pass

schema = graphene.Schema(query=CombinedQuery, mutation=CombinedMutation)