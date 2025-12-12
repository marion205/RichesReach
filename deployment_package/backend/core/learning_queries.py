"""
GraphQL Queries and Mutations for Learning/Education Features
- Tutor progress tracking
- Daily quests
- Lessons and quizzes
- Live simulations
"""
import graphene
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class SkillMasteryType(graphene.ObjectType):
    """GraphQL type for skill mastery"""
    skill = graphene.String()
    masteryLevel = graphene.String()
    masteryPercentage = graphene.Float()
    status = graphene.String()


class TutorProgressType(graphene.ObjectType):
    """GraphQL type for tutor progress"""
    userId = graphene.String()
    xp = graphene.Int()
    level = graphene.Int()
    streakDays = graphene.Int()
    badges = graphene.List(graphene.String)
    abilityEstimate = graphene.Float()
    skillMastery = graphene.List(SkillMasteryType)
    hearts = graphene.Int()
    maxHearts = graphene.Int()


class RewardType(graphene.ObjectType):
    """GraphQL type for quest/lesson rewards"""
    type = graphene.String()
    amount = graphene.Int()


class ScenarioType(graphene.ObjectType):
    """GraphQL type for quest scenario"""
    id = graphene.String()
    description = graphene.String()
    type = graphene.String()
    marketCondition = graphene.String()
    expectedOutcome = graphene.String()


class QuestType(graphene.ObjectType):
    """GraphQL type for quest"""
    id = graphene.String()
    topic = graphene.String()
    difficulty = graphene.String()
    rewards = graphene.List(RewardType)
    progress = graphene.Float()
    narration = graphene.String()
    expiresAt = graphene.String()
    questType = graphene.String()
    timeLimitMinutes = graphene.Int()
    scenarios = graphene.List(ScenarioType)


class QuizType(graphene.ObjectType):
    """GraphQL type for quiz"""
    id = graphene.String()
    question = graphene.String()
    options = graphene.List(graphene.String)
    correct = graphene.Int()
    explanation = graphene.String()
    voiceHint = graphene.String()


class LessonType(graphene.ObjectType):
    """GraphQL type for lesson"""
    id = graphene.String()
    title = graphene.String()
    text = graphene.String()
    voiceNarration = graphene.String()
    quiz = graphene.Field(QuizType)
    xpEarned = graphene.Int()
    streak = graphene.Int()
    difficulty = graphene.String()
    estimatedTimeMinutes = graphene.Int()
    skillsTargeted = graphene.List(graphene.String)


class CompletionCriteriaType(graphene.ObjectType):
    """GraphQL type for quest completion criteria"""
    scenariosCompleted = graphene.Int()
    successRate = graphene.Float()


class DailyQuestType(graphene.ObjectType):
    """GraphQL type for daily quest"""
    id = graphene.String()
    title = graphene.String()
    description = graphene.String()
    questType = graphene.String()
    difficulty = graphene.String()
    xpReward = graphene.Int()
    timeLimitMinutes = graphene.Int()
    requiredSkills = graphene.List(graphene.String)
    regimeContext = graphene.String()
    voiceNarration = graphene.String()
    completionCriteria = graphene.Field(CompletionCriteriaType)


class LevelProgressType(graphene.ObjectType):
    """GraphQL type for level progress"""
    currentLevel = graphene.Int()
    currentXp = graphene.Int()
    nextLevelXp = graphene.Int()
    progressPercentage = graphene.Float()


class QuizResultType(graphene.ObjectType):
    """GraphQL type for quiz submission result"""
    score = graphene.Float()
    xpBonus = graphene.Int()
    totalXp = graphene.Int()
    feedback = graphene.String()
    badgesEarned = graphene.List(graphene.String)
    nextRecommendation = graphene.String()
    streakStatus = graphene.String()
    levelProgress = graphene.Field(LevelProgressType)


class QuestProgressResultType(graphene.ObjectType):
    """GraphQL type for quest progress update result"""
    questId = graphene.String()
    progress = graphene.Float()
    completed = graphene.Boolean()
    rewardsEarned = graphene.List(RewardType)
    message = graphene.String()
    nextQuestAvailable = graphene.Boolean()
    streakBonus = graphene.Int()


class PerformanceMetricsType(graphene.ObjectType):
    """GraphQL type for live simulation performance metrics"""
    totalTrades = graphene.Int()
    winRate = graphene.Float()
    totalPnL = graphene.Float()
    returnPercentage = graphene.Float()


