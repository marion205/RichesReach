"""
GraphQL Mutations for SBLOC (Securities-Based Line of Credit) Operations
"""
import os
import graphene
from typing import Optional
from .sbloc_types import SBLOCBankType, SBLOCSessionType
from .sbloc_models import SBLOCBank, SBLOCSession
from graphql import GraphQLError
import uuid
from django.utils import timezone


class CreateSBLOCSession(graphene.Mutation):
    """Create a new SBLOC application session"""
    
    class Arguments:
        bank_id = graphene.ID(required=True, description="SBLOC bank ID")
        amount_usd = graphene.Int(required=True, description="Requested loan amount in USD")
    
    success = graphene.Boolean()
    session_id = graphene.String()
    application_url = graphene.String()
    error = graphene.String()
    
    @staticmethod
    def mutate(root, info, bank_id, amount_usd):
        """Create SBLOC session"""
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("Authentication required")
        
        # Validate amount
        if amount_usd < 1000:
            return CreateSBLOCSession(
                success=False,
                error="Minimum loan amount is $1,000"
            )
        
        if amount_usd > 10000000:  # $10M max
            return CreateSBLOCSession(
                success=False,
                error="Maximum loan amount is $10,000,000"
            )
        
        try:
            # Get bank
            bank = SBLOCBank.objects.get(id=bank_id, is_active=True)
        except SBLOCBank.DoesNotExist:
            return CreateSBLOCSession(
                success=False,
                error="SBLOC bank not found"
            )
        
        # Check if aggregator is enabled
        use_aggregator = os.getenv('USE_SBLOC_AGGREGATOR', 'false').lower() == 'true'
        
        if use_aggregator:
            # Use aggregator service to create session
            try:
                from .sbloc_aggregator import SBLOCAggregatorService
                aggregator = SBLOCAggregatorService()
                result = aggregator.create_session(
                    user=user,
                    bank_id=bank_id,
                    amount_usd=amount_usd
                )
                
                # Create session record
                session = SBLOCSession.objects.create(
                    user=user,
                    bank=bank,
                    amount_usd=amount_usd,
                    session_id=result.get('session_id', str(uuid.uuid4())),
                    application_url=result.get('application_url', ''),
                    status='PENDING',
                    aggregator_response=result
                )
                
                return CreateSBLOCSession(
                    success=True,
                    session_id=session.session_id,
                    application_url=session.application_url
                )
            except Exception as e:
                return CreateSBLOCSession(
                    success=False,
                    error=f"Failed to create session: {str(e)}"
                )
        else:
            # Direct bank integration (if implemented)
            # For now, create a session with a placeholder URL
            session_id = str(uuid.uuid4())
            application_url = f"https://{bank.name.lower().replace(' ', '')}.com/apply?sbloc_session={session_id}"
            
            session = SBLOCSession.objects.create(
                user=user,
                bank=bank,
                amount_usd=amount_usd,
                session_id=session_id,
                application_url=application_url,
                status='PENDING'
            )
            
            return CreateSBLOCSession(
                success=True,
                session_id=session.session_id,
                application_url=session.application_url
            )


class SyncSBLOCBanks(graphene.Mutation):
    """Sync SBLOC banks from aggregator service"""
    
    success = graphene.Boolean()
    banks_synced = graphene.Int()
    error = graphene.String()
    
    @staticmethod
    def mutate(root, info):
        """Sync banks from aggregator"""
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("Authentication required")
        
        # Only allow admins to sync
        if not user.is_staff:
            return SyncSBLOCBanks(
                success=False,
                error="Admin access required"
            )
        
        use_aggregator = os.getenv('USE_SBLOC_AGGREGATOR', 'false').lower() == 'true'
        
        if not use_aggregator:
            return SyncSBLOCBanks(
                success=False,
                error="Aggregator service not enabled"
            )
        
        try:
            from .sbloc_aggregator import SBLOCAggregatorService
            aggregator = SBLOCAggregatorService()
            banks = aggregator.get_available_banks()
            
            # Sync banks to database
            banks_synced = 0
            for bank_data in banks:
                bank, created = SBLOCBank.objects.update_or_create(
                    external_id=bank_data.get('id'),
                    defaults={
                        'name': bank_data.get('name', ''),
                        'logo_url': bank_data.get('logoUrl'),
                        'min_apr': bank_data.get('minApr'),
                        'max_apr': bank_data.get('maxApr'),
                        'min_ltv': bank_data.get('minLtv'),
                        'max_ltv': bank_data.get('maxLtv'),
                        'notes': bank_data.get('notes'),
                        'regions': bank_data.get('regions', []),
                        'min_loan_usd': bank_data.get('minLoanUsd'),
                        'is_active': True,
                    }
                )
                if created:
                    banks_synced += 1
            
            return SyncSBLOCBanks(
                success=True,
                banks_synced=banks_synced
            )
        except Exception as e:
            return SyncSBLOCBanks(
                success=False,
                error=f"Failed to sync banks: {str(e)}"
            )


class SBLOCMutations(graphene.ObjectType):
    """GraphQL mutations for SBLOC operations"""
    create_sbloc_session = CreateSBLOCSession.Field()
    createSblocSession = CreateSBLOCSession.Field()  # Alias for mobile app compatibility
    sync_sbloc_banks = SyncSBLOCBanks.Field()
    syncSblocBanks = SyncSBLOCBanks.Field()  # Alias for mobile app compatibility

