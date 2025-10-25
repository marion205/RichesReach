# Live Streaming Views for RichesReach
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Q, F
from django.core.paginator import Paginator
import json
import logging
from datetime import timedelta

from .models_live_streaming import (
    LiveStream, StreamViewer, StreamMessage, StreamReaction,
    StreamPoll, PollOption, PollVote, QASession, QAQuestion, ScreenShare
)
# from core.models import WealthCircle  # WealthCircle model doesn't exist yet

logger = logging.getLogger(__name__)

# ==================== LIVE STREAMS ====================

@csrf_exempt
@require_http_methods(["GET", "POST"])
def live_streams_list(request):
    """List all live streams or create a new one"""
    
    if request.method == "GET":
        # Get query parameters
        circle_id = request.GET.get('circle_id')
        category = request.GET.get('category')
        status = request.GET.get('status', 'live')
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 20))
        
        # Build query
        queryset = LiveStream.objects.select_related('host', 'circle')
        
        if circle_id:
            queryset = queryset.filter(circle_id=circle_id)
        if category:
            queryset = queryset.filter(category=category)
        if status:
            queryset = queryset.filter(status=status)
        
        # Pagination
        paginator = Paginator(queryset, limit)
        page_obj = paginator.get_page(page)
        
        streams_data = []
        for stream in page_obj:
            streams_data.append({
                'id': str(stream.id),
                'title': stream.title,
                'description': stream.description,
                'category': stream.category,
                'status': stream.status,
                'host': {
                    'id': stream.host.id,
                    'username': stream.host.username,
                    'first_name': stream.host.first_name,
                    'last_name': stream.host.last_name,
                },
                'circle': {
                    'id': stream.circle.id,
                    'name': stream.circle.name,
                },
                'viewer_count': stream.current_viewer_count,
                'max_viewers': stream.max_viewers,
                'total_reactions': stream.total_reactions,
                'total_messages': stream.total_messages,
                'started_at': stream.started_at.isoformat() if stream.started_at else None,
                'duration': str(stream.duration) if stream.duration else None,
                'is_public': stream.is_public,
                'allow_chat': stream.allow_chat,
                'allow_reactions': stream.allow_reactions,
                'allow_screen_share': stream.allow_screen_share,
                'created_at': stream.created_at.isoformat(),
            })
        
        return JsonResponse({
            'success': True,
            'data': streams_data,
            'pagination': {
                'page': page,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            }
        })
    
    elif request.method == "POST":
        # Create new live stream
        try:
            data = json.loads(request.body)
            
            # Validate required fields
            required_fields = ['title', 'circle_id', 'category']
            for field in required_fields:
                if field not in data:
                    return JsonResponse({
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }, status=400)
            
            # Get circle
            circle = get_object_or_404(WealthCircle, id=data['circle_id'])
            
            # Create stream
            stream = LiveStream.objects.create(
                host=request.user,
                circle=circle,
                title=data['title'],
                description=data.get('description', ''),
                category=data['category'],
                is_public=data.get('is_public', True),
                allow_chat=data.get('allow_chat', True),
                allow_reactions=data.get('allow_reactions', True),
                allow_screen_share=data.get('allow_screen_share', False),
            )
            
            logger.info(f"Created live stream: {stream.id} by {request.user.username}")
            
            return JsonResponse({
                'success': True,
                'data': {
                    'id': str(stream.id),
                    'title': stream.title,
                    'description': stream.description,
                    'category': stream.category,
                    'status': stream.status,
                    'stream_key': stream.stream_key,
                    'created_at': stream.created_at.isoformat(),
                }
            }, status=201)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f"Error creating live stream: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Failed to create live stream'
            }, status=500)


