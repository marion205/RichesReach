"""
Education GraphQL Query Class
Adds tutorProgress and dailyQuest queries to the GraphQL schema
"""
import graphene
from graphql import GraphQLError

# Import the resolver
from .education_resolvers import education_resolver


class SkillMasteryType(graphene.ObjectType):
    """Skill Mastery Type"""
    skill = graphene.String(required=True)
    masteryLevel = graphene.Float(required=True)
    masteryPercentage = graphene.Int(required=True)
    status = graphene.String(required=True)
    lastPracticed = graphene.DateTime()
    timesPracticed = graphene.Int(required=True)


class TutorProgressType(graphene.ObjectType):
    """Tutor Progress Type"""
    userId = graphene.ID(required=True)
    xp = graphene.Int(required=True)
    level = graphene.Int(required=True)
    streakDays = graphene.Int(required=True)
    badges = graphene.List(graphene.String, required=True)
    lastLogin = graphene.DateTime()
    abilityEstimate = graphene.Float(required=True)
    nextReviewAt = graphene.DateTime()
    skillMastery = graphene.List(SkillMasteryType, required=True)
    reviewQueue = graphene.List(graphene.String, required=True)
    hearts = graphene.Int(required=True)
    maxHearts = graphene.Int(required=True)
    heartsRegenAt = graphene.DateTime()


class CompletionCriteriaType(graphene.ObjectType):
    """Completion Criteria Type"""
    scenariosCompleted = graphene.Int()
    successRate = graphene.Float()
    quizzesPassed = graphene.Int()
    scoreThreshold = graphene.Int()
    duelsWon = graphene.Int()
    accuracy = graphene.Float()
    strategiesLearned = graphene.Int()
    communityEngagement = graphene.Int()
    simulationsCompleted = graphene.Int()
    profitTarget = graphene.Float()
    lessonsCompleted = graphene.Int()


class QuestType(graphene.ObjectType):
    """Quest Type"""
    id = graphene.ID(required=True)
    title = graphene.String(required=True)
    description = graphene.String(required=True)
    questType = graphene.String(required=True)
    difficulty = graphene.String(required=True)
    xpReward = graphene.Int(required=True)
    timeLimitMinutes = graphene.Int(required=True)
    requiredSkills = graphene.List(graphene.String, required=True)
    regimeContext = graphene.String(required=True)
    voiceNarration = graphene.String(required=True)
    completionCriteria = graphene.Field(CompletionCriteriaType, required=True)
    isActive = graphene.Boolean()
    createdAt = graphene.DateTime()
    expiresAt = graphene.DateTime()
    participants = graphene.Int()
    completionRate = graphene.Float()


class EducationQuery(graphene.ObjectType):
    """Education GraphQL Query"""
    
    tutorProgress = graphene.Field(TutorProgressType, required=True)
    dailyQuest = graphene.Field(QuestType, required=True)
    
    def resolve_tutor_progress(self, info):
        """Resolve tutor progress"""
        try:
            return education_resolver.resolve_tutor_progress(info)
        except Exception as e:
            raise GraphQLError(f"Failed to fetch tutor progress: {str(e)}")
    
    def resolve_daily_quest(self, info):
        """Resolve daily quest"""
        try:
            return education_resolver.resolve_daily_quest(info)
        except Exception as e:
            raise GraphQLError(f"Failed to fetch daily quest: {str(e)}")

