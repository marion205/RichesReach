"""
GraphQL Queries for Advanced Blockchain Features
NFTs, DAO Governance, Yield Aggregators
"""
import graphene
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# NFT Education & Enrichment Types
# ---------------------------------------------------------------------------

class GlossaryTermType(graphene.ObjectType):
    """A single glossary term with plain-English explanation"""
    term = graphene.String()
    definition = graphene.String()


class NFTEducationContentType(graphene.ObjectType):
    """
    Rich education content for a single NFT.
    Generated from collection packs (demo) or dynamically enriched (live wallets).
    """
    story = graphene.String()           # 2-4 sentence history/lore
    rarity_summary = graphene.String()  # Plain-English trait rarity explainer
    lesson = graphene.String()          # 1-sentence blockchain concept tied to this NFT
    glossary = graphene.List(GlossaryTermType)  # Tap-to-expand terms
    confidence = graphene.Float()       # 0-1, how rich the content is
    source = graphene.String()          # "demo" | "cached_collection" | "generic"


class UtilityLinkType(graphene.ObjectType):
    """Official link associated with an NFT's utility"""
    label = graphene.String()
    url = graphene.String()


class NFTUtilityType(graphene.ObjectType):
    """Real-world perks and official links for an NFT"""
    perks = graphene.List(graphene.String)
    official_links = graphene.List(UtilityLinkType)


class NFTRiskType(graphene.ObjectType):
    """Risk assessment for an NFT contract"""
    level = graphene.String()               # LOW | MED | HIGH
    reasons = graphene.List(graphene.String)
    recommended_action = graphene.String()


# ---------------------------------------------------------------------------
# Core NFT Type (extended)
# ---------------------------------------------------------------------------

class NFTType(graphene.ObjectType):
    """GraphQL type for NFT — extended with education, utility, and risk"""
    id = graphene.String()
    tokenId = graphene.String()
    contractAddress = graphene.String()
    name = graphene.String()
    description = graphene.String()
    imageUrl = graphene.String()
    collectionName = graphene.String()
    chain = graphene.String()
    attributes = graphene.List(graphene.JSONString)
    floorPrice = graphene.Float()
    lastSalePrice = graphene.Float()
    # New enrichment fields
    education_content = graphene.Field(NFTEducationContentType)
    utility_data = graphene.Field(NFTUtilityType)
    risk = graphene.Field(NFTRiskType)


# ---------------------------------------------------------------------------
# Collection education packs — rich demo content, zero API calls needed
# ---------------------------------------------------------------------------