@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
def live_stream_detail(request, stream_id):
    """Get, update, or delete a specific live stream"""
    
    stream = get_object_or_404(LiveStream, id=stream_id)
    
    if request.method == "GET":
        # Get stream details
        return JsonResponse({
            'success': True,
            'data': {
                'id': str(stream.id),
                'title': stream.title,
                'description': stream.description,
                'category': stream.category,
                'status': stream.status,
                'host': {
                    'id': stream.host.id,
                    'username': stream.host.username,
                    'first_name': stream.host.first_name,
                    'last_name': stream.host.last_name,
                },
                'circle': {
                    'id': stream.circle.id,
                    'name': stream.circle.name,
                },
                'viewer_count': stream.current_viewer_count,
                'max_viewers': stream.max_viewers,
                'total_reactions': stream.total_reactions,
                'total_messages': stream.total_messages,
                'started_at': stream.started_at.isoformat() if stream.started_at else None,
                'ended_at': stream.ended_at.isoformat() if stream.ended_at else None,
                'duration': str(stream.duration) if stream.duration else None,
                'is_public': stream.is_public,
                'allow_chat': stream.allow_chat,
                'allow_reactions': stream.allow_reactions,
                'allow_screen_share': stream.allow_screen_share,
                'stream_urls': stream.get_stream_urls(),
                'created_at': stream.created_at.isoformat(),
                'updated_at': stream.updated_at.isoformat(),
            }
        })
    
    elif request.method == "PUT":
        # Update stream (only host can update)
        if stream.host != request.user:
            return JsonResponse({
                'success': False,
                'error': 'Only the host can update this stream'
            }, status=403)
        
        try:
            data = json.loads(request.body)
            
            # Update allowed fields
            if 'title' in data:
                stream.title = data['title']
            if 'description' in data:
                stream.description = data['description']
            if 'category' in data:
                stream.category = data['category']
            if 'is_public' in data:
                stream.is_public = data['is_public']
            if 'allow_chat' in data:
                stream.allow_chat = data['allow_chat']
            if 'allow_reactions' in data:
                stream.allow_reactions = data['allow_reactions']
            if 'allow_screen_share' in data:
                stream.allow_screen_share = data['allow_screen_share']
            
            stream.save()
            
            logger.info(f"Updated live stream: {stream.id}")
            
            return JsonResponse({
                'success': True,
                'data': {
                    'id': str(stream.id),
                    'title': stream.title,
                    'description': stream.description,
                    'category': stream.category,
                    'status': stream.status,
                    'updated_at': stream.updated_at.isoformat(),
                }
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f"Error updating live stream: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Failed to update live stream'
            }, status=500)
    
    elif request.method == "DELETE":
        # Delete stream (only host can delete)
        if stream.host != request.user:
            return JsonResponse({
                'success': False,
                'error': 'Only the host can delete this stream'
            }, status=403)
        
        stream.delete()
        logger.info(f"Deleted live stream: {stream_id}")
        
        return JsonResponse({
            'success': True,
            'message': 'Stream deleted successfully'
        })


@csrf_exempt
@require_http_methods(["POST"])
def start_stream(request, stream_id):
    """Start a live stream"""
    
    stream = get_object_or_404(LiveStream, id=stream_id)
    
    # Only host can start the stream
    if stream.host != request.user:
        return JsonResponse({
            'success': False,
            'error': 'Only the host can start this stream'
        }, status=403)
    
    # Check if stream is already live
    if stream.is_live:
        return JsonResponse({
            'success': False,
            'error': 'Stream is already live'
        }, status=400)
    
    # Start the stream
    stream.start_stream()
    
    logger.info(f"Started live stream: {stream.id}")
    
    return JsonResponse({
        'success': True,
        'data': {
            'id': str(stream.id),
            'status': stream.status,
            'started_at': stream.started_at.isoformat(),
            'stream_key': stream.stream_key,
            'stream_urls': stream.get_stream_urls(),
        }
    })


@csrf_exempt
@require_http_methods(["POST"])
def end_stream(request, stream_id):
    """End a live stream"""
    
    stream = get_object_or_404(LiveStream, id=stream_id)
    
    # Only host can end the stream
    if stream.host != request.user:
        return JsonResponse({
            'success': False,
            'error': 'Only the host can end this stream'
        }, status=403)
    
    # Check if stream is live
    if not stream.is_live:
        return JsonResponse({
            'success': False,
            'error': 'Stream is not currently live'
        }, status=400)
    
    # End the stream
    stream.end_stream()
    
    # Mark all active viewers as having left
    StreamViewer.objects.filter(stream=stream, is_active=True).update(
        is_active=False,
        left_at=timezone.now()
    )
    
    logger.info(f"Ended live stream: {stream.id}")
    
    return JsonResponse({
        'success': True,
        'data': {
            'id': str(stream.id),
            'status': stream.status,
            'ended_at': stream.ended_at.isoformat(),
            'duration': str(stream.duration),
        }
    })