class LiveSimType(graphene.ObjectType):
    """GraphQL type for live simulation"""
    id = graphene.String()
    symbol = graphene.String()
    mode = graphene.String()
    initialBalance = graphene.Float()
    currentBalance = graphene.Float()
    learningObjectives = graphene.List(graphene.String)
    voiceFeedbackEnabled = graphene.Boolean()
    regimeContext = graphene.String()
    performanceMetrics = graphene.Field(PerformanceMetricsType)


class LearningQueries(graphene.ObjectType):
    """GraphQL queries for learning/education features"""
    
    tutor_progress = graphene.Field(
        TutorProgressType,
        description="Get user's tutor progress"
    )
    tutorProgress = graphene.Field(
        TutorProgressType,
        description="Get user's tutor progress (camelCase alias)"
    )
    
    daily_quest = graphene.Field(
        DailyQuestType,
        description="Get today's daily quest"
    )
    dailyQuest = graphene.Field(
        DailyQuestType,
        description="Get today's daily quest (camelCase alias)"
    )
    
    def resolve_tutor_progress(self, info):
        """Get user's tutor progress"""
        try:
            user = info.context.user
            if not user.is_authenticated:
                return None
            
            # In production, this would query from database
            return TutorProgressType(
                userId=str(user.id),
                xp=1250,
                level=3,
                streakDays=7,
                badges=['First Steps', 'Quiz Master', 'Streak Keeper'],
                abilityEstimate=0.75,
                skillMastery=[
                    SkillMasteryType(
                        skill='options_trading',
                        masteryLevel='intermediate',
                        masteryPercentage=65.0,
                        status='learning'
                    )
                ],
                hearts=3,
                maxHearts=5
            )
        except Exception as e:
            logger.error(f"Error fetching tutor progress: {e}", exc_info=True)
            return None
    
    def resolve_tutorProgress(self, info):
        """CamelCase alias for tutor_progress"""
        return self.resolve_tutor_progress(info)
    
    def resolve_daily_quest(self, info):
        """Get today's daily quest"""
        try:
            user = info.context.user
            if not user.is_authenticated:
                return None
            
            # In production, this would query from database
            return DailyQuestType(
                id='quest_001',
                title='Options Spread Mastery',
                description='Complete 3 options spread scenarios with 80% accuracy',
                questType='simulation',
                difficulty='medium',
                xpReward=150,
                timeLimitMinutes=15,
                requiredSkills=['options_trading', 'risk_management'],
                regimeContext='bull_market',
                voiceNarration="Welcome to today's quest! You'll practice options spreads in a bull market scenario.",
                completionCriteria=CompletionCriteriaType(
                    scenariosCompleted=0,
                    successRate=0.0
                )
            )
        except Exception as e:
            logger.error(f"Error fetching daily quest: {e}", exc_info=True)
            return None
    
    def resolve_dailyQuest(self, info):
        """CamelCase alias for daily_quest"""
        return self.resolve_daily_quest(info)


class StartQuest(graphene.Mutation):
    """Start a new quest"""
    class Arguments:
        difficulty = graphene.String(required=True)
    
    quest = graphene.Field(QuestType)
    
    def mutate(self, info, difficulty):
        try:
            user = info.context.user
            if not user.is_authenticated:
                return StartQuest(quest=None)
            
            # In production, this would create a quest in the database
            quest = QuestType(
                id='quest_new_001',
                topic='options_trading',
                difficulty=difficulty,
                rewards=[
                    RewardType(type='xp', amount=100),
                    RewardType(type='badge', amount=1)
                ],
                progress=0.0,
                narration=f"Starting a {difficulty} quest!",
                expiresAt='2024-01-02T00:00:00Z',
                questType='simulation',
                timeLimitMinutes=15,
                scenarios=[]
            )
            
            return StartQuest(quest=quest)
        except Exception as e:
            logger.error(f"Error starting quest: {e}", exc_info=True)
            return StartQuest(quest=None)


class UpdateQuestProgress(graphene.Mutation):
    """Update quest progress"""
    class Arguments:
        questId = graphene.String(required=True)
        progress = graphene.Float(required=True)
        completedScenarios = graphene.Int(required=True)
    
    result = graphene.Field(QuestProgressResultType)
    
    def mutate(self, info, questId, progress, completedScenarios):
        try:
            user = info.context.user
            if not user.is_authenticated:
                return UpdateQuestProgress(result=None)
            
            # In production, this would update quest in database
            result = QuestProgressResultType(
                questId=questId,
                progress=progress,
                completed=progress >= 1.0,
                rewardsEarned=[
                    RewardType(type='xp', amount=50) if progress >= 1.0 else None
                ],
                message='Progress updated successfully',
                nextQuestAvailable=progress >= 1.0,
                streakBonus=10 if progress >= 1.0 else 0
            )
            
            return UpdateQuestProgress(result=result)
        except Exception as e:
            logger.error(f"Error updating quest progress: {e}", exc_info=True)
            return UpdateQuestProgress(result=None)


