import graphene

class SblocBankType(graphene.ObjectType):
    id = graphene.ID(required=True)
    name = graphene.String(required=True)
    logo_url = graphene.String()
    min_apr = graphene.Float()
    max_apr = graphene.Float()
    min_ltv = graphene.Float()
    max_ltv = graphene.Float()
    regions = graphene.List(graphene.String)
    min_loan_usd = graphene.Int()
    notes = graphene.String()

class SblocSessionType(graphene.ObjectType):
    id = graphene.ID(required=True)
    status = graphene.String(required=True)
    application_url = graphene.String(required=True)

class CreateSblocSessionResult(graphene.ObjectType):
    success = graphene.Boolean(required=True)
    session_id = graphene.String()
    application_url = graphene.String()
    error = graphene.String()