# ==================== STREAM VIEWERS ====================

@csrf_exempt
@require_http_methods(["POST"])
def join_stream(request, stream_id):
    """Join a live stream as a viewer"""
    
    stream = get_object_or_404(LiveStream, id=stream_id)
    
    # Check if stream is live
    if not stream.is_live:
        return JsonResponse({
            'success': False,
            'error': 'Stream is not currently live'
        }, status=400)
    
    # Check if user is already viewing
    viewer, created = StreamViewer.objects.get_or_create(
        stream=stream,
        user=request.user,
        defaults={'is_active': True}
    )
    
    if not created:
        # User was already a viewer, reactivate
        viewer.is_active = True
        viewer.joined_at = timezone.now()
        viewer.left_at = None
        viewer.save()
    
    # Update stream viewer count
    current_count = stream.current_viewer_count
    if current_count > stream.max_viewers:
        stream.max_viewers = current_count
        stream.save()
    
    logger.info(f"User {request.user.username} joined stream {stream.id}")
    
    return JsonResponse({
        'success': True,
        'data': {
            'viewer_id': str(viewer.id),
            'stream_id': str(stream.id),
            'joined_at': viewer.joined_at.isoformat(),
            'viewer_count': current_count,
        }
    })


@csrf_exempt
@require_http_methods(["POST"])
def leave_stream(request, stream_id):
    """Leave a live stream"""
    
    stream = get_object_or_404(LiveStream, id=stream_id)
    
    try:
        viewer = StreamViewer.objects.get(stream=stream, user=request.user, is_active=True)
        viewer.leave_stream()
        
        logger.info(f"User {request.user.username} left stream {stream.id}")
        
        return JsonResponse({
            'success': True,
            'data': {
                'viewer_id': str(viewer.id),
                'stream_id': str(stream.id),
                'left_at': viewer.left_at.isoformat(),
                'watch_time': str(viewer.total_watch_time),
            }
        })
        
    except StreamViewer.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'User is not currently viewing this stream'
        }, status=400)


@require_http_methods(["GET"])
def stream_viewers(request, stream_id):
    """Get list of viewers for a stream"""
    
    stream = get_object_or_404(LiveStream, id=stream_id)
    page = int(request.GET.get('page', 1))
    limit = int(request.GET.get('limit', 50))
    
    viewers = StreamViewer.objects.filter(
        stream=stream,
        is_active=True
    ).select_related('user').order_by('-joined_at')
    
    paginator = Paginator(viewers, limit)
    page_obj = paginator.get_page(page)
    
    viewers_data = []
    for viewer in page_obj:
        viewers_data.append({
            'id': str(viewer.id),
            'user': {
                'id': viewer.user.id,
                'username': viewer.user.username,
                'first_name': viewer.user.first_name,
                'last_name': viewer.user.last_name,
            },
            'joined_at': viewer.joined_at.isoformat(),
            'reactions_sent': viewer.reactions_sent,
            'messages_sent': viewer.messages_sent,
        })
    
    return JsonResponse({
        'success': True,
        'data': viewers_data,
        'pagination': {
            'page': page,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        }
    })


# ==================== STREAM MESSAGES ====================

@require_http_methods(["GET"])
def stream_messages(request, stream_id):
    """Get chat messages for a stream"""
    
    stream = get_object_or_404(LiveStream, id=stream_id)
    page = int(request.GET.get('page', 1))
    limit = int(request.GET.get('limit', 50))
    
    messages = StreamMessage.objects.filter(
        stream=stream,
        is_deleted=False
    ).select_related('user').order_by('-created_at')
    
    paginator = Paginator(messages, limit)
    page_obj = paginator.get_page(page)
    
    messages_data = []
    for message in page_obj:
        messages_data.append({
            'id': str(message.id),
            'user': {
                'id': message.user.id,
                'username': message.user.username,
                'first_name': message.user.first_name,
                'last_name': message.user.last_name,
            },
            'message_type': message.message_type,
            'content': message.content,
            'is_pinned': message.is_pinned,
            'likes': message.likes,
            'replies': message.replies,
            'created_at': message.created_at.isoformat(),
        })
    
    return JsonResponse({
        'success': True,
        'data': messages_data,
        'pagination': {
            'page': page,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        }
    })


