# Generated migration for live streaming models
from django.db import migrations, models
import django.db.models.deletion
import uuid
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LiveStream',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True, null=True)),
                ('category', models.CharField(choices=[('market-analysis', 'Market Analysis'), ('portfolio-review', 'Portfolio Review'), ('qa', 'Q&A Session'), ('general', 'General Discussion')], default='general', max_length=20)),
                ('status', models.CharField(choices=[('scheduled', 'Scheduled'), ('live', 'Live'), ('ended', 'Ended'), ('cancelled', 'Cancelled')], default='scheduled', max_length=20)),
                ('stream_key', models.CharField(blank=True, max_length=100, unique=True)),
                ('rtmp_url', models.URLField(blank=True, null=True)),
                ('hls_url', models.URLField(blank=True, null=True)),
                ('scheduled_at', models.DateTimeField(blank=True, null=True)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('ended_at', models.DateTimeField(blank=True, null=True)),
                ('duration', models.DurationField(blank=True, null=True)),
                ('max_viewers', models.PositiveIntegerField(default=0)),
                ('total_viewers', models.PositiveIntegerField(default=0)),
                ('total_reactions', models.PositiveIntegerField(default=0)),
                ('total_messages', models.PositiveIntegerField(default=0)),
                ('is_public', models.BooleanField(default=True)),
                ('allow_chat', models.BooleanField(default=True)),
                ('allow_reactions', models.BooleanField(default=True)),
                ('allow_screen_share', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('circle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='live_streams', to='community.wealthcircle')),
                ('host', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hosted_streams', to='auth.user')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='StreamViewer',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                ('left_at', models.DateTimeField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('total_watch_time', models.DurationField(default=datetime.timedelta(0))),
                ('reactions_sent', models.PositiveIntegerField(default=0)),
                ('messages_sent', models.PositiveIntegerField(default=0)),
                ('stream', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='viewers', to='core.livestream')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stream_viewings', to='auth.user')),
            ],
            options={
                'unique_together': {('stream', 'user')},
            },
        ),
        migrations.CreateModel(
            name='StreamMessage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('message_type', models.CharField(choices=[('message', 'Chat Message'), ('system', 'System Message'), ('announcement', 'Announcement'), ('moderation', 'Moderation')], default='message', max_length=20)),
                ('content', models.TextField()),
                ('is_pinned', models.BooleanField(default=False)),
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('likes', models.PositiveIntegerField(default=0)),
                ('replies', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deleted_messages', to='auth.user')),
                ('stream', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='core.livestream')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stream_messages', to='auth.user')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='StreamReaction',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('reaction_type', models.CharField(choices=[('heart', '❤️ Heart'), ('fire', '🔥 Fire'), ('money', '💰 Money'), ('thumbs', '👍 Thumbs Up'), ('clap', '👏 Clap'), ('laugh', '😂 Laugh')], max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('stream', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reactions', to='core.livestream')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stream_reactions', to='auth.user')),
            ],
            options={
                'unique_together': {('stream', 'user', 'reaction_type')},
            },
        ),
        migrations.CreateModel(
            name='StreamPoll',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('question', models.TextField()),
                ('is_active', models.BooleanField(default=True)),
                ('is_multiple_choice', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('ended_at', models.DateTimeField(blank=True, null=True)),
                ('total_votes', models.PositiveIntegerField(default=0)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_polls', to='auth.user')),
                ('stream', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='polls', to='core.livestream')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PollOption',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('text', models.CharField(max_length=200)),
                ('votes', models.PositiveIntegerField(default=0)),
                ('order', models.PositiveIntegerField(default=0)),
                ('poll', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='options', to='core.streampoll')),
            ],
            options={
                'ordering': ['order'],
                'unique_together': {('poll', 'order')},
            },
        ),
        migrations.CreateModel(
            name='PollVote',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('option', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='votes', to='core.polloption')),
                ('poll', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='votes', to='core.streampoll')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='poll_votes', to='auth.user')),
            ],
            options={
                'unique_together': {('poll', 'user', 'option')},
            },
        ),
        migrations.CreateModel(
            name='QASession',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('ended_at', models.DateTimeField(blank=True, null=True)),
                ('stream', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='qa_sessions', to='core.livestream')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='QAQuestion',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('question', models.TextField()),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('answered', 'Answered'), ('dismissed', 'Dismissed')], default='pending', max_length=20)),
                ('answer', models.TextField(blank=True, null=True)),
                ('answered_at', models.DateTimeField(blank=True, null=True)),
                ('upvotes', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('answered_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='answered_questions', to='auth.user')),
                ('qa_session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='core.qasession')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='qa_questions', to='auth.user')),
            ],
            options={
                'ordering': ['-upvotes', 'created_at'],
            },
        ),
        migrations.CreateModel(
            name='ScreenShare',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('is_active', models.BooleanField(default=True)),
                ('share_type', models.CharField(default='screen', max_length=20)),
                ('title', models.CharField(blank=True, max_length=200)),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('ended_at', models.DateTimeField(blank=True, null=True)),
                ('stream', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='screen_shares', to='core.livestream')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='screen_shares', to='auth.user')),
            ],
            options={
                'ordering': ['-started_at'],
            },
        ),
        migrations.AddIndex(
            model_name='livestream',
            index=models.Index(fields=['status', 'created_at'], name='core_livest_status_4b8c8a_idx'),
        ),
        migrations.AddIndex(
            model_name='livestream',
            index=models.Index(fields=['circle', 'status'], name='core_livest_circle_8a9c8a_idx'),
        ),
        migrations.AddIndex(
            model_name='livestream',
            index=models.Index(fields=['host', 'status'], name='core_livest_host_9a8c8a_idx'),
        ),
        migrations.AddIndex(
            model_name='streamviewer',
            index=models.Index(fields=['stream', 'is_active'], name='core_stream_stream_8a9c8a_idx'),
        ),
        migrations.AddIndex(
            model_name='streamviewer',
            index=models.Index(fields=['user', 'joined_at'], name='core_stream_user_9a8c8a_idx'),
        ),
        migrations.AddIndex(
            model_name='streammessage',
            index=models.Index(fields=['stream', 'created_at'], name='core_stream_stream_8a9c8a_idx'),
        ),
        migrations.AddIndex(
            model_name='streammessage',
            index=models.Index(fields=['user', 'created_at'], name='core_stream_user_9a8c8a_idx'),
        ),
        migrations.AddIndex(
            model_name='streammessage',
            index=models.Index(fields=['message_type', 'created_at'], name='core_stream_messag_8a9c8a_idx'),
        ),
        migrations.AddIndex(
            model_name='streamreaction',
            index=models.Index(fields=['stream', 'created_at'], name='core_stream_stream_8a9c8a_idx'),
        ),
        migrations.AddIndex(
            model_name='streamreaction',
            index=models.Index(fields=['reaction_type', 'created_at'], name='core_stream_reacti_8a9c8a_idx'),
        ),
        migrations.AddIndex(
            model_name='streampoll',
            index=models.Index(fields=['stream', 'is_active'], name='core_streamp_stream_8a9c8a_idx'),
        ),
        migrations.AddIndex(
            model_name='streampoll',
            index=models.Index(fields=['created_at'], name='core_streamp_created_8a9c8a_idx'),
        ),
        migrations.AddIndex(
            model_name='pollvote',
            index=models.Index(fields=['poll', 'created_at'], name='core_pollvo_poll_8a9c8a_idx'),
        ),
        migrations.AddIndex(
            model_name='qaquestion',
            index=models.Index(fields=['qa_session', 'status'], name='core_qaques_qa_ses_8a9c8a_idx'),
        ),
        migrations.AddIndex(
            model_name='qaquestion',
            index=models.Index(fields=['user', 'created_at'], name='core_qaques_user_9a8c8a_idx'),
        ),
        migrations.AddIndex(
            model_name='screenshare',
            index=models.Index(fields=['stream', 'is_active'], name='core_screen_stream_8a9c8a_idx'),
        ),
    ]