COLLECTION_EDUCATION_PACKS = {
    "0xbc4ca0eda7647a8ab7c2061c2e118a18a936f13d": {  # BAYC
        "story": (
            "Bored Ape Yacht Club launched in April 2021 with 10,000 hand-drawn apes "
            "and became the defining 'profile picture' (PFP) collection of the NFT era. "
            "Ownership grants access to the Yacht Club — real events, exclusive merch, "
            "and governance rights over the ApeCoin DAO. It proved NFTs could be more "
            "than art: they became membership keys to a community."
        ),
        "rarity_summary": (
            "BAYC traits like gold fur, laser eyes, or solid gold backgrounds appear in "
            "less than 1% of the collection. Rarity is determined by combining all trait "
            "frequencies — rarer combinations command significant premiums on secondary markets."
        ),
        "lesson": (
            "Your Bored Ape is an ERC-721 token: a unique entry in Ethereum's permanent "
            "ledger that no company — not even Yuga Labs — can delete, freeze, or reassign "
            "without your private key. That immutability is what 'true ownership' means on-chain."
        ),
        "glossary": [
            {"term": "ERC-721", "definition": "The Ethereum standard for non-fungible tokens — each token is unique, unlike ERC-20 coins which are interchangeable."},
            {"term": "Floor price", "definition": "The lowest asking price in a collection. It's the cost to enter the club, not the value of your specific ape."},
            {"term": "ApeCoin (APE)", "definition": "A governance token given to BAYC/MAYC holders. Owning APE lets you vote on how the ApeCoin DAO spends its treasury."},
        ],
        "perks": [
            "Access to the Bored Ape Yacht Club private Discord",
            "ApeCoin (APE) governance rights via the ApeCoin DAO",
            "Exclusive IRL events — ApeFest and invite-only gatherings",
            "Commercial IP rights to use your ape's image",
            "Eligibility for future Yuga Labs airdrops and land in Otherside metaverse",
        ],
        "official_links": [
            {"label": "Yuga Labs", "url": "https://yuga.com"},
            {"label": "ApeCoin DAO", "url": "https://apecoin.com"},
            {"label": "Otherside", "url": "https://otherside.xyz"},
        ],
        "risk_level": "LOW",
        "risk_reasons": ["Contract verified on Etherscan", "Top-5 collection by volume", "Active development team"],
    },
    "0xb47e3cd837ddf8e4c57f05d70ab865de6e193bbb": {  # CryptoPunks
        "story": (
            "CryptoPunks were created by Larva Labs in June 2017 — before the ERC-721 "
            "standard even existed. The 10,000 pixel-art characters were given away free "
            "and inspired the entire NFT movement. Acquired by Yuga Labs in 2022, Punks "
            "are widely considered the 'original blue-chip' NFT and cultural artifacts of "
            "early crypto history."
        ),
        "rarity_summary": (
            "Only 88 Zombies, 24 Apes, and 9 Aliens exist among the 10,000 Punks — "
            "making them the rarest types. Attribute count also matters: a Punk with 0 "
            "or 7 attributes is rarer than average. Aliens with minimal attributes have "
            "sold for thousands of ETH."
        ),
        "lesson": (
            "CryptoPunks predate ERC-721 and use a custom on-chain marketplace contract "
            "from 2017 that's still operating today. This is blockchain permanence in action: "
            "code deployed years ago continues to run without any company maintaining it."
        ),
        "glossary": [
            {"term": "On-chain metadata", "definition": "The NFT's image and traits stored directly on the blockchain — unlike most NFTs where images sit on external servers that could go offline."},
            {"term": "Blue-chip NFT", "definition": "A collection with a long track record, high liquidity, and broad recognition — analogous to blue-chip stocks."},
            {"term": "Provenance", "definition": "The verifiable history of ownership for an NFT, recorded permanently on-chain from its first mint to today."},
        ],
        "perks": [
            "CryptoPunks holder commercial IP rights (granted by Yuga Labs, 2022)",
            "Cultural status as one of the earliest NFT artifacts",
            "On-chain marketplace — buy, sell, and bid directly via the contract",
        ],
        "official_links": [
            {"label": "CryptoPunks", "url": "https://cryptopunks.app"},
            {"label": "Larva Labs", "url": "https://larvalabs.com"},
        ],
        "risk_level": "LOW",
        "risk_reasons": ["Contract verified", "8+ years of on-chain history", "Acquired by Yuga Labs"],
    },
    "0x60e4d786628fea6478f785a6d7e704777c86a7c6": {  # MAYC
        "story": (
            "Mutant Ape Yacht Club launched in August 2021 as a companion to BAYC. "
            "Existing BAYC holders received 'mutant serum' to transform their apes; "
            "another 20,000 were sold publicly. MAYC gave the broader community a path "
            "into the Yuga ecosystem at a lower price point while maintaining many of "
            "the same membership benefits."
        ),
        "rarity_summary": (
            "M3 Mega Mutant serums — which created the rarest MAYC — were only held "
            "by a handful of BAYC owners. Serums were tiered (M1, M2, M3), so a Mutant "
            "Ape's origin serum directly impacts its rarity tier and market value."
        ),
        "lesson": (
            "Airdrops — like the mutant serum sent to BAYC holders — are one of the most "
            "powerful Web3 loyalty tools. Projects reward early or existing holders with "
            "new tokens or NFTs, creating value for the community without a traditional sale."
        ),
        "glossary": [
            {"term": "Airdrop", "definition": "Free tokens or NFTs sent directly to wallet addresses, usually as a reward for holding another asset or being an early adopter."},
            {"term": "Companion collection", "definition": "A secondary NFT collection tied to an existing one, expanding the ecosystem while offering a lower entry price."},
        ],
        "perks": [
            "Access to MAYC holder Discord channels",
            "Eligibility for Yuga Labs ecosystem events",
            "Commercial IP rights to your Mutant Ape's image",
            "Otherside metaverse access",
        ],
        "official_links": [
            {"label": "Yuga Labs", "url": "https://yuga.com"},
        ],
        "risk_level": "LOW",
        "risk_reasons": ["Contract verified", "Yuga Labs ecosystem", "High trading volume"],
    },
    "0x49cf6f5d44e70224e2e23fdcdd2c053f30ada28b": {  # CloneX
        "story": (
            "CloneX launched in December 2021 as a collaboration between RTFKT Studio "
            "and Nike — making it one of the first major NFT collections from a global "
            "sportswear brand. The 20,000 avatars are designed as next-generation digital "
            "identities, with physical Nike sneaker claims and metaverse utility built in "
            "from launch."
        ),
        "rarity_summary": (
            "CloneX has 8 DNA types: Human, Robot, Undead, Alien, Angel, Demon, and two "
            "rare variants. Non-Human DNA types are significantly rarer and command premiums. "
            "File type (3D vs 2D) and specific drip traits further differentiate value."
        ),
        "lesson": (
            "CloneX demonstrates how traditional brands are entering Web3: Nike acquired "
            "RTFKT to own the IP and the on-chain relationship with customers. NFT ownership "
            "can unlock physical products — bridging digital tokens with real-world goods."
        ),
        "glossary": [
            {"term": "Physical redemption", "definition": "When an NFT holder can claim a real-world item (shoes, merch, tickets) by 'burning' or proving ownership of their token."},
            {"term": "Digital identity", "definition": "Using an NFT as your avatar or profile picture across platforms — asserting ownership of your online persona."},
        ],
        "perks": [
            "Nike x RTFKT physical sneaker claim eligibility",
            "Access to RTFKT creator drops and forging events",
            "CloneX metaverse avatar across supported platforms",
            "Early access to future RTFKT collections",
        ],
        "official_links": [
            {"label": "RTFKT", "url": "https://rtfkt.com"},
            {"label": "Nike NFT", "url": "https://www.nike.com/nft"},
        ],
        "risk_level": "LOW",
        "risk_reasons": ["Nike-backed (RTFKT acquired 2021)", "Contract verified", "Active product roadmap"],
    },
    "0x8a90cab2b38dba80c64b7734e58ee1db38b8992e": {  # Doodles
        "story": (
            "Doodles launched in October 2021 with 10,000 hand-drawn characters by "
            "illustrator Burnt Toast. Beyond art, Doodles established a community treasury "
            "funded by royalties, governed by holders. Pharrell Williams joined as Chief "
            "Brand Officer in 2022, and the project expanded into music, animation, and "
            "physical consumer products — evolving from a PFP into a media brand."
        ),
        "rarity_summary": (
            "Rare traits include Rainbow backgrounds (under 1%), Alien heads, and Gold "
            "outfits. Doodles uses a Points system where rarer traits score higher — "
            "the total score determines a Doodle's rarity rank within the collection."
        ),
        "lesson": (
            "Doodles pioneered the 'community treasury' model: a percentage of secondary "
            "sale royalties flows into a shared pool that NFT holders vote on how to spend. "
            "This is decentralized governance in action — your NFT is also a voting share."
        ),
        "glossary": [
            {"term": "Royalties", "definition": "A percentage (usually 5-10%) paid to the original creator every time their NFT is resold on secondary markets."},
            {"term": "Community treasury", "definition": "A shared pool of funds, often from royalties, that NFT holders govern collectively via on-chain or off-chain voting."},
            {"term": "PFP (Profile Picture)", "definition": "An NFT used as a social media avatar. PFP collections often double as membership passes to communities."},
        ],
        "perks": [
            "Doodles community treasury governance rights",
            "Access to exclusive Doodles events and activations",
            "Early access to Doodles2 and extended universe drops",
            "Physical and digital consumer products from the Doodles brand",
        ],
        "official_links": [
            {"label": "Doodles", "url": "https://doodles.app"},
        ],
        "risk_level": "LOW",
        "risk_reasons": ["Contract verified", "Pharrell Williams partnership", "Active community treasury"],
    },
    "0x1a92f7381b9f03921564a437210bb9396471050c": {  # Cool Cats
        "story": (
            "Cool Cats launched in July 2021 with 9,999 randomly generated cats. "
            "An early standout of the PFP era, Cool Cats built a strong community "
            "through frequent holder benefits and a clear brand identity. The collection "
            "expanded with Cool Pets — companion NFTs — and has focused on storytelling "
            "and animation to build a long-term IP."
        ),
        "rarity_summary": (
            "Cool Cats are scored on a tier system: Cool (3-4 pts), Extra Cool (5 pts), "
            "Super Cool (6 pts), and Beyond Cool (7+ pts). Higher point totals indicate "
            "rarer trait combinations. Wild backgrounds and unique outfits significantly "
            "boost a Cat's rarity score."
        ),
        "lesson": (
            "Cool Cats is an example of how NFT projects build 'lore' — a narrative "
            "universe that gives holders emotional attachment beyond the art. Storytelling "
            "increases long-term retention and can expand a collection's IP value over time."
        ),
        "glossary": [
            {"term": "NFT lore", "definition": "The backstory, world-building, and narrative that a project builds around its collection to deepen community engagement."},
            {"term": "Companion NFT", "definition": "A secondary collection designed to pair with a primary one — like Cool Pets for Cool Cats — extending the ecosystem."},
        ],
        "perks": [
            "Cool Cats holder Discord access",
            "Eligibility for Cool Pets companion NFT benefits",
            "Exclusive holder merchandise and event access",
            "Voting rights on community initiatives",
        ],
        "official_links": [
            {"label": "Cool Cats", "url": "https://coolcatsnft.com"},
        ],
        "risk_level": "LOW",
        "risk_reasons": ["Contract verified on Etherscan", "Active since July 2021", "Established community"],
    },
}