@csrf_exempt
@require_http_methods(["POST"])
def send_message(request, stream_id):
    """Send a chat message to a stream"""
    
    stream = get_object_or_404(LiveStream, id=stream_id)
    
    # Check if stream is live
    if not stream.is_live:
        return JsonResponse({
            'success': False,
            'error': 'Stream is not currently live'
        }, status=400)
    
    # Check if chat is allowed
    if not stream.allow_chat:
        return JsonResponse({
            'success': False,
            'error': 'Chat is disabled for this stream'
        }, status=400)
    
    # Check if user is viewing the stream
    try:
        viewer = StreamViewer.objects.get(stream=stream, user=request.user, is_active=True)
    except StreamViewer.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'You must be viewing the stream to send messages'
        }, status=400)
    
    try:
        data = json.loads(request.body)
        content = data.get('content', '').strip()
        
        if not content:
            return JsonResponse({
                'success': False,
                'error': 'Message content cannot be empty'
            }, status=400)
        
        # Create message
        message = StreamMessage.objects.create(
            stream=stream,
            user=request.user,
            message_type=data.get('message_type', 'message'),
            content=content
        )
        
        # Update viewer stats
        viewer.messages_sent += 1
        viewer.save()
        
        # Update stream stats
        stream.total_messages += 1
        stream.save()
        
        logger.info(f"Message sent to stream {stream.id} by {request.user.username}")
        
        return JsonResponse({
            'success': True,
            'data': {
                'id': str(message.id),
                'user': {
                    'id': message.user.id,
                    'username': message.user.username,
                    'first_name': message.user.first_name,
                    'last_name': message.user.last_name,
                },
                'message_type': message.message_type,
                'content': message.content,
                'created_at': message.created_at.isoformat(),
            }
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to send message'
        }, status=500)


# ==================== STREAM REACTIONS ====================

@csrf_exempt
@require_http_methods(["POST"])
def send_reaction(request, stream_id):
    """Send a reaction to a stream"""
    
    stream = get_object_or_404(LiveStream, id=stream_id)
    
    # Check if stream is live
    if not stream.is_live:
        return JsonResponse({
            'success': False,
            'error': 'Stream is not currently live'
        }, status=400)
    
    # Check if reactions are allowed
    if not stream.allow_reactions:
        return JsonResponse({
            'success': False,
            'error': 'Reactions are disabled for this stream'
        }, status=400)
    
    # Check if user is viewing the stream
    try:
        viewer = StreamViewer.objects.get(stream=stream, user=request.user, is_active=True)
    except StreamViewer.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'You must be viewing the stream to send reactions'
        }, status=400)
    
    try:
        data = json.loads(request.body)
        reaction_type = data.get('reaction_type')
        
        if not reaction_type:
            return JsonResponse({
                'success': False,
                'error': 'Reaction type is required'
            }, status=400)
        
        # Validate reaction type
        valid_types = [choice[0] for choice in StreamReaction.REACTION_TYPES]
        if reaction_type not in valid_types:
            return JsonResponse({
                'success': False,
                'error': f'Invalid reaction type. Valid types: {valid_types}'
            }, status=400)
        
        # Create or update reaction
        reaction, created = StreamReaction.objects.get_or_create(
            stream=stream,
            user=request.user,
            reaction_type=reaction_type,
            defaults={'created_at': timezone.now()}
        )
        
        if not created:
            # Update existing reaction timestamp
            reaction.created_at = timezone.now()
            reaction.save()
        
        # Update viewer stats
        if created:
            viewer.reactions_sent += 1
            viewer.save()
        
        # Update stream stats
        if created:
            stream.total_reactions += 1
            stream.save()
        
        logger.info(f"Reaction {reaction_type} sent to stream {stream.id} by {request.user.username}")
        
        return JsonResponse({
            'success': True,
            'data': {
                'id': str(reaction.id),
                'reaction_type': reaction.reaction_type,
                'user': {
                    'id': reaction.user.id,
                    'username': reaction.user.username,
                },
                'created_at': reaction.created_at.isoformat(),
            }
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error sending reaction: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to send reaction'
        }, status=500)


