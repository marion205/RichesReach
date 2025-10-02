import graphene
from django.conf import settings
from core.sbloc_types import CreateSblocSessionResult
from core.services.sbloc import SblocService

class CreateSblocSession(graphene.Mutation):
    class Arguments:
        bank_id = graphene.ID(required=True)
        amount_usd = graphene.Int(required=True)

    Output = CreateSblocSessionResult

    def mutate(self, info, bank_id, amount_usd):
        user = info.context.user if info.context.user.is_authenticated else None
        svc = SblocService()
        try:
            session = svc.create_session(user=user, bank_id=str(bank_id), amount_usd=amount_usd)
            return CreateSblocSessionResult(success=True, session_id=session.id, application_url=session.application_url)
        except Exception as e:
            return CreateSblocSessionResult(success=False, error=str(e))

class SblocMutation(graphene.ObjectType):
    create_sbloc_session = CreateSblocSession.Field()