GENERIC_EDUCATION_CONTENT = {
    "story": (
        "This NFT lives as a unique token on the blockchain. Unlike a JPEG you can "
        "copy-paste, the token itself — and its verifiable ownership history — cannot "
        "be duplicated. Every transfer, sale, and interaction is recorded permanently."
    ),
    "rarity_summary": (
        "NFT rarity is determined by trait frequency: how often each attribute appears "
        "across the whole collection. Rarer trait combinations typically command higher "
        "prices, though market demand ultimately drives value."
    ),
    "lesson": (
        "Every NFT transaction is settled on-chain in minutes with full transparency — "
        "no bank, no clearinghouse, no three-day settlement window. This is the core "
        "promise of blockchain: permissionless, trustless, instant ownership transfer."
    ),
    "glossary": [
        {"term": "NFT", "definition": "Non-Fungible Token — a unique digital asset on a blockchain. Unlike Bitcoin, no two NFTs are identical."},
        {"term": "Mint", "definition": "The process of creating an NFT on the blockchain for the first time. Like pressing the first copy of a coin."},
        {"term": "Gas fee", "definition": "A small payment to blockchain validators who process and confirm your transaction. Higher demand = higher gas."},
        {"term": "Smart contract", "definition": "Self-executing code on the blockchain that powers NFTs — automatically enforcing rules like royalties and transfers without a middleman."},
    ],
}