@require_http_methods(["GET"])
def stream_reactions(request, stream_id):
    """Get recent reactions for a stream"""
    
    stream = get_object_or_404(LiveStream, id=stream_id)
    limit = int(request.GET.get('limit', 100))
    
    # Get reactions from the last 5 minutes
    since = timezone.now() - timedelta(minutes=5)
    reactions = StreamReaction.objects.filter(
        stream=stream,
        created_at__gte=since
    ).select_related('user').order_by('-created_at')[:limit]
    
    reactions_data = []
    for reaction in reactions:
        reactions_data.append({
            'id': str(reaction.id),
            'reaction_type': reaction.reaction_type,
            'user': {
                'id': reaction.user.id,
                'username': reaction.user.username,
            },
            'created_at': reaction.created_at.isoformat(),
        })
    
    return JsonResponse({
        'success': True,
        'data': reactions_data,
    })


# ==================== STREAM POLLS ====================

@csrf_exempt
@require_http_methods(["POST"])
def create_poll(request, stream_id):
    """Create a poll for a stream"""
    
    stream = get_object_or_404(LiveStream, id=stream_id)
    
    # Only host can create polls
    if stream.host != request.user:
        return JsonResponse({
            'success': False,
            'error': 'Only the host can create polls'
        }, status=403)
    
    # Check if stream is live
    if not stream.is_live:
        return JsonResponse({
            'success': False,
            'error': 'Stream is not currently live'
        }, status=400)
    
    try:
        data = json.loads(request.body)
        question = data.get('question', '').strip()
        options = data.get('options', [])
        is_multiple_choice = data.get('is_multiple_choice', False)
        expires_in = data.get('expires_in')  # minutes
        
        if not question:
            return JsonResponse({
                'success': False,
                'error': 'Poll question is required'
            }, status=400)
        
        if len(options) < 2:
            return JsonResponse({
                'success': False,
                'error': 'At least 2 options are required'
            }, status=400)
        
        # Create poll
        poll = StreamPoll.objects.create(
            stream=stream,
            created_by=request.user,
            question=question,
            is_multiple_choice=is_multiple_choice,
        )
        
        # Set expiration if provided
        if expires_in:
            poll.expires_at = timezone.now() + timedelta(minutes=expires_in)
            poll.save()
        
        # Create poll options
        for i, option_text in enumerate(options):
            PollOption.objects.create(
                poll=poll,
                text=option_text.strip(),
                order=i
            )
        
        logger.info(f"Created poll for stream {stream.id}: {question}")
        
        return JsonResponse({
            'success': True,
            'data': {
                'id': str(poll.id),
                'question': poll.question,
                'is_multiple_choice': poll.is_multiple_choice,
                'is_active': poll.is_active,
                'expires_at': poll.expires_at.isoformat() if poll.expires_at else None,
                'created_at': poll.created_at.isoformat(),
            }
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error creating poll: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to create poll'
        }, status=500)


@require_http_methods(["GET"])
def stream_polls(request, stream_id):
    """Get active polls for a stream"""
    
    stream = get_object_or_404(LiveStream, id=stream_id)
    
    polls = StreamPoll.objects.filter(
        stream=stream,
        is_active=True
    ).prefetch_related('options').order_by('-created_at')
    
    polls_data = []
    for poll in polls:
        options_data = []
        for option in poll.options.all():
            options_data.append({
                'id': str(option.id),
                'text': option.text,
                'votes': option.votes,
                'order': option.order,
            })
        
        polls_data.append({
            'id': str(poll.id),
            'question': poll.question,
            'is_multiple_choice': poll.is_multiple_choice,
            'is_active': poll.is_active,
            'total_votes': poll.total_votes,
            'expires_at': poll.expires_at.isoformat() if poll.expires_at else None,
            'created_at': poll.created_at.isoformat(),
            'options': options_data,
        })
    
    return JsonResponse({
        'success': True,
        'data': polls_data,
    })


