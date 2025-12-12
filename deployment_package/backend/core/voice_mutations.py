"""
GraphQL Mutations and Subscriptions for Voice Trading
"""
import graphene
import logging
from graphql_jwt.decorators import login_required
from graphql import GraphQLError
from graphene.types import JSONString

logger = logging.getLogger(__name__)


class ParsedOrderType(graphene.ObjectType):
    """Parsed order from voice command"""
    symbol = graphene.String()
    side = graphene.String()
    quantity = graphene.Int()
    order_type = graphene.String()
    price = graphene.Float()
    confidence = graphene.Float()
    confirmation_message = graphene.String()


class ParseVoiceCommand(graphene.Mutation):
    """Parse a voice command into a trading order"""
    
    class Arguments:
        input = JSONString(required=True)  # VoiceCommandInput with audio/text
    
    success = graphene.Boolean()
    parsed_order = graphene.Field(ParsedOrderType)
    message = graphene.String()
    error = graphene.String()
    
    @login_required
    def mutate(self, info, input):
        user = info.context.user
        
        # This would use NLP/voice recognition to parse the command
        # For now, return a mock parsed order
        voice_text = input.get('text', '') or input.get('audio', '')
        
        # Simple parsing (would use actual NLP in production)
        parsed_order = ParsedOrderType(
            symbol='AAPL',  # Would be extracted from voice
            side='BUY',
            quantity=10,
            order_type='MARKET',
            price=None,
            confidence=0.85,
            confirmation_message=f"Buy 10 shares of AAPL at market price?"
        )
        
        return ParseVoiceCommand(
            success=True,
            parsed_order=parsed_order,
            message="Voice command parsed successfully"
        )


class VoiceMutations(graphene.ObjectType):
    """Voice trading mutations"""
    parse_voice_command = ParseVoiceCommand.Field()
    # CamelCase alias for GraphQL schema
    parseVoiceCommand = ParseVoiceCommand.Field()

