"""
KYC/AML GraphQL Mutations
Handles Know Your Customer and Anti-Money Laundering workflows
"""
import graphene
from graphene_django import DjangoObjectType
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import datetime
import logging

# Get the User model (handles custom user models)
User = get_user_model()

from .services.kyc_workflow_service import KYCWorkflowService

logger = logging.getLogger(__name__)

# =============================================================================
# GRAPHQL TYPES
# =============================================================================

class KYCWorkflowType(graphene.ObjectType):
    """Type for KYC workflow status"""
    user_id = graphene.String()
    workflow_type = graphene.String()
    status = graphene.String()
    steps_required = graphene.List(graphene.JSONString)
    current_step = graphene.Int()
    created_at = graphene.DateTime()
    estimated_completion = graphene.DateTime()

class KYCStepType(graphene.ObjectType):
    """Type for individual KYC steps"""
    step = graphene.Int()
    name = graphene.String()
    required = graphene.Boolean()
    status = graphene.String()
    completed_at = graphene.DateTime()

class KYCStatusType(graphene.ObjectType):
    """Type for KYC status"""
    account_id = graphene.String()
    status = graphene.String()
    kyc_required = graphene.Boolean()
    documents_uploaded = graphene.Int()
    verification_status = graphene.String()
    last_updated = graphene.DateTime()

class ComplianceStatusType(graphene.ObjectType):
    """Type for compliance status"""
    account_id = graphene.String()
    kyc_complete = graphene.Boolean()
    aml_clear = graphene.Boolean()
    sanctions_clear = graphene.Boolean()
    risk_level = graphene.String()
    monitoring_active = graphene.Boolean()
    last_review = graphene.String()
    next_review = graphene.String()

class AccountStatusType(graphene.ObjectType):
    """Type for account status"""
    account_id = graphene.String()
    status = graphene.String()
    trading_enabled = graphene.Boolean()
    crypto_enabled = graphene.Boolean()
    buying_power = graphene.Float()
    cash = graphene.Float()
    portfolio_value = graphene.Float()
    created_at = graphene.DateTime()
    updated_at = graphene.DateTime()

# =============================================================================
# MUTATIONS
# =============================================================================

class InitiateKYCWorkflow(graphene.Mutation):
    """Initiate KYC workflow for a user"""
    
    class Arguments:
        workflow_type = graphene.String(required=True)  # 'brokerage' or 'crypto'
    
    success = graphene.Boolean()
    message = graphene.String()
    workflow = graphene.Field(KYCWorkflowType)
    
    def mutate(self, info, workflow_type):
        user = info.context.user
        if not user.is_authenticated:
            return InitiateKYCWorkflow(
                success=False,
                message="Authentication required"
            )
        
        try:
            kyc_service = KYCWorkflowService()
            workflow_data = kyc_service.initiate_kyc_workflow(user, workflow_type)
            
            return InitiateKYCWorkflow(
                success=True,
                message=f"KYC workflow initiated for {workflow_type}",
                workflow=KYCWorkflowType(
                    user_id=workflow_data['user_id'],
                    workflow_type=workflow_data['workflow_type'],
                    status=workflow_data['status'],
                    steps_required=workflow_data['steps_required'],
                    current_step=workflow_data['current_step'],
                    created_at=timezone.now(),
                    estimated_completion=timezone.now()
                )
            )
            
        except Exception as e:
            logger.error(f"Failed to initiate KYC workflow: {e}")
            return InitiateKYCWorkflow(
                success=False,
                message=f"Failed to initiate KYC workflow: {str(e)}"
            )