@csrf_exempt
@require_http_methods(["POST"])
def vote_poll(request, stream_id, poll_id):
    """Vote on a poll"""
    
    stream = get_object_or_404(LiveStream, id=stream_id)
    poll = get_object_or_404(StreamPoll, id=poll_id, stream=stream)
    
    # Check if poll is active
    if not poll.is_active:
        return JsonResponse({
            'success': False,
            'error': 'Poll is not active'
        }, status=400)
    
    # Check if poll has expired
    if poll.expires_at and poll.expires_at < timezone.now():
        return JsonResponse({
            'success': False,
            'error': 'Poll has expired'
        }, status=400)
    
    # Check if user is viewing the stream
    try:
        StreamViewer.objects.get(stream=stream, user=request.user, is_active=True)
    except StreamViewer.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'You must be viewing the stream to vote'
        }, status=400)
    
    try:
        data = json.loads(request.body)
        option_ids = data.get('option_ids', [])
        
        if not option_ids:
            return JsonResponse({
                'success': False,
                'error': 'At least one option must be selected'
            }, status=400)
        
        # Validate options belong to this poll
        valid_option_ids = list(poll.options.values_list('id', flat=True))
        for option_id in option_ids:
            if option_id not in valid_option_ids:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid option selected'
                }, status=400)
        
        # Check if user already voted (for single choice polls)
        if not poll.is_multiple_choice and len(option_ids) > 1:
            return JsonResponse({
                'success': False,
                'error': 'Only one option can be selected for this poll'
            }, status=400)
        
        # Check existing votes
        existing_votes = PollVote.objects.filter(poll=poll, user=request.user)
        if existing_votes.exists():
            return JsonResponse({
                'success': False,
                'error': 'You have already voted on this poll'
            }, status=400)
        
        # Create votes
        votes_created = []
        for option_id in option_ids:
            option = PollOption.objects.get(id=option_id, poll=poll)
            vote = PollVote.objects.create(
                poll=poll,
                user=request.user,
                option=option
            )
            votes_created.append(vote)
            
            # Update option vote count
            option.votes += 1
            option.save()
        
        # Update poll total votes
        poll.total_votes += len(votes_created)
        poll.save()
        
        logger.info(f"User {request.user.username} voted on poll {poll.id}")
        
        return JsonResponse({
            'success': True,
            'data': {
                'poll_id': str(poll.id),
                'votes_cast': len(votes_created),
                'total_votes': poll.total_votes,
            }
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error voting on poll: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to vote on poll'
        }, status=500)


# ==================== Q&A SESSIONS ====================

@csrf_exempt
@require_http_methods(["POST"])
def start_qa_session(request, stream_id):
    """Start a Q&A session for a stream"""
    
    stream = get_object_or_404(LiveStream, id=stream_id)
    
    # Only host can start Q&A
    if stream.host != request.user:
        return JsonResponse({
            'success': False,
            'error': 'Only the host can start Q&A sessions'
        }, status=403)
    
    # Check if stream is live
    if not stream.is_live:
        return JsonResponse({
            'success': False,
            'error': 'Stream is not currently live'
        }, status=400)
    
    # Check if Q&A is already active
    active_qa = QASession.objects.filter(stream=stream, is_active=True).first()
    if active_qa:
        return JsonResponse({
            'success': False,
            'error': 'Q&A session is already active'
        }, status=400)
    
    # Create Q&A session
    qa_session = QASession.objects.create(stream=stream)
    
    logger.info(f"Started Q&A session for stream {stream.id}")
    
    return JsonResponse({
        'success': True,
        'data': {
            'id': str(qa_session.id),
            'stream_id': str(stream.id),
            'is_active': qa_session.is_active,
            'created_at': qa_session.created_at.isoformat(),
        }
    }, status=201)


@csrf_exempt
@require_http_methods(["POST"])
def submit_question(request, stream_id):
    """Submit a question to the Q&A session"""
    
    stream = get_object_or_404(LiveStream, id=stream_id)
    
    # Check if stream is live
    if not stream.is_live:
        return JsonResponse({
            'success': False,
            'error': 'Stream is not currently live'
        }, status=400)
    
    # Check if Q&A is active
    qa_session = QASession.objects.filter(stream=stream, is_active=True).first()
    if not qa_session:
        return JsonResponse({
            'success': False,
            'error': 'No active Q&A session'
        }, status=400)
    
    # Check if user is viewing the stream
    try:
        StreamViewer.objects.get(stream=stream, user=request.user, is_active=True)
    except StreamViewer.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'You must be viewing the stream to submit questions'
        }, status=400)
    
    try:
        data = json.loads(request.body)
        question = data.get('question', '').strip()
        
        if not question:
            return JsonResponse({
                'success': False,
                'error': 'Question cannot be empty'
            }, status=400)
        
        # Create question
        qa_question = QAQuestion.objects.create(
            qa_session=qa_session,
            user=request.user,
            question=question
        )
        
        logger.info(f"Question submitted to stream {stream.id} by {request.user.username}")
        
        return JsonResponse({
            'success': True,
            'data': {
                'id': str(qa_question.id),
                'question': qa_question.question,
                'status': qa_question.status,
                'upvotes': qa_question.upvotes,
                'created_at': qa_question.created_at.isoformat(),
            }
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error submitting question: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to submit question'
        }, status=500)