def _get_education_pack(contract_address: str) -> Optional[dict]:
    """Return education pack for a given contract, or None."""
    return COLLECTION_EDUCATION_PACKS.get(contract_address.lower())


def _score_nft_risk(contract_address: str, chain: str) -> dict:
    """
    Lightweight risk scoring for an NFT contract.
    Production: check Etherscan verification, trading volume, metadata hosting.
    """
    pack = _get_education_pack(contract_address)
    if pack:
        return {
            "level": pack.get("risk_level", "LOW"),
            "reasons": pack.get("risk_reasons", ["Contract verified"]),
            "recommended_action": "No action needed — this is a well-established collection.",
        }
    return {
        "level": "MED",
        "reasons": [
            "Contract not in our verified collection list",
            "We couldn't confirm on-chain trading history",
        ],
        "recommended_action": (
            "Verify this contract on Etherscan before connecting it to any sites. "
            "Never sign transactions from unknown sources."
        ),
    }


def _build_nft_type(nft_data: dict) -> 'NFTType':
    """Enrich a raw NFT dict with education, utility, and risk data."""
    contract = (nft_data.get("contractAddress") or "").lower()
    chain = nft_data.get("chain", "ethereum")
    pack = _get_education_pack(contract)

    if pack:
        glossary = [GlossaryTermType(term=g["term"], definition=g["definition"]) for g in pack.get("glossary", [])]
        education = NFTEducationContentType(
            story=pack["story"],
            rarity_summary=pack["rarity_summary"],
            lesson=pack["lesson"],
            glossary=glossary,
            confidence=0.95,
            source="cached_collection",
        )
        utility = NFTUtilityType(
            perks=pack.get("perks", []),
            official_links=[
                UtilityLinkType(label=lnk["label"], url=lnk["url"])
                for lnk in pack.get("official_links", [])
            ],
        )
    else:
        glossary = [GlossaryTermType(term=g["term"], definition=g["definition"]) for g in GENERIC_EDUCATION_CONTENT["glossary"]]
        education = NFTEducationContentType(
            story=GENERIC_EDUCATION_CONTENT["story"],
            rarity_summary=GENERIC_EDUCATION_CONTENT["rarity_summary"],
            lesson=GENERIC_EDUCATION_CONTENT["lesson"],
            glossary=glossary,
            confidence=0.5,
            source="generic",
        )
        utility = NFTUtilityType(perks=[], official_links=[])

    risk_data = _score_nft_risk(contract, chain)
    risk = NFTRiskType(
        level=risk_data["level"],
        reasons=risk_data["reasons"],
        recommended_action=risk_data["recommended_action"],
    )

    return NFTType(
        id=nft_data.get("id", ""),
        tokenId=nft_data.get("tokenId", ""),
        contractAddress=nft_data.get("contractAddress", ""),
        name=nft_data.get("name", ""),
        description=nft_data.get("description", ""),
        imageUrl=nft_data.get("imageUrl", ""),
        collectionName=nft_data.get("collectionName", ""),
        chain=nft_data.get("chain", "ethereum"),
        attributes=nft_data.get("attributes", []),
        floorPrice=nft_data.get("floorPrice"),
        lastSalePrice=nft_data.get("lastSalePrice"),
        education_content=education,
        utility_data=utility,
        risk=risk,
    )