class CreateBrokerageAccount(graphene.Mutation):
    """Create a new brokerage account with KYC data"""
    
    class Arguments:
        kyc_data = graphene.JSONString(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    account_id = graphene.String()
    status = graphene.String()
    
    def mutate(self, info, kyc_data):
        user = info.context.user
        if not user.is_authenticated:
            return CreateBrokerageAccount(
                success=False,
                message="Authentication required"
            )
        
        try:
            kyc_service = KYCWorkflowService()
            response = kyc_service.create_brokerage_account(user, kyc_data)
            
            return CreateBrokerageAccount(
                success=True,
                message="Brokerage account created successfully",
                account_id=response.get('id', ''),
                status=response.get('status', 'PENDING')
            )
            
        except Exception as e:
            logger.error(f"Failed to create brokerage account: {e}")
            return CreateBrokerageAccount(
                success=False,
                message=f"Failed to create account: {str(e)}"
            )

class CreateCryptoAccount(graphene.Mutation):
    """Create a new crypto account with KYC data"""
    
    class Arguments:
        kyc_data = graphene.JSONString(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    account_id = graphene.String()
    status = graphene.String()
    
    def mutate(self, info, kyc_data):
        user = info.context.user
        if not user.is_authenticated:
            return CreateCryptoAccount(
                success=False,
                message="Authentication required"
            )
        
        try:
            kyc_service = KYCWorkflowService()
            response = kyc_service.create_crypto_account(user, kyc_data)
            
            return CreateCryptoAccount(
                success=True,
                message="Crypto account created successfully",
                account_id=response.get('id', ''),
                status=response.get('status', 'PENDING')
            )
            
        except Exception as e:
            logger.error(f"Failed to create crypto account: {e}")
            return CreateCryptoAccount(
                success=False,
                message=f"Failed to create crypto account: {str(e)}"
            )

class UploadKYCDocument(graphene.Mutation):
    """Upload KYC documents for verification"""
    
    class Arguments:
        account_id = graphene.String(required=True)
        document_type = graphene.String(required=True)
        content = graphene.String(required=True)  # Base64 encoded
        content_type = graphene.String(required=False, default_value="application/pdf")
    
    success = graphene.Boolean()
    message = graphene.String()
    document_id = graphene.String()
    
    def mutate(self, info, account_id, document_type, content, content_type="application/pdf"):
        user = info.context.user
        if not user.is_authenticated:
            return UploadKYCDocument(
                success=False,
                message="Authentication required"
            )
        
        try:
            kyc_service = KYCWorkflowService()
            
            document_data = {
                'document_type': document_type,
                'content': content,
                'content_type': content_type
            }
            
            response = kyc_service.upload_kyc_document(account_id, document_data)
            
            return UploadKYCDocument(
                success=True,
                message="Document uploaded successfully",
                document_id=response.get('id', '')
            )
            
        except Exception as e:
            logger.error(f"Failed to upload KYC document: {e}")
            return UploadKYCDocument(
                success=False,
                message=f"Failed to upload document: {str(e)}"
            )

class UpdateKYCStep(graphene.Mutation):
    """Update KYC workflow step status"""
    
    class Arguments:
        step = graphene.Int(required=True)
        status = graphene.String(required=True)
        data = graphene.JSONString(required=False)
    
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info, step, status, data=None):
        user = info.context.user
        if not user.is_authenticated:
            return UpdateKYCStep(
                success=False,
                message="Authentication required"
            )
        
        try:
            kyc_service = KYCWorkflowService()
            response = kyc_service.update_workflow_step(str(user.id), step, status, data)
            
            return UpdateKYCStep(
                success=True,
                message=f"Step {step} updated to {status}"
            )
            
        except Exception as e:
            logger.error(f"Failed to update KYC step: {e}")
            return UpdateKYCStep(
                success=False,
                message=f"Failed to update step: {str(e)}"
            )

class CompleteKYCWorkflow(graphene.Mutation):
    """Complete KYC workflow"""
    
    class Arguments:
        workflow_type = graphene.String(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    next_steps = graphene.List(graphene.String)
    
    def mutate(self, info, workflow_type):
        user = info.context.user
        if not user.is_authenticated:
            return CompleteKYCWorkflow(
                success=False,
                message="Authentication required"
            )
        
        try:
            kyc_service = KYCWorkflowService()
            response = kyc_service.complete_kyc_workflow(str(user.id), workflow_type)
            
            return CompleteKYCWorkflow(
                success=True,
                message=f"KYC workflow completed for {workflow_type}",
                next_steps=response.get('next_steps', [])
            )
            
        except Exception as e:
            logger.error(f"Failed to complete KYC workflow: {e}")
            return CompleteKYCWorkflow(
                success=False,
                message=f"Failed to complete workflow: {str(e)}"
            )

# =============================================================================
# QUERIES
# =============================================================================

class KYCQuery(graphene.ObjectType):
    """KYC-related queries"""
    
    kyc_status = graphene.Field(KYCStatusType, account_id=graphene.String())
    account_status = graphene.Field(AccountStatusType, account_id=graphene.String())
    compliance_status = graphene.Field(ComplianceStatusType, account_id=graphene.String())
    kyc_documents = graphene.List(graphene.JSONString, account_id=graphene.String())
    account_activities = graphene.List(graphene.JSONString, account_id=graphene.String(), activity_type=graphene.String())
    
    def resolve_kyc_status(self, info, account_id):
        user = info.context.user
        if not user.is_authenticated:
            return None
        
        try:
            kyc_service = KYCWorkflowService()
            status_data = kyc_service.get_kyc_status(account_id)
            
            return KYCStatusType(
                account_id=status_data.get('account_id'),
                status=status_data.get('status'),
                kyc_required=status_data.get('kyc_required'),
                documents_uploaded=status_data.get('documents_uploaded'),
                verification_status=status_data.get('verification_status'),
                last_updated=timezone.now()
            )
        except Exception as e:
            logger.error(f"Failed to get KYC status: {e}")
            return None
    
    def resolve_account_status(self, info, account_id):
        user = info.context.user
        if not user.is_authenticated:
            return None
        
        try:
            kyc_service = KYCWorkflowService()
            status_data = kyc_service.get_account_status(account_id)
            
            return AccountStatusType(
                account_id=status_data.get('account_id'),
                status=status_data.get('status'),
                trading_enabled=status_data.get('trading_enabled'),
                crypto_enabled=status_data.get('crypto_enabled'),
                buying_power=status_data.get('buying_power'),
                cash=status_data.get('cash'),
                portfolio_value=status_data.get('portfolio_value'),
                created_at=timezone.now(),
                updated_at=timezone.now()
            )
        except Exception as e:
            logger.error(f"Failed to get account status: {e}")
            return None
    
    def resolve_compliance_status(self, info, account_id):
        user = info.context.user
        if not user.is_authenticated:
            return None
        
        try:
            kyc_service = KYCWorkflowService()
            compliance_data = kyc_service.check_compliance_status(account_id)
            
            return ComplianceStatusType(
                account_id=compliance_data.get('account_id'),
                kyc_complete=compliance_data.get('kyc_complete'),
                aml_clear=compliance_data.get('aml_clear'),
                sanctions_clear=compliance_data.get('sanctions_clear'),
                risk_level=compliance_data.get('risk_level'),
                monitoring_active=compliance_data.get('monitoring_active'),
                last_review=compliance_data.get('last_review'),
                next_review=compliance_data.get('next_review')
            )
        except Exception as e:
            logger.error(f"Failed to get compliance status: {e}")
            return None
    
    def resolve_kyc_documents(self, info, account_id):
        user = info.context.user
        if not user.is_authenticated:
            return []
        
        try:
            kyc_service = KYCWorkflowService()
            documents = kyc_service.get_kyc_documents(account_id)
            return documents
        except Exception as e:
            logger.error(f"Failed to get KYC documents: {e}")
            return []
    
    def resolve_account_activities(self, info, account_id, activity_type=None):
        user = info.context.user
        if not user.is_authenticated:
            return []
        
        try:
            kyc_service = KYCWorkflowService()
            activities = kyc_service.get_account_activities(account_id, activity_type)
            return activities
        except Exception as e:
            logger.error(f"Failed to get account activities: {e}")
            return []

# =============================================================================
# MUTATION CLASS
# =============================================================================

class KYCMutation(graphene.ObjectType):
    """KYC-related mutations"""
    
    initiate_kyc_workflow = InitiateKYCWorkflow.Field()
    create_brokerage_account = CreateBrokerageAccount.Field()
    create_crypto_account = CreateCryptoAccount.Field()
    upload_kyc_document = UploadKYCDocument.Field()
    update_kyc_step = UpdateKYCStep.Field()
    complete_kyc_workflow = CompleteKYCWorkflow.Field()