@require_http_methods(["GET"])
def stream_questions(request, stream_id):
    """Get questions for a stream's Q&A session"""
    
    stream = get_object_or_404(LiveStream, id=stream_id)
    
    qa_session = QASession.objects.filter(stream=stream, is_active=True).first()
    if not qa_session:
        return JsonResponse({
            'success': True,
            'data': []
        })
    
    questions = QAQuestion.objects.filter(
        qa_session=qa_session
    ).select_related('user', 'answered_by').order_by('-upvotes', 'created_at')
    
    questions_data = []
    for question in questions:
        questions_data.append({
            'id': str(question.id),
            'user': {
                'id': question.user.id,
                'username': question.user.username,
                'first_name': question.user.first_name,
                'last_name': question.user.last_name,
            },
            'question': question.question,
            'status': question.status,
            'answer': question.answer,
            'answered_by': {
                'id': question.answered_by.id,
                'username': question.answered_by.username,
            } if question.answered_by else None,
            'answered_at': question.answered_at.isoformat() if question.answered_at else None,
            'upvotes': question.upvotes,
            'created_at': question.created_at.isoformat(),
        })
    
    return JsonResponse({
        'success': True,
        'data': questions_data,
    })


# ==================== SCREEN SHARING ====================

@csrf_exempt
@require_http_methods(["POST"])
def start_screen_share(request, stream_id):
    """Start screen sharing for a stream"""
    
    stream = get_object_or_404(LiveStream, id=stream_id)
    
    # Only host can start screen sharing
    if stream.host != request.user:
        return JsonResponse({
            'success': False,
            'error': 'Only the host can start screen sharing'
        }, status=403)
    
    # Check if stream is live
    if not stream.is_live:
        return JsonResponse({
            'success': False,
            'error': 'Stream is not currently live'
        }, status=400)
    
    # Check if screen sharing is allowed
    if not stream.allow_screen_share:
        return JsonResponse({
            'success': False,
            'error': 'Screen sharing is not enabled for this stream'
        }, status=400)
    
    # Check if screen sharing is already active
    active_share = ScreenShare.objects.filter(stream=stream, is_active=True).first()
    if active_share:
        return JsonResponse({
            'success': False,
            'error': 'Screen sharing is already active'
        }, status=400)
    
    try:
        data = json.loads(request.body)
        share_type = data.get('share_type', 'screen')
        title = data.get('title', '')
        
        # Create screen share
        screen_share = ScreenShare.objects.create(
            stream=stream,
            user=request.user,
            share_type=share_type,
            title=title
        )
        
        logger.info(f"Started screen sharing for stream {stream.id}")
        
        return JsonResponse({
            'success': True,
            'data': {
                'id': str(screen_share.id),
                'share_type': screen_share.share_type,
                'title': screen_share.title,
                'is_active': screen_share.is_active,
                'started_at': screen_share.started_at.isoformat(),
            }
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error starting screen share: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to start screen sharing'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def stop_screen_share(request, stream_id):
    """Stop screen sharing for a stream"""
    
    stream = get_object_or_404(LiveStream, id=stream_id)
    
    # Only host can stop screen sharing
    if stream.host != request.user:
        return JsonResponse({
            'success': False,
            'error': 'Only the host can stop screen sharing'
        }, status=403)
    
    # Find active screen share
    screen_share = ScreenShare.objects.filter(stream=stream, is_active=True).first()
    if not screen_share:
        return JsonResponse({
            'success': False,
            'error': 'No active screen sharing session'
        }, status=400)
    
    # Stop screen sharing
    screen_share.is_active = False
    screen_share.ended_at = timezone.now()
    screen_share.save()
    
    logger.info(f"Stopped screen sharing for stream {stream.id}")
    
    return JsonResponse({
        'success': True,
        'data': {
            'id': str(screen_share.id),
            'is_active': screen_share.is_active,
            'ended_at': screen_share.ended_at.isoformat(),
        }
    })
