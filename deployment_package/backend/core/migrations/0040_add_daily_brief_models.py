# Generated migration for Daily Brief models
from django.db import migrations, models
import django.db.models.deletion
import uuid
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0039_complianceautomation_supplychainvendor_accesspolicy_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='DailyBrief',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('market_summary', models.TextField(help_text='Plain English market update (30 sec)')),
                ('personalized_action', models.TextField(help_text='One personalized action (30 sec)')),
                ('action_type', models.CharField(choices=[('review_portfolio', 'Review Portfolio'), ('learn_lesson', 'Learn Lesson'), ('check_tax', 'Check Tax Opportunities'), ('rebalance', 'Rebalance Portfolio'), ('set_goal', 'Set Goal')], default='learn_lesson', max_length=50)),
                ('lesson_id', models.CharField(blank=True, help_text='ID of the 2-min lesson', max_length=100, null=True)),
                ('lesson_title', models.CharField(blank=True, max_length=200, null=True)),
                ('lesson_content', models.TextField(blank=True, help_text='2-minute lesson content', null=True)),
                ('experience_level', models.CharField(choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')], default='beginner', max_length=20)),
                ('goals_referenced', models.JSONField(default=list, help_text='List of user goals referenced')),
                ('is_completed', models.BooleanField(db_index=True, default=False)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('time_spent_seconds', models.IntegerField(blank=True, help_text='Time spent reading brief', null=True)),
                ('generated_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='daily_briefs', to='core.user')),
            ],
            options={
                'db_table': 'daily_briefs',
                'ordering': ['-date'],
            },
        ),
        migrations.CreateModel(
            name='UserStreak',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('current_streak', models.IntegerField(default=0, help_text='Current consecutive days')),
                ('longest_streak', models.IntegerField(default=0, help_text='Longest streak ever achieved')),
                ('last_completed_date', models.DateField(blank=True, help_text='Last date brief was completed', null=True)),
                ('streak_started_at', models.DateField(blank=True, help_text='When current streak started', null=True)),
                ('last_milestone_reached', models.IntegerField(default=0, help_text='Last milestone (3, 7, 30, etc.)')),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='streak', to='core.user')),
            ],
            options={
                'db_table': 'user_streaks',
            },
        ),
        migrations.CreateModel(
            name='UserProgress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('concepts_learned', models.IntegerField(default=0, help_text='Total concepts learned')),
                ('lessons_completed', models.IntegerField(default=0, help_text='Total lessons completed')),
                ('current_level', models.CharField(choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')], default='beginner', max_length=20)),
                ('weekly_briefs_completed', models.IntegerField(default=0, help_text='Briefs completed this week')),
                ('weekly_lessons_completed', models.IntegerField(default=0, help_text='Lessons completed this week')),
                ('weekly_goal', models.IntegerField(default=5, help_text='Weekly goal (default: 5 briefs)')),
                ('week_start_date', models.DateField(default=django.utils.timezone.now, help_text='Start of current week')),
                ('monthly_lessons_completed', models.IntegerField(default=0, help_text='Lessons completed this month')),
                ('monthly_goal', models.IntegerField(default=20, help_text='Monthly goal (default: 20 lessons)')),
                ('month_start_date', models.DateField(default=django.utils.timezone.now, help_text='Start of current month')),
                ('confidence_score', models.IntegerField(default=5, help_text='User confidence score (1-10)')),
                ('confidence_history', models.JSONField(default=list, help_text='Array of {date, score} objects for tracking confidence over time')),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='progress', to='core.user')),
            ],
            options={
                'db_table': 'user_progress',
            },
        ),
        migrations.CreateModel(
            name='UserAchievement',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('achievement_type', models.CharField(choices=[('early_bird', 'Early Bird'), ('consistent_learner', 'Consistent Learner'), ('first_investment', 'First Investment'), ('goal_setter', 'Goal Setter'), ('streak_3', '3 Day Streak'), ('streak_7', '7 Day Streak'), ('streak_30', '30 Day Streak'), ('lessons_10', '10 Lessons Learned'), ('lessons_50', '50 Lessons Learned')], max_length=50)),
                ('unlocked_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='achievements', to='core.user')),
            ],
            options={
                'db_table': 'user_achievements',
                'ordering': ['-unlocked_at'],
            },
        ),
        migrations.CreateModel(
            name='DailyBriefCompletion',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('time_spent_seconds', models.IntegerField(help_text='Time spent reading brief')),
                ('sections_viewed', models.JSONField(default=list, help_text="Which sections user viewed: ['market_summary', 'action', 'lesson']")),
                ('lesson_completed', models.BooleanField(default=False)),
                ('action_completed', models.BooleanField(default=False)),
                ('completed_at', models.DateTimeField(auto_now_add=True)),
                ('brief', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='completions', to='core.dailybrief')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='brief_completions', to='core.user')),
            ],
            options={
                'db_table': 'daily_brief_completions',
                'ordering': ['-completed_at'],
            },
        ),
        migrations.AddIndex(
            model_name='dailybrief',
            index=models.Index(fields=['user', 'date'], name='daily_brie_user_id_date_idx'),
        ),
        migrations.AddIndex(
            model_name='dailybrief',
            index=models.Index(fields=['user', 'is_completed'], name='daily_brie_user_id_is_com_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='dailybrief',
            unique_together={('user', 'date')},
        ),
        migrations.AlterUniqueTogether(
            name='userachievement',
            unique_together={('user', 'achievement_type')},
        ),
    ]

