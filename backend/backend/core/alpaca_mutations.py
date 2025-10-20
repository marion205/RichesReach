"""
Alpaca-specific GraphQL mutations for account management and trading
"""
import graphene
from graphene_django import DjangoObjectType
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import datetime
import logging

# Get the User model (handles custom user models)
User = get_user_model()

from .models.alpaca_models import AlpacaAccount, AlpacaKycDocument, AlpacaOrder, AlpacaPosition, AlpacaActivity
from .services.alpaca_broker_service import AlpacaBrokerService

logger = logging.getLogger(__name__)

# =============================================================================
# GRAPHQL TYPES
# =============================================================================

class AlpacaAccountType(DjangoObjectType):
    # Add computed fields for frontend (camelCase for GraphQL)
    buyingPower = graphene.Float()
    cash = graphene.Float()
    portfolioValue = graphene.Float()
    accountNumber = graphene.String()  # Alias for alpaca_account_id
    
    def resolve_buyingPower(self, info):
        """Calculate buying power based on account status and mock data"""
        if self.status == 'APPROVED':
            return 10000.0  # Mock buying power
        return 0.0
    
    def resolve_cash(self, info):
        """Calculate available cash"""
        if self.status == 'APPROVED':
            return 5000.0  # Mock cash balance
        return 0.0
    
    def resolve_portfolioValue(self, info):
        """Calculate total portfolio value"""
        if self.status == 'APPROVED':
            return 5000.0  # Mock portfolio value
        return 0.0
    
    def resolve_accountNumber(self, info):
        """Return alpaca_account_id as accountNumber"""
        return self.alpaca_account_id or ""
    
    class Meta:
        model = AlpacaAccount
        fields = '__all__'

class AlpacaKycDocumentType(DjangoObjectType):
    class Meta:
        model = AlpacaKycDocument
        fields = '__all__'

class AlpacaOrderType(DjangoObjectType):
    class Meta:
        model = AlpacaOrder
        fields = '__all__'

class AlpacaPositionType(DjangoObjectType):
    class Meta:
        model = AlpacaPosition
        fields = '__all__'

class AlpacaActivityType(DjangoObjectType):
    class Meta:
        model = AlpacaActivity
        fields = '__all__'

# =============================================================================
# MUTATIONS
# =============================================================================