class StartLesson(graphene.Mutation):
    """Start a new lesson"""
    class Arguments:
        topic = graphene.String(required=True)
        regime = graphene.String()
    
    lesson = graphene.Field(LessonType)
    
    def mutate(self, info, topic, regime=None):
        try:
            user = info.context.user
            if not user.is_authenticated:
                return StartLesson(lesson=None)
            
            # In production, this would create a lesson in the database
            lesson = LessonType(
                id='lesson_new_001',
                title=f'Introduction to {topic}',
                text=f'This lesson covers the basics of {topic}.',
                voiceNarration=f'Welcome to the lesson on {topic}.',
                quiz=QuizType(
                    id='quiz_001',
                    question=f'What is {topic}?',
                    options=['Option A', 'Option B', 'Option C', 'Option D'],
                    correct=0,
                    explanation=f'{topic} is...',
                    voiceHint='Think about the basics'
                ),
                xpEarned=50,
                streak=1,
                difficulty='beginner',
                estimatedTimeMinutes=10,
                skillsTargeted=[topic]
            )
            
            return StartLesson(lesson=lesson)
        except Exception as e:
            logger.error(f"Error starting lesson: {e}", exc_info=True)
            return StartLesson(lesson=None)


class SubmitQuiz(graphene.Mutation):
    """Submit quiz answers"""
    class Arguments:
        lessonId = graphene.ID(required=True)
        answers = graphene.List(graphene.Int, required=True)
    
    result = graphene.Field(QuizResultType)
    
    def mutate(self, info, lessonId, answers):
        try:
            user = info.context.user
            if not user.is_authenticated:
                return SubmitQuiz(result=None)
            
            # In production, this would grade the quiz and update progress
            score = 0.85  # Mock score
            result = QuizResultType(
                score=score,
                xpBonus=25,
                totalXp=1275,
                feedback='Great job! You scored 85%.',
                badgesEarned=['Quiz Master'] if score >= 0.8 else [],
                nextRecommendation='Try the advanced lesson',
                streakStatus='active',
                levelProgress=LevelProgressType(
                    currentLevel=3,
                    currentXp=1275,
                    nextLevelXp=2000,
                    progressPercentage=63.75
                )
            )
            
            return SubmitQuiz(result=result)
        except Exception as e:
            logger.error(f"Error submitting quiz: {e}", exc_info=True)
            return SubmitQuiz(result=None)


class StartLiveSim(graphene.Mutation):
    """Start a live trading simulation"""
    class Arguments:
        symbol = graphene.String(required=True)
        mode = graphene.String(required=True)
    
    simulation = graphene.Field(LiveSimType)
    
    def mutate(self, info, symbol, mode):
        try:
            user = info.context.user
            if not user.is_authenticated:
                return StartLiveSim(simulation=None)
            
            # In production, this would create a simulation in the database
            simulation = LiveSimType(
                id='sim_new_001',
                symbol=symbol,
                mode=mode,
                initialBalance=10000.0,
                currentBalance=10000.0,
                learningObjectives=['Learn risk management', 'Practice entry/exit timing'],
                voiceFeedbackEnabled=True,
                regimeContext='bull_market',
                performanceMetrics=PerformanceMetricsType(
                    totalTrades=0,
                    winRate=0.0,
                    totalPnL=0.0,
                    returnPercentage=0.0
                )
            )
            
            return StartLiveSim(simulation=simulation)
        except Exception as e:
            logger.error(f"Error starting live sim: {e}", exc_info=True)
            return StartLiveSim(simulation=None)


class LearningMutations(graphene.ObjectType):
    """GraphQL mutations for learning/education features"""
    
    start_quest = StartQuest.Field()
    startQuest = StartQuest.Field(name='startQuest')
    
    update_quest_progress = UpdateQuestProgress.Field()
    updateQuestProgress = UpdateQuestProgress.Field(name='updateQuestProgress')
    
    start_lesson = StartLesson.Field()
    startLesson = StartLesson.Field(name='startLesson')
    
    submit_quiz = SubmitQuiz.Field()
    submitQuiz = SubmitQuiz.Field(name='submitQuiz')
    
    start_live_sim = StartLiveSim.Field()
    startLiveSim = StartLiveSim.Field(name='startLiveSim')

