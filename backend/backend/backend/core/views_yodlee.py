"""
Yodlee Integration Views
Handles FastLink sessions, callbacks, and data fetching
"""
import json
import logging
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db import transaction
from django.conf import settings
from .yodlee_service import YodleeService, YodleeDataProcessor
from .models import BankLink, BankAccount

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def start_fastlink(request):
    """Create a FastLink session for bank account linking"""
    try:
        if not settings.USE_YODLEE:
            return JsonResponse({
                "error": "Yodlee integration is disabled",
                "message": "Bank linking is currently unavailable"
            }, status=503)
        
        yodlee_service = YodleeService()
        session_data = yodlee_service.create_fastlink_session(user_id=request.user.id)
        
        logger.info(f"Created FastLink session for user {request.user.id}")
        return JsonResponse(session_data)
        
    except Exception as e:
        logger.error(f"Failed to create FastLink session: {e}")
        return JsonResponse({
            "error": "Failed to create FastLink session",
            "message": str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def fastlink_callback(request):
    """Handle FastLink callback after bank account linking"""
    try:
        if not settings.USE_YODLEE:
            return JsonResponse({
                "error": "Yodlee integration is disabled",
                "message": "Bank linking is currently unavailable"
            }, status=503)
        
        # Parse callback data
        try:
            data = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return JsonResponse({
                "error": "Invalid JSON data",
                "message": "Request body must be valid JSON"
            }, status=400)
        
        # Validate required fields
        if "providerAccountId" not in data:
            return JsonResponse({
                "error": "Missing providerAccountId",
                "message": "providerAccountId is required"
            }, status=400)
        
        if "userId" not in data:
            return JsonResponse({
                "error": "Missing userId",
                "message": "userId is required"
            }, status=400)
        
        # Process the callback
        processor = YodleeDataProcessor()
        result = processor.process_fastlink_callback(
            user_id=data["userId"],
            callback_data=data
        )
        
        if result["success"]:
            logger.info(f"Successfully processed FastLink callback for user {data['userId']}")
            return JsonResponse({
                "success": True,
                "message": result["message"],
                "bankLinkId": result["bank_link"].id,
                "accountsCount": len(result["accounts"])
            })
        else:
            logger.error(f"Failed to process FastLink callback: {result['error']}")
            return JsonResponse({
                "success": False,
                "error": result["error"],
                "message": result["message"]
            }, status=500)
            
    except Exception as e:
        logger.error(f"FastLink callback error: {e}")
        return JsonResponse({
            "error": "Internal server error",
            "message": str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def fetch_accounts(request):
    """Fetch accounts for the authenticated user"""
    try:
        if not settings.USE_YODLEE:
            return JsonResponse({
                "error": "Yodlee integration is disabled",
                "message": "Bank linking is currently unavailable"
            }, status=503)
        
        # Get user's bank links
        bank_links = BankLink.objects.filter(user=request.user, status__in=['linked', 'active'])
        
        accounts_data = []
        for bank_link in bank_links:
            for account in bank_link.accounts.all():
                accounts_data.append({
                    "id": account.id,
                    "accountId": account.account_id,
                    "name": account.name,
                    "type": account.type,
                    "mask": account.mask,
                    "currency": account.currency,
                    "balance": float(account.balance) if account.balance else 0,
                    "availableBalance": float(account.available_balance) if account.available_balance else 0,
                    "institutionName": bank_link.institution_name,
                    "lastUpdated": account.last_updated.isoformat() if account.last_updated else None
                })
        
        return JsonResponse({
            "success": True,
            "accounts": accounts_data,
            "count": len(accounts_data)
        })
        
    except Exception as e:
        logger.error(f"Failed to fetch accounts: {e}")
        return JsonResponse({
            "error": "Failed to fetch accounts",
            "message": str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def refresh_account(request):
    """Refresh account data from Yodlee"""
    try:
        if not settings.USE_YODLEE:
            return JsonResponse({
                "error": "Yodlee integration is disabled",
                "message": "Bank linking is currently unavailable"
            }, status=503)
        
        # Parse request data
        try:
            data = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return JsonResponse({
                "error": "Invalid JSON data",
                "message": "Request body must be valid JSON"
            }, status=400)
        
        bank_link_id = data.get("bankLinkId")
        if not bank_link_id:
            return JsonResponse({
                "error": "Missing bankLinkId",
                "message": "bankLinkId is required"
            }, status=400)
        
        # Get bank link
        try:
            bank_link = BankLink.objects.get(id=bank_link_id, user=request.user)
        except BankLink.DoesNotExist:
            return JsonResponse({
                "error": "Bank link not found",
                "message": "The specified bank link does not exist"
            }, status=404)
        
        # Refresh account data
        processor = YodleeDataProcessor()
        success = processor.sync_account_data(bank_link)
        
        if success:
            return JsonResponse({
                "success": True,
                "message": "Account data refreshed successfully"
            })
        else:
            return JsonResponse({
                "success": False,
                "error": "Failed to refresh account data",
                "message": bank_link.error_message or "Unknown error occurred"
            }, status=500)
            
    except Exception as e:
        logger.error(f"Failed to refresh account: {e}")
        return JsonResponse({
            "error": "Failed to refresh account",
            "message": str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_transactions(request):
    """Get transactions for a specific account"""
    try:
        if not settings.USE_YODLEE:
            return JsonResponse({
                "error": "Yodlee integration is disabled",
                "message": "Bank linking is currently unavailable"
            }, status=503)
        
        account_id = request.GET.get("accountId")
        if not account_id:
            return JsonResponse({
                "error": "Missing accountId",
                "message": "accountId parameter is required"
            }, status=400)
        
        # Get account
        try:
            account = BankAccount.objects.get(id=account_id, link__user=request.user)
        except BankAccount.DoesNotExist:
            return JsonResponse({
                "error": "Account not found",
                "message": "The specified account does not exist"
            }, status=404)
        
        # Get transactions from database
        transactions = account.transactions.all()[:100]  # Limit to 100 most recent
        
        transactions_data = []
        for transaction in transactions:
            transactions_data.append({
                "id": transaction.id,
                "transactionId": transaction.transaction_id,
                "amount": float(transaction.amount),
                "description": transaction.description,
                "merchantName": transaction.merchant_name,
                "category": transaction.category,
                "subcategory": transaction.subcategory,
                "date": transaction.date.isoformat(),
                "postDate": transaction.post_date.isoformat() if transaction.post_date else None,
                "type": transaction.type,
                "status": transaction.status
            })
        
        return JsonResponse({
            "success": True,
            "transactions": transactions_data,
            "count": len(transactions_data)
        })
        
    except Exception as e:
        logger.error(f"Failed to get transactions: {e}")
        return JsonResponse({
            "error": "Failed to get transactions",
            "message": str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def yodlee_webhook(request):
    """Handle Yodlee webhook events"""
    try:
        if not settings.USE_YODLEE:
            return JsonResponse({
                "error": "Yodlee integration is disabled",
                "message": "Webhook processing is currently unavailable"
            }, status=503)
        
        # Parse webhook data
        try:
            event_data = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return JsonResponse({
                "error": "Invalid JSON data",
                "message": "Request body must be valid JSON"
            }, status=400)
        
        event_type = event_data.get("eventType")
        logger.info(f"Received Yodlee webhook: {event_type}")
        
        # Handle different event types
        if event_type == "REFRESH_COMPLETED":
            # Account refresh completed - sync data
            provider_account_id = event_data.get("providerAccountId")
            if provider_account_id:
                try:
                    bank_link = BankLink.objects.get(provider_account_id=provider_account_id)
                    processor = YodleeDataProcessor()
                    processor.sync_account_data(bank_link)
                    logger.info(f"Synced data for provider account {provider_account_id}")
                except BankLink.DoesNotExist:
                    logger.warning(f"Bank link not found for provider account {provider_account_id}")
        
        elif event_type == "ACCOUNT_UPDATED":
            # Account data updated - sync data
            provider_account_id = event_data.get("providerAccountId")
            if provider_account_id:
                try:
                    bank_link = BankLink.objects.get(provider_account_id=provider_account_id)
                    processor = YodleeDataProcessor()
                    processor.sync_account_data(bank_link)
                    logger.info(f"Synced updated data for provider account {provider_account_id}")
                except BankLink.DoesNotExist:
                    logger.warning(f"Bank link not found for provider account {provider_account_id}")
        
        elif event_type == "TRANSACTION_DATA_AVAILABLE":
            # New transaction data available - could trigger transaction sync
            provider_account_id = event_data.get("providerAccountId")
            logger.info(f"Transaction data available for provider account {provider_account_id}")
        
        return JsonResponse({"success": True, "message": "Webhook processed successfully"})
        
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        return JsonResponse({
            "error": "Webhook processing failed",
            "message": str(e)
        }, status=500)


@login_required
@require_http_methods(["DELETE"])
def delete_bank_link(request, bank_link_id):
    """Delete a bank link and all associated data"""
    try:
        if not settings.USE_YODLEE:
            return JsonResponse({
                "error": "Yodlee integration is disabled",
                "message": "Bank linking is currently unavailable"
            }, status=503)
        
        # Get bank link
        try:
            bank_link = BankLink.objects.get(id=bank_link_id, user=request.user)
        except BankLink.DoesNotExist:
            return JsonResponse({
                "error": "Bank link not found",
                "message": "The specified bank link does not exist"
            }, status=404)
        
        # Delete from Yodlee (optional - depends on your requirements)
        try:
            yodlee_service = YodleeService()
            access_token = yodlee_service.get_access_token()
            yodlee_service.delete_provider_account(access_token, bank_link.provider_account_id)
        except Exception as e:
            logger.warning(f"Failed to delete from Yodlee: {e}")
        
        # Delete from database
        bank_link.delete()
        
        logger.info(f"Deleted bank link {bank_link_id} for user {request.user.id}")
        return JsonResponse({
            "success": True,
            "message": "Bank link deleted successfully"
        })
        
    except Exception as e:
        logger.error(f"Failed to delete bank link: {e}")
        return JsonResponse({
            "error": "Failed to delete bank link",
            "message": str(e)
        }, status=500)
