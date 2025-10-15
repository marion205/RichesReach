import graphene
from django.conf import settings
from web3 import Web3
from .abis import AAVE_POOL_ABI

w3 = Web3(Web3.HTTPProvider(settings.RPC_URL))
pool = w3.eth.contract(address=Web3.to_checksum_address(settings.AAVE_POOL_ADDRESS), abi=AAVE_POOL_ABI)

class AAVEUserData(graphene.ObjectType):
    total_collateral_base = graphene.String()
    total_debt_base = graphene.String()
    available_borrows_base = graphene.String()
    ltv = graphene.Int()
    health_factor = graphene.String()

class Query(graphene.ObjectType):
    aave_user_data = graphene.Field(AAVEUserData, address=graphene.String(required=True))

    def resolve_aave_user_data(root, info, address):
        data = pool.functions.getUserAccountData(Web3.to_checksum_address(address)).call()
        return AAVEUserData(
            total_collateral_base=str(data[0]),
            total_debt_base=str(data[1]),
            available_borrows_base=str(data[2]),
            ltv=int(data[4]),
            health_factor=str(data[5]),
        )

schema = graphene.Schema(query=Query)
