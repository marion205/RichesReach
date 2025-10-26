"""
GraphQL Schema Extensions for Voice AI Trading
Advanced order types, real-time subscriptions, and voice command integration
"""

import graphene
from graphene import ObjectType, String, Float, Int, Boolean, List, Field
from graphene_django import DjangoObjectType
from datetime import datetime
import logging

from ..voice.command_parser import VoiceCommandParser, ParsedOrder
from ..broker.adapters.base import Broker, OrderSide, OrderType, TimeInForce
from ..broker.adapters.alpaca_paper import AlpacaPaperBroker
from django.conf import settings


# Input Types
class OrderInput(graphene.InputObjectType):
    symbol = String(required=True)
    side = String(required=True)  # "buy" or "sell"
    quantity = Int(required=True)
    order_type = String(required=True)  # "market", "limit", "stop"
    price = Float()
    stop_price = Float()
    client_order_id = String()


class VoiceCommandInput(graphene.InputObjectType):
    transcript = String(required=True)
    voice_name = String(default_value="Nova")


class BracketOrderInput(graphene.InputObjectType):
    symbol = String(required=True)
    side = String(required=True)
    quantity = Int(required=True)
    take_profit_price = Float(required=True)
    stop_loss_price = Float(required=True)
    limit_price = Float()


# Output Types
class OrderType(graphene.ObjectType):
    id = String()
    symbol = String()
    side = String()
    order_type = String()
    quantity = Int()
    status = String()
    filled_quantity = Int()
    remaining_quantity = Int()
    limit_price = Float()
    stop_price = Float()
    average_fill_price = Float()
    time_in_force = String()
    created_at = String()
    updated_at = String()
    client_order_id = String()


class QuoteUpdateType(graphene.ObjectType):
    symbol = String()
    bid_price = Float()
    ask_price = Float()
    spread_bps = Float()
    timestamp = String()
    mid_price = Float()


class VoiceAlertType(graphene.ObjectType):
    symbol = String()
    message = String()
    alert_type = String()
    timestamp = String()


class ParsedOrderType(graphene.ObjectType):
    symbol = String()
    side = String()
    quantity = Int()
    order_type = String()
    price = Float()
    confidence = Float()
    confirmation_message = String()


class OrderResult(graphene.ObjectType):
    success = Boolean()
    order = Field(OrderType)
    message = String()
    error = String()


class VoiceCommandResult(graphene.ObjectType):
    success = Boolean()
    parsed_order = Field(ParsedOrderType)
    message = String()
    error = String()


# Mutations
class PlaceOrder(graphene.Mutation):
    """Place a trading order through Alpaca"""
    
    class Arguments:
        input = OrderInput(required=True)
    
    Output = OrderResult
    
    async def mutate(self, info, input):
        try:
            # Get broker instance
            broker = AlpacaPaperBroker(
                api_key_id=settings.ALPACA_API_KEY_ID,
                api_secret_key=settings.ALPACA_SECRET_KEY
            )
            
            # Map input to broker enums
            side = OrderSide.BUY if input.side.lower() == "buy" else OrderSide.SELL
            order_type = OrderType(input.order_type.lower())
            
            # Place order
            order = await broker.place_order(
                symbol=input.symbol,
                side=side,
                quantity=input.quantity,
                order_type=order_type,
                limit_price=input.price,
                stop_price=input.stop_price,
                client_order_id=input.client_order_id
            )
            
            # Log the order
            logging.info(f"Order placed: {order.symbol} {order.side} {order.quantity} - ID: {order.id}")
            
            return OrderResult(
                success=True,
                order=OrderType(
                    id=order.id,
                    symbol=order.symbol,
                    side=order.side.value,
                    order_type=order.type.value,
                    quantity=order.quantity,
                    status=order.status.value,
                    filled_quantity=order.filled_quantity,
                    remaining_quantity=order.remaining_quantity,
                    limit_price=order.limit_price,
                    stop_price=order.stop_price,
                    average_fill_price=order.average_fill_price,
                    time_in_force=order.time_in_force.value,
                    created_at=order.created_at.isoformat() if order.created_at else None,
                    updated_at=order.updated_at.isoformat() if order.updated_at else None,
                    client_order_id=order.client_order_id
                ),
                message="Order placed successfully"
            )
            
        except Exception as e:
            logging.error(f"Order placement failed: {e}")
            return OrderResult(
                success=False,
                message=f"Order placement failed: {str(e)}",
                error=str(e)
            )