# Demo NFTs — mirrors the frontend DEMO_NFTS constant in NFTGallery.tsx
DEMO_NFTS_DATA = [
    {
        "id": "demo-1", "tokenId": "4201",
        "contractAddress": "0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D",
        "name": "Bored Ape #4201", "collectionName": "Bored Ape Yacht Club",
        "chain": "ethereum", "floorPrice": 14.29, "lastSalePrice": 16.5,
        "imageUrl": "https://ipfs.io/ipfs/QmRRPWG96cmgTn2qSzjwr2qvfNEuhunv6FNeMFGa9bx6mQ",
        "description": "A unique ape from the Bored Ape Yacht Club collection.",
    },
    {
        "id": "demo-2", "tokenId": "7804",
        "contractAddress": "0xb47e3cd837dDF8e4c57F05d70Ab865de6e193BBB",
        "name": "CryptoPunk #7804", "collectionName": "CryptoPunks",
        "chain": "ethereum", "floorPrice": 44.95, "lastSalePrice": 48.0,
        "imageUrl": "https://www.larvalabs.com/public/images/cryptopunks/punk7804.png",
        "description": "One of the original 10,000 CryptoPunks.",
    },
    {
        "id": "demo-3", "tokenId": "1337",
        "contractAddress": "0x60E4d786628Fea6478F785A6d7e704777c86a7c6",
        "name": "Mutant Ape #1337", "collectionName": "Mutant Ape Yacht Club",
        "chain": "ethereum", "floorPrice": 3.12, "lastSalePrice": 3.5,
        "imageUrl": "https://ipfs.io/ipfs/QmPbxeGcXhYQQNgsC6a36dDyYUcHgMLnGKnF8pVFmGsvqi",
        "description": "A mutant ape from the MAYC collection.",
    },
    {
        "id": "demo-4", "tokenId": "9921",
        "contractAddress": "0x49cF6f5d44E70224e2E23fDcdd2C053F30aDA28B",
        "name": "CloneX #9921", "collectionName": "CloneX",
        "chain": "ethereum", "floorPrice": 1.85, "lastSalePrice": 2.1,
        "imageUrl": "https://clonex-assets.rtfkt.com/images/9921.png",
        "description": "A next-gen avatar from RTFKT x Nike.",
    },
    {
        "id": "demo-5", "tokenId": "3820",
        "contractAddress": "0x8a90CAb2b38dba80c64b7734e58Ee1dB38B8992e",
        "name": "Doodle #3820", "collectionName": "Doodles",
        "chain": "ethereum", "floorPrice": 1.2, "lastSalePrice": 1.4,
        "imageUrl": "https://ipfs.io/ipfs/QmPMc4tcBsMqLRuCQtPmPe84bpSjrC3Ky7t3JWuHXYB4aS/3820.png",
        "description": "A hand-drawn doodle from the Doodles collection.",
    },
    {
        "id": "demo-6", "tokenId": "512",
        "contractAddress": "0x1A92f7381B9F03921564a437210bB9396471050C",
        "name": "Cool Cat #512", "collectionName": "Cool Cats",
        "chain": "polygon", "floorPrice": 0.18, "lastSalePrice": 0.22,
        "imageUrl": "https://ipfs.io/ipfs/QmTNBQDbggLZdKF1fRgWnXsnRikd52zL5ciNu769g9y9K7/512.png",
        "description": "A cool cat just chilling.",
    },
]


