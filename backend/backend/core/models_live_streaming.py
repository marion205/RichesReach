# Live Streaming Models for RichesReach
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()

class LiveStream(models.Model):
    """Model for live streaming sessions"""
    
    STREAM_CATEGORIES = [
        ('market-analysis', 'Market Analysis'),
        ('portfolio-review', 'Portfolio Review'),
        ('qa', 'Q&A Session'),
        ('general', 'General Discussion'),
    ]
    
    STREAM_STATUS = [
        ('scheduled', 'Scheduled'),
        ('live', 'Live'),
        ('ended', 'Ended'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hosted_streams')
    circle_id = models.IntegerField(null=True, blank=True)  # Reference to wealth circle ID
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=20, choices=STREAM_CATEGORIES, default='general')
    status = models.CharField(max_length=20, choices=STREAM_STATUS, default='scheduled')
    
    # Stream metadata
    stream_key = models.CharField(max_length=100, unique=True, blank=True)
    rtmp_url = models.URLField(blank=True, null=True)
    hls_url = models.URLField(blank=True, null=True)
    
    # Timing
    scheduled_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)
    
    # Analytics
    max_viewers = models.PositiveIntegerField(default=0)
    total_viewers = models.PositiveIntegerField(default=0)
    total_reactions = models.PositiveIntegerField(default=0)
    total_messages = models.PositiveIntegerField(default=0)
    
    # Settings
    is_public = models.BooleanField(default=True)
    allow_chat = models.BooleanField(default=True)
    allow_reactions = models.BooleanField(default=True)
    allow_screen_share = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['circle_id', 'status']),
            models.Index(fields=['host', 'status']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.host.username}"
    
    @property
    def is_live(self):
        return self.status == 'live'
    
    @property
    def current_viewer_count(self):
        return self.viewers.filter(is_active=True).count()
    
    def start_stream(self):
        """Start the live stream"""
        self.status = 'live'
        self.started_at = timezone.now()
        self.stream_key = f"stream_{self.id.hex[:12]}"
        self.save()
    
    def end_stream(self):
        """End the live stream"""
        self.status = 'ended'
        self.ended_at = timezone.now()
        if self.started_at:
            self.duration = self.ended_at - self.started_at
        self.save()
    
    def get_stream_urls(self):
        """Get streaming URLs for the stream"""
        base_url = "rtmp://your-streaming-server.com/live"
        return {
            'rtmp': f"{base_url}/{self.stream_key}",
            'hls': f"https://your-cdn.com/hls/{self.stream_key}.m3u8",
            'webrtc': f"wss://your-signaling-server.com/stream/{self.stream_key}"
        }


class StreamViewer(models.Model):
    """Model for tracking stream viewers"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stream = models.ForeignKey(LiveStream, on_delete=models.CASCADE, related_name='viewers')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stream_viewings')
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Viewer stats
    total_watch_time = models.DurationField(default=timezone.timedelta(0))
    reactions_sent = models.PositiveIntegerField(default=0)
    messages_sent = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ['stream', 'user']
        indexes = [
            models.Index(fields=['stream', 'is_active']),
            models.Index(fields=['user', 'joined_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} viewing {self.stream.title}"
    
    def leave_stream(self):
        """Mark viewer as having left the stream"""
        self.is_active = False
        self.left_at = timezone.now()
        if self.joined_at:
            self.total_watch_time = self.left_at - self.joined_at
        self.save()


class StreamMessage(models.Model):
    """Model for live stream chat messages"""
    
    MESSAGE_TYPES = [
        ('message', 'Chat Message'),
        ('system', 'System Message'),
        ('announcement', 'Announcement'),
        ('moderation', 'Moderation'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stream = models.ForeignKey(LiveStream, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stream_messages')
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='message')
    content = models.TextField()
    
    # Message metadata
    is_pinned = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='deleted_messages')
    
    # Engagement
    likes = models.PositiveIntegerField(default=0)
    replies = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['stream', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['message_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username}: {self.content[:50]}..."


class StreamReaction(models.Model):
    """Model for live stream reactions"""
    
    REACTION_TYPES = [
        ('heart', '❤️ Heart'),
        ('fire', '🔥 Fire'),
        ('money', '💰 Money'),
        ('thumbs', '👍 Thumbs Up'),
        ('clap', '👏 Clap'),
        ('laugh', '😂 Laugh'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stream = models.ForeignKey(LiveStream, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stream_reactions')
    reaction_type = models.CharField(max_length=20, choices=REACTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['stream', 'user', 'reaction_type']
        indexes = [
            models.Index(fields=['stream', 'created_at']),
            models.Index(fields=['reaction_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} reacted with {self.reaction_type}"


class StreamPoll(models.Model):
    """Model for live stream polls"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stream = models.ForeignKey(LiveStream, on_delete=models.CASCADE, related_name='polls')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_polls')
    question = models.TextField()
    is_active = models.BooleanField(default=True)
    is_multiple_choice = models.BooleanField(default=False)
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    # Results
    total_votes = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['stream', 'is_active']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Poll: {self.question[:50]}..."


class PollOption(models.Model):
    """Model for poll options"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    poll = models.ForeignKey(StreamPoll, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=200)
    vote_count = models.PositiveIntegerField(default=0)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
        unique_together = ['poll', 'order']
    
    def __str__(self):
        return f"{self.text} ({self.vote_count} votes)"


class PollVote(models.Model):
    """Model for poll votes"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    poll = models.ForeignKey(StreamPoll, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='poll_votes')
    option = models.ForeignKey(PollOption, on_delete=models.CASCADE, related_name='poll_votes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['poll', 'user', 'option']
        indexes = [
            models.Index(fields=['poll', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} voted for {self.option.text}"


class QASession(models.Model):
    """Model for Q&A sessions during live streams"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stream = models.ForeignKey(LiveStream, on_delete=models.CASCADE, related_name='qa_sessions')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Q&A for {self.stream.title}"


class QAQuestion(models.Model):
    """Model for Q&A questions"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('answered', 'Answered'),
        ('dismissed', 'Dismissed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    qa_session = models.ForeignKey(QASession, on_delete=models.CASCADE, related_name='questions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='qa_questions')
    question = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Answer
    answer = models.TextField(blank=True, null=True)
    answered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='answered_questions')
    answered_at = models.DateTimeField(null=True, blank=True)
    
    # Engagement
    upvotes = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-upvotes', 'created_at']
        indexes = [
            models.Index(fields=['qa_session', 'status']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"Q: {self.question[:50]}..."


class ScreenShare(models.Model):
    """Model for screen sharing sessions"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stream = models.ForeignKey(LiveStream, on_delete=models.CASCADE, related_name='screen_shares')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='screen_shares')
    is_active = models.BooleanField(default=True)
    
    # Screen share metadata
    share_type = models.CharField(max_length=20, default='screen')  # screen, window, tab
    title = models.CharField(max_length=200, blank=True)
    
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['stream', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.username} sharing {self.share_type}"