class PlaceBracketOrder(graphene.Mutation):
    """Place a bracket order (entry + take profit + stop loss)"""
    
    class Arguments:
        input = BracketOrderInput(required=True)
    
    Output = OrderResult
    
    async def mutate(self, info, input):
        try:
            broker = AlpacaPaperBroker(
                api_key_id=settings.ALPACA_API_KEY_ID,
                api_secret_key=settings.ALPACA_SECRET_KEY
            )
            
            # Create bracket order
            bracket_orders = {
                "take_profit": input.take_profit_price,
                "stop_loss": input.stop_loss_price
            }
            
            side = OrderSide.BUY if input.side.lower() == "buy" else OrderSide.SELL
            order_type = OrderType.LIMIT if input.limit_price else OrderType.MARKET
            
            order = await broker.place_order(
                symbol=input.symbol,
                side=side,
                quantity=input.quantity,
                order_type=order_type,
                limit_price=input.limit_price,
                bracket_orders=bracket_orders
            )
            
            return OrderResult(
                success=True,
                order=OrderType(
                    id=order.id,
                    symbol=order.symbol,
                    side=order.side.value,
                    order_type=order.type.value,
                    quantity=order.quantity,
                    status=order.status.value,
                    message="Bracket order placed successfully"
                )
            )
            
        except Exception as e:
            return OrderResult(
                success=False,
                message=f"Bracket order failed: {str(e)}",
                error=str(e)
            )


class ParseVoiceCommand(graphene.Mutation):
    """Parse voice command into structured order data"""
    
    class Arguments:
        input = VoiceCommandInput(required=True)
    
    Output = VoiceCommandResult
    
    def mutate(self, info, input):
        try:
            parser = VoiceCommandParser()
            parsed_order = parser.parse_command(input.transcript)
            
            if parsed_order:
                confirmation_message = parser.get_confirmation_message(
                    parsed_order, 
                    input.voice_name
                )
                
                return VoiceCommandResult(
                    success=True,
                    parsed_order=ParsedOrderType(
                        symbol=parsed_order.symbol,
                        side=parsed_order.side,
                        quantity=parsed_order.quantity,
                        order_type=parsed_order.order_type,
                        price=parsed_order.price,
                        confidence=parsed_order.confidence,
                        confirmation_message=confirmation_message
                    ),
                    message="Voice command parsed successfully"
                )
            else:
                return VoiceCommandResult(
                    success=False,
                    message="Could not parse voice command",
                    error="Invalid command format"
                )
                
        except Exception as e:
            return VoiceCommandResult(
                success=False,
                message=f"Voice parsing failed: {str(e)}",
                error=str(e)
            )


class CancelOrder(graphene.Mutation):
    """Cancel an existing order"""
    
    class Arguments:
        order_id = String(required=True)
    
    Output = OrderResult
    
    async def mutate(self, info, order_id):
        try:
            broker = AlpacaPaperBroker(
                api_key_id=settings.ALPACA_API_KEY_ID,
                api_secret_key=settings.ALPACA_SECRET_KEY
            )
            
            result = await broker.cancel_order(order_id)
            
            return OrderResult(
                success=result["status"] == "success",
                message=result["message"]
            )
            
        except Exception as e:
            return OrderResult(
                success=False,
                message=f"Order cancellation failed: {str(e)}",
                error=str(e)
            )


# Subscriptions
class QuoteUpdateSubscription(graphene.ObjectType):
    """Real-time quote updates subscription"""
    
    quote_update = Field(QuoteUpdateType, symbol=String())
    
    def resolve_quote_update(self, info, symbol=None):
        # This will be handled by Django Channels
        return QuoteUpdateType(
            symbol=symbol,
            bid_price=0.0,
            ask_price=0.0,
            spread_bps=0.0,
            timestamp=datetime.now().isoformat(),
            mid_price=0.0
        )


class VoiceAlertSubscription(graphene.ObjectType):
    """Voice AI alerts subscription"""
    
    voice_alert = Field(VoiceAlertType)
    
    def resolve_voice_alert(self, info):
        # This will be handled by Django Channels
        return VoiceAlertType(
            symbol="",
            message="",
            alert_type="",
            timestamp=datetime.now().isoformat()
        )


# Main Mutation and Subscription classes
class TradingMutations(graphene.ObjectType):
    place_order = PlaceOrder.Field()
    place_bracket_order = PlaceBracketOrder.Field()
    parse_voice_command = ParseVoiceCommand.Field()
    cancel_order = CancelOrder.Field()


class TradingSubscriptions(graphene.ObjectType):
    quote_update = QuoteUpdateSubscription.Field()
    voice_alert = VoiceAlertSubscription.Field()