class GovernanceProposalType(graphene.ObjectType):
    """GraphQL type for governance proposal"""
    id = graphene.String()
    title = graphene.String()
    description = graphene.String()
    proposer = graphene.String()
    startBlock = graphene.Int()
    endBlock = graphene.Int()
    votesFor = graphene.Float()
    votesAgainst = graphene.Float()
    abstainVotes = graphene.Float()
    totalVotes = graphene.Float()
    quorum = graphene.Float()
    status = graphene.String()
    hasVoted = graphene.Boolean()
    userVote = graphene.String()
    actions = graphene.List(graphene.JSONString)


class UserVotingPowerType(graphene.ObjectType):
    """GraphQL type for user voting power"""
    votingPower = graphene.Float()
    delegatedTo = graphene.String()
    delegators = graphene.List(graphene.String)
    proposalsVoted = graphene.Int()


class YieldOpportunityType(graphene.ObjectType):
    """GraphQL type for yield opportunity"""
    protocol = graphene.String()
    asset = graphene.String()
    apy = graphene.Float()
    tvl = graphene.Float()
    risk = graphene.String()
    strategy = graphene.String()
    minDeposit = graphene.Float()
    chain = graphene.String()
    contractAddress = graphene.String()


class UserYieldPositionType(graphene.ObjectType):
    """GraphQL type for user yield position"""
    id = graphene.String()
    protocol = graphene.String()
    asset = graphene.String()
    amount = graphene.Float()
    apy = graphene.Float()
    earned = graphene.Float()
    chain = graphene.String()


