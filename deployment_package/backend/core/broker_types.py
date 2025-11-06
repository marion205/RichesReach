"""
GraphQL Types for Broker API
"""
import graphene
from graphene_django import DjangoObjectType
from .broker_models import (
    BrokerAccount, BrokerOrder, BrokerPosition, BrokerActivity,
    BrokerFunding, BrokerGuardrailLog
)


class BrokerAccountType(DjangoObjectType):
    class Meta:
        model = BrokerAccount
        fields = '__all__'


class BrokerOrderType(DjangoObjectType):
    class Meta:
        model = BrokerOrder
        fields = '__all__'


class BrokerPositionType(DjangoObjectType):
    class Meta:
        model = BrokerPosition
        fields = '__all__'


class BrokerActivityType(DjangoObjectType):
    class Meta:
        model = BrokerActivity
        fields = '__all__'


class BrokerFundingType(DjangoObjectType):
    class Meta:
        model = BrokerFunding
        fields = '__all__'