class CreateAlpacaAccount(graphene.Mutation):
    """Create a new Alpaca brokerage account"""
    
    class Arguments:
        firstName = graphene.String(required=True)
        lastName = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String()
        dateOfBirth = graphene.Date(required=True)
        ssn = graphene.String()
        streetAddress = graphene.String(required=True)
        city = graphene.String(required=True)
        state = graphene.String(required=True)
        postalCode = graphene.String(required=True)
        country = graphene.String(default_value="US")
        employmentStatus = graphene.String()
        annualIncome = graphene.Float()
        netWorth = graphene.Float()
        riskTolerance = graphene.String(default_value="medium")
        investmentExperience = graphene.String(default_value="beginner")
    
    success = graphene.Boolean()
    message = graphene.String()
    account = graphene.Field(AlpacaAccountType)
    alpaca_account_id = graphene.String()
    
    def mutate(self, info, **kwargs):
        user = info.context.user
        logger.info(f"CreateAlpacaAccount: user={user}, is_authenticated={user.is_authenticated if user else 'No user'}")
        
        # For testing purposes, allow unauthenticated access
        # TODO: Re-enable authentication in production
        if not user or not user.is_authenticated:
            # Create a test user for unauthenticated requests
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user, created = User.objects.get_or_create(
                email=kwargs['email'],
                defaults={
                    'username': kwargs['email'],
                    'first_name': kwargs['firstName'],
                    'last_name': kwargs['lastName'],
                    'is_active': True
                }
            )
            logger.info(f"CreateAlpacaAccount: Using test user {user} (created: {created})")
        
        try:
            # Create local Alpaca account record
            alpaca_account = AlpacaAccount.objects.create(
                user=user,
                first_name=kwargs['firstName'],
                last_name=kwargs['lastName'],
                email=kwargs['email'],
                phone=kwargs.get('phone', ''),
                date_of_birth=kwargs['dateOfBirth'],
                ssn=kwargs.get('ssn', ''),
                street_address=kwargs['streetAddress'],
                city=kwargs['city'],
                state=kwargs['state'],
                postal_code=kwargs['postalCode'],
                country=kwargs.get('country', 'US'),
                employment_status=kwargs.get('employmentStatus', ''),
                annual_income=kwargs.get('annualIncome'),
                net_worth=kwargs.get('netWorth'),
                risk_tolerance=kwargs.get('riskTolerance', 'medium'),
                investment_experience=kwargs.get('investmentExperience', 'beginner'),
            )
            
            # Check if Alpaca integration is enabled
            from django.conf import settings
            use_alpaca = getattr(settings, 'USE_ALPACA', False)
            
            if use_alpaca:
                # Create account in Alpaca
                broker_service = AlpacaBrokerService()
                
                account_data = {
                    'contact': {
                        'email_address': kwargs['email'],
                        'phone_number': kwargs.get('phone', ''),
                        'street_address': [kwargs['streetAddress']],
                        'city': kwargs['city'],
                        'state': kwargs['state'],
                        'postal_code': kwargs['postalCode'],
                        'country': kwargs.get('country', 'US'),
                    },
                    'identity': {
                        'given_name': kwargs['firstName'],
                        'family_name': kwargs['lastName'],
                        'date_of_birth': kwargs['dateOfBirth'].isoformat(),
                        'tax_id': kwargs.get('ssn', ''),
                        'tax_id_type': 'USA_SSN',
                    },
                    'disclosures': {
                        'is_control_person': False,
                        'is_affiliated_exchange_or_finra': False,
                        'is_politically_exposed': False,
                        'immediate_family_exposed': False,
                    },
                    'agreements': [
                        {
                            'agreement': 'margin_agreement',
                            'signed_at': datetime.now().isoformat(),
                            'ip_address': info.context.META.get('REMOTE_ADDR', ''),
                        },
                        {
                            'agreement': 'account_agreement',
                            'signed_at': datetime.now().isoformat(),
                            'ip_address': info.context.META.get('REMOTE_ADDR', ''),
                        },
                        {
                            'agreement': 'customer_agreement',
                            'signed_at': datetime.now().isoformat(),
                            'ip_address': info.context.META.get('REMOTE_ADDR', ''),
                        },
                    ],
                    'documents': [],
                    'trusted_contact': {
                        'given_name': kwargs['first_name'],
                        'family_name': kwargs['last_name'],
                        'email_address': kwargs['email'],
                    },
                }
                
                alpaca_response = broker_service.create_account(account_data)
                alpaca_account_id = alpaca_response.get('id')
                
                # Update local record with Alpaca account ID
                alpaca_account.alpaca_account_id = alpaca_account_id
                alpaca_account.status = alpaca_response.get('status', 'PENDING')
                alpaca_account.alpaca_created_at = timezone.now()
                alpaca_account.save()
            else:
                # Mock response for development
                import uuid
                alpaca_account_id = f"mock_{uuid.uuid4().hex[:8]}"
                alpaca_account.alpaca_account_id = alpaca_account_id
                alpaca_account.status = 'APPROVED'  # Mock as approved for development
                alpaca_account.alpaca_created_at = timezone.now()
                alpaca_account.save()
                
                logger.info(f"Mock Alpaca account created: {alpaca_account_id}")
            
            return CreateAlpacaAccount(
                success=True,
                message="Alpaca account created successfully",
                account=alpaca_account,
                alpaca_account_id=alpaca_account_id
            )
            
        except Exception as e:
            logger.error(f"Failed to create Alpaca account: {e}")
            return CreateAlpacaAccount(
                success=False,
                message=f"Failed to create account: {str(e)}"
            )