class BlockchainQueries(graphene.ObjectType):
    """GraphQL queries for advanced blockchain features"""

    user_nfts = graphene.List(
        NFTType,
        address=graphene.String(required=True),
        chain=graphene.String(),
        description="Get user's NFTs with education, utility, and risk enrichment"
    )
    userNFTs = graphene.List(
        NFTType,
        address=graphene.String(required=True),
        chain=graphene.String(),
        description="Get user's NFTs (camelCase alias)"
    )

    governance_proposals = graphene.List(
        GovernanceProposalType,
        daoAddress=graphene.String(required=True),
        description="Get governance proposals for a DAO"
    )
    governanceProposals = graphene.List(
        GovernanceProposalType,
        daoAddress=graphene.String(required=True),
        description="Get governance proposals (camelCase alias)"
    )

    user_voting_power = graphene.Field(
        UserVotingPowerType,
        daoAddress=graphene.String(required=True),
        userAddress=graphene.String(required=True),
        description="Get user's voting power in a DAO"
    )
    userVotingPower = graphene.Field(
        UserVotingPowerType,
        daoAddress=graphene.String(required=True),
        userAddress=graphene.String(required=True),
        description="Get user's voting power (camelCase alias)"
    )

    yield_opportunities = graphene.List(
        YieldOpportunityType,
        chain=graphene.String(),
        asset=graphene.String(),
        description="Get available yield opportunities"
    )
    yieldOpportunities = graphene.List(
        YieldOpportunityType,
        chain=graphene.String(),
        asset=graphene.String(),
        description="Get available yield opportunities (camelCase alias)"
    )

    user_yield_positions = graphene.List(
        UserYieldPositionType,
        userAddress=graphene.String(required=True),
        description="Get user's yield positions"
    )
    userYieldPositions = graphene.List(
        UserYieldPositionType,
        userAddress=graphene.String(required=True),
        description="Get user's yield positions (camelCase alias)"
    )

    def resolve_user_nfts(self, info, address, chain=None):
        """
        Get user's NFTs enriched with education, utility, and risk data.
        Demo NFTs served for empty/unauthenticated wallets.
        Production: query Alchemy/OpenSea then enrich via _build_nft_type.
        """
        try:
            # TODO(production): replace with Alchemy getNFTsForOwner or OpenSea API
            # raw_nfts = alchemy_client.get_nfts_for_owner(address, chain)
            # return [_build_nft_type(n) for n in raw_nfts]
            filtered = [
                n for n in DEMO_NFTS_DATA
                if chain is None or n["chain"] == chain
            ]
            return [_build_nft_type(n) for n in filtered]
        except Exception as e:
            logger.error(f"Error fetching NFTs: {e}", exc_info=True)
            return []

    def resolve_userNFTs(self, info, address, chain=None):
        return self.resolve_user_nfts(info, address, chain)

    def resolve_governance_proposals(self, info, daoAddress):
        try:
            return []
        except Exception as e:
            logger.error(f"Error fetching governance proposals: {e}", exc_info=True)
            return []

    def resolve_governanceProposals(self, info, daoAddress):
        return self.resolve_governance_proposals(info, daoAddress)

    def resolve_user_voting_power(self, info, daoAddress, userAddress):
        try:
            return UserVotingPowerType(
                votingPower=0.0,
                delegatedTo=None,
                delegators=[],
                proposalsVoted=0
            )
        except Exception as e:
            logger.error(f"Error fetching voting power: {e}", exc_info=True)
            return UserVotingPowerType(votingPower=0.0, delegatedTo=None, delegators=[], proposalsVoted=0)

    def resolve_userVotingPower(self, info, daoAddress, userAddress):
        return self.resolve_user_voting_power(info, daoAddress, userAddress)

    def resolve_yield_opportunities(self, info, chain=None, asset=None):
        try:
            return []
        except Exception as e:
            logger.error(f"Error fetching yield opportunities: {e}", exc_info=True)
            return []

    def resolve_yieldOpportunities(self, info, chain=None, asset=None):
        return self.resolve_yield_opportunities(info, chain, asset)

    def resolve_user_yield_positions(self, info, userAddress):
        try:
            return []
        except Exception as e:
            logger.error(f"Error fetching yield positions: {e}", exc_info=True)
            return []

    def resolve_userYieldPositions(self, info, userAddress):
        return self.resolve_user_yield_positions(info, userAddress)
