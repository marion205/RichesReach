# Live Streaming URL patterns for RichesReach
from django.urls import path
from . import views_live_streaming

urlpatterns = [
    # Live Streams
    path('live-streams/', views_live_streaming.live_streams_list, name='live_streams_list'),
    path('live-streams/<uuid:stream_id>/', views_live_streaming.live_stream_detail, name='live_stream_detail'),
    path('live-streams/<uuid:stream_id>/start/', views_live_streaming.start_stream, name='start_stream'),
    path('live-streams/<uuid:stream_id>/end/', views_live_streaming.end_stream, name='end_stream'),
    
    # Stream Viewers
    path('live-streams/<uuid:stream_id>/join/', views_live_streaming.join_stream, name='join_stream'),
    path('live-streams/<uuid:stream_id>/leave/', views_live_streaming.leave_stream, name='leave_stream'),
    path('live-streams/<uuid:stream_id>/viewers/', views_live_streaming.stream_viewers, name='stream_viewers'),
    
    # Stream Messages
    path('live-streams/<uuid:stream_id>/messages/', views_live_streaming.stream_messages, name='stream_messages'),
    path('live-streams/<uuid:stream_id>/messages/send/', views_live_streaming.send_message, name='send_message'),
    
    # Stream Reactions
    path('live-streams/<uuid:stream_id>/reactions/', views_live_streaming.stream_reactions, name='stream_reactions'),
    path('live-streams/<uuid:stream_id>/reactions/send/', views_live_streaming.send_reaction, name='send_reaction'),
    
    # Stream Polls
    path('live-streams/<uuid:stream_id>/polls/', views_live_streaming.stream_polls, name='stream_polls'),
    path('live-streams/<uuid:stream_id>/polls/create/', views_live_streaming.create_poll, name='create_poll'),
    path('live-streams/<uuid:stream_id>/polls/<uuid:poll_id>/vote/', views_live_streaming.vote_poll, name='vote_poll'),
    
    # Q&A Sessions
    path('live-streams/<uuid:stream_id>/qa/start/', views_live_streaming.start_qa_session, name='start_qa_session'),
    path('live-streams/<uuid:stream_id>/qa/questions/', views_live_streaming.stream_questions, name='stream_questions'),
    path('live-streams/<uuid:stream_id>/qa/questions/submit/', views_live_streaming.submit_question, name='submit_question'),
    
    # Screen Sharing
    path('live-streams/<uuid:stream_id>/screen-share/start/', views_live_streaming.start_screen_share, name='start_screen_share'),
    path('live-streams/<uuid:stream_id>/screen-share/stop/', views_live_streaming.stop_screen_share, name='stop_screen_share'),
]
