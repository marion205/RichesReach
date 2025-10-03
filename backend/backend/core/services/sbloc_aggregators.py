# core/services/sbloc_aggregators.py
import uuid
from dataclasses import dataclass
from typing import Protocol, Optional

@dataclass
class AggregatorSession:
    external_session_id: str
    application_url: str

class SblocAggregator(Protocol):
    def create_session(self, *, bank_name: str, amount_usd: int, user_id: Optional[int]) -> AggregatorSession: ...

class MockSblocAggregator:
    """
    Fake aggregator that returns a hosted URL and an external_session_id.
    Pair this with the status cycler below to simulate real-time updates.
    """
    base_url = "https://mock-sbloc.richesreach.net/apply"

    def create_session(self, *, bank_name: str, amount_usd: int, user_id: Optional[int]) -> AggregatorSession:
        ext = str(uuid.uuid4())
        # make it look legit:
        url = f"{self.base_url}/{bank_name.lower().replace(' ', '-')}/{ext}?amount={amount_usd}"
        return AggregatorSession(external_session_id=ext, application_url=url)