class CreateKycDocument(graphene.Mutation):
    """Create a KYC document for Alpaca account"""
    
    class Arguments:
        account_id = graphene.String(required=True)
        document_type = graphene.String(required=True)
        document_name = graphene.String(required=True)
        file_name = graphene.String(required=True)
        content_type = graphene.String(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    document = graphene.Field(AlpacaKycDocumentType)
    
    def mutate(self, info, **kwargs):
        user = info.context.user
        if not user.is_authenticated:
            return CreateKycDocument(
                success=False,
                message="Authentication required"
            )
        
        try:
            # Get the Alpaca account
            alpaca_account = AlpacaAccount.objects.get(
                user=user,
                alpaca_account_id=kwargs['account_id']
            )
            
            # Create local KYC document record
            kyc_document = AlpacaKycDocument.objects.create(
                alpaca_account=alpaca_account,
                document_type=kwargs['document_type'],
                document_name=kwargs['document_name'],
                file_name=kwargs['file_name'],
                content_type=kwargs['content_type'],
            )
            
            # Create document in Alpaca
            broker_service = AlpacaBrokerService()
            
            document_data = {
                'document_type': kwargs['document_type'],
                'document_sub_type': 'passport',  # Default, can be customized
                'content': '',  # Will be uploaded separately
            }
            
            alpaca_response = broker_service.create_kyc_document(
                kwargs['account_id'], 
                document_data
            )
            
            # Update local record with Alpaca document ID
            kyc_document.alpaca_document_id = alpaca_response.get('id')
            kyc_document.save()
            
            return CreateKycDocument(
                success=True,
                message="KYC document created successfully",
                document=kyc_document
            )
            
        except AlpacaAccount.DoesNotExist:
            return CreateKycDocument(
                success=False,
                message="Alpaca account not found"
            )
        except Exception as e:
            logger.error(f"Failed to create KYC document: {e}")
            return CreateKycDocument(
                success=False,
                message=f"Failed to create document: {str(e)}"
            )

class CreateAlpacaOrder(graphene.Mutation):
    """Create a trading order through Alpaca"""
    
    class Arguments:
        account_id = graphene.String(required=True)
        symbol = graphene.String(required=True)
        order_type = graphene.String(required=True)
        side = graphene.String(required=True)
        quantity = graphene.Float(required=True)
        price = graphene.Float()
        stop_price = graphene.Float()
        time_in_force = graphene.String(default_value="day")
    
    success = graphene.Boolean()
    message = graphene.String()
    order = graphene.Field(AlpacaOrderType)
    alpaca_order_id = graphene.String()
    
    def mutate(self, info, **kwargs):
        user = info.context.user
        if not user.is_authenticated:
            return CreateAlpacaOrder(
                success=False,
                message="Authentication required"
            )
        
        try:
            # Get the Alpaca account
            alpaca_account = AlpacaAccount.objects.get(
                user=user,
                alpaca_account_id=kwargs['account_id']
            )
            
            if not alpaca_account.is_approved:
                return CreateAlpacaOrder(
                    success=False,
                    message="Account not approved for trading"
                )
            
            # Create order in Alpaca
            broker_service = AlpacaBrokerService()
            
            order_data = {
                'symbol': kwargs['symbol'],
                'qty': str(kwargs['quantity']),
                'side': kwargs['side'],
                'type': kwargs['order_type'],
                'time_in_force': kwargs.get('time_in_force', 'day'),
            }
            
            if kwargs.get('price'):
                order_data['limit_price'] = str(kwargs['price'])
            
            if kwargs.get('stop_price'):
                order_data['stop_price'] = str(kwargs['stop_price'])
            
            alpaca_response = broker_service.create_order(
                kwargs['account_id'],
                order_data
            )
            
            # Create local order record
            alpaca_order = AlpacaOrder.objects.create(
                alpaca_account=alpaca_account,
                alpaca_order_id=alpaca_response['id'],
                symbol=kwargs['symbol'],
                order_type=kwargs['order_type'],
                side=kwargs['side'],
                quantity=kwargs['quantity'],
                price=kwargs.get('price'),
                stop_price=kwargs.get('stop_price'),
                time_in_force=kwargs.get('time_in_force', 'day'),
                status=alpaca_response.get('status', 'new'),
                submitted_at=timezone.now(),
            )
            
            return CreateAlpacaOrder(
                success=True,
                message="Order created successfully",
                order=alpaca_order,
                alpaca_order_id=alpaca_response['id']
            )
            
        except AlpacaAccount.DoesNotExist:
            return CreateAlpacaOrder(
                success=False,
                message="Alpaca account not found"
            )
        except Exception as e:
            logger.error(f"Failed to create order: {e}")
            return CreateAlpacaOrder(
                success=False,
                message=f"Failed to create order: {str(e)}"
            )

class SyncAlpacaData(graphene.Mutation):
    """Sync data from Alpaca API to local database"""
    
    class Arguments:
        account_id = graphene.String(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    synced_orders = graphene.Int()
    synced_positions = graphene.Int()
    synced_activities = graphene.Int()
    
    def mutate(self, info, **kwargs):
        user = info.context.user
        if not user.is_authenticated:
            return SyncAlpacaData(
                success=False,
                message="Authentication required"
            )
        
        try:
            # Get the Alpaca account
            alpaca_account = AlpacaAccount.objects.get(
                user=user,
                alpaca_account_id=kwargs['account_id']
            )
            
            broker_service = AlpacaBrokerService()
            synced_orders = 0
            synced_positions = 0
            synced_activities = 0
            
            # Sync orders
            orders = broker_service.get_orders(kwargs['account_id'])
            for order_data in orders:
                order, created = AlpacaOrder.objects.get_or_create(
                    alpaca_order_id=order_data['id'],
                    defaults={
                        'alpaca_account': alpaca_account,
                        'symbol': order_data['symbol'],
                        'order_type': order_data['order_type'],
                        'side': order_data['side'],
                        'quantity': order_data['qty'],
                        'price': order_data.get('limit_price'),
                        'stop_price': order_data.get('stop_price'),
                        'time_in_force': order_data.get('time_in_force', 'day'),
                        'status': order_data['status'],
                        'filled_quantity': order_data.get('filled_qty', 0),
                        'average_fill_price': order_data.get('filled_avg_price'),
                        'submitted_at': timezone.now(),
                    }
                )
                if created:
                    synced_orders += 1
            
            # Sync positions
            positions = broker_service.get_positions(kwargs['account_id'])
            for position_data in positions:
                position, created = AlpacaPosition.objects.get_or_create(
                    alpaca_account=alpaca_account,
                    symbol=position_data['symbol'],
                    defaults={
                        'quantity': position_data['qty'],
                        'market_value': position_data['market_value'],
                        'cost_basis': position_data['cost_basis'],
                        'unrealized_pl': position_data['unrealized_pl'],
                        'unrealized_plpc': position_data['unrealized_plpc'],
                    }
                )
                if created:
                    synced_positions += 1
            
            # Sync activities
            activities = broker_service.get_activities(kwargs['account_id'])
            for activity_data in activities:
                activity, created = AlpacaActivity.objects.get_or_create(
                    alpaca_activity_id=activity_data['id'],
                    defaults={
                        'alpaca_account': alpaca_account,
                        'activity_type': activity_data['activity_type'],
                        'symbol': activity_data.get('symbol', ''),
                        'quantity': activity_data.get('qty'),
                        'price': activity_data.get('price'),
                        'net_amount': activity_data.get('net_amount'),
                        'description': activity_data.get('description', ''),
                        'activity_date': timezone.now(),
                    }
                )
                if created:
                    synced_activities += 1
            
            return SyncAlpacaData(
                success=True,
                message="Data synced successfully",
                synced_orders=synced_orders,
                synced_positions=synced_positions,
                synced_activities=synced_activities
            )
            
        except AlpacaAccount.DoesNotExist:
            return SyncAlpacaData(
                success=False,
                message="Alpaca account not found"
            )
        except Exception as e:
            logger.error(f"Failed to sync Alpaca data: {e}")
            return SyncAlpacaData(
                success=False,
                message=f"Failed to sync data: {str(e)}"
            )

# =============================================================================
# QUERIES
# =============================================================================

class AlpacaQuery(graphene.ObjectType):
    """Alpaca-related queries"""
    
    my_alpaca_account = graphene.Field(AlpacaAccountType)
    alpaca_account = graphene.Field(AlpacaAccountType, user_id=graphene.Int())
    my_alpaca_orders = graphene.List(AlpacaOrderType)
    alpaca_orders = graphene.List(AlpacaOrderType)  # Alias for frontend compatibility
    my_alpaca_positions = graphene.List(AlpacaPositionType)
    alpaca_positions = graphene.List(AlpacaPositionType)  # Alias for frontend compatibility
    my_alpaca_activities = graphene.List(AlpacaActivityType)
    
    def resolve_my_alpaca_account(self, info):
        user = info.context.user
        if not user.is_authenticated:
            return None
        try:
            # Use filter().first() to handle multiple accounts gracefully
            return AlpacaAccount.objects.filter(user=user).first()
        except Exception as e:
            logger.error(f"Error fetching Alpaca account: {e}")
            return None
    
    def resolve_alpaca_account(self, info, user_id=None):
        user = info.context.user
        if not user.is_authenticated:
            return None
        
        # If user_id is provided, verify it matches the authenticated user
        if user_id and user.id != user_id:
            return None
            
        try:
            # Use filter().first() to handle multiple accounts gracefully
            return AlpacaAccount.objects.filter(user=user).first()
        except Exception as e:
            logger.error(f"Error fetching Alpaca account: {e}")
            return None
    
    def resolve_my_alpaca_orders(self, info):
        user = info.context.user
        if not user.is_authenticated:
            return []
        try:
            alpaca_account = AlpacaAccount.objects.filter(user=user).first()
            if alpaca_account:
                return AlpacaOrder.objects.filter(alpaca_account=alpaca_account)
            return []
        except Exception as e:
            logger.error(f"Error fetching Alpaca orders: {e}")
            return []
    
    def resolve_alpaca_orders(self, info):
        """Alias for my_alpaca_orders for frontend compatibility"""
        return self.resolve_my_alpaca_orders(info)
    
    def resolve_my_alpaca_positions(self, info):
        user = info.context.user
        if not user.is_authenticated:
            return []
        try:
            alpaca_account = AlpacaAccount.objects.filter(user=user).first()
            if alpaca_account:
                return AlpacaPosition.objects.filter(alpaca_account=alpaca_account)
            return []
        except Exception as e:
            logger.error(f"Error fetching Alpaca positions: {e}")
            return []
    
    def resolve_alpaca_positions(self, info):
        """Alias for my_alpaca_positions for frontend compatibility"""
        return self.resolve_my_alpaca_positions(info)
    
    def resolve_my_alpaca_activities(self, info):
        user = info.context.user
        if not user.is_authenticated:
            return []
        try:
            alpaca_account = AlpacaAccount.objects.filter(user=user).first()
            if alpaca_account:
                return AlpacaActivity.objects.filter(alpaca_account=alpaca_account)
            return []
        except Exception as e:
            logger.error(f"Error fetching Alpaca activities: {e}")
            return []

# =============================================================================
# MUTATION CLASS
# =============================================================================

class AlpacaMutation(graphene.ObjectType):
    """Alpaca-related mutations"""
    
    create_alpaca_account = CreateAlpacaAccount.Field()
    create_kyc_document = CreateKycDocument.Field()
    create_alpaca_order = CreateAlpacaOrder.Field()
    sync_alpaca_data = SyncAlpacaData.Field()
