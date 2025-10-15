import graphene
from core.sbloc_types import SblocBankType, SblocSessionType
from core.models import SblocBank, SblocSession

class SblocQuery(graphene.ObjectType):
    sbloc_banks = graphene.List(SblocBankType)
    sbloc_session = graphene.Field(SblocSessionType, session_id=graphene.ID(required=True))
    my_sbloc_sessions = graphene.List(SblocSessionType)

    def resolve_sbloc_banks(self, info):
        return SblocBank.objects.filter(is_active=True).order_by('min_apr')

    def resolve_sbloc_session(self, info, session_id):
        s = SblocSession.objects.get(pk=session_id)
        return SblocSessionType(id=s.id, status=s.status, application_url=s.application_url)

    def resolve_my_sbloc_sessions(self, info):
        uid = getattr(info.context.user, "id", None)
        qs = SblocSession.objects.all() if not uid else SblocSession.objects.filter(referral__user_id=uid)
        return [SblocSessionType(id=s.id, status=s.status, application_url=s.application_url) for s in qs]
