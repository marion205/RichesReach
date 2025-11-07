# Generated migration for Family Sharing models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0017_auto_20250908_0125'),
    ]

    operations = [
        migrations.CreateModel(
            name='FamilyGroup',
            fields=[
                ('id', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('shared_orb_enabled', models.BooleanField(default=True)),
                ('shared_orb_net_worth', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('shared_orb_last_synced', models.DateTimeField(blank=True, null=True)),
                ('settings', models.JSONField(blank=True, default=dict)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='owned_family_groups', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'family_groups',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='FamilyMember',
            fields=[
                ('id', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('role', models.CharField(choices=[('owner', 'Owner'), ('member', 'Member'), ('teen', 'Teen')], default='member', max_length=20)),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                ('last_active', models.DateTimeField(blank=True, null=True)),
                ('permissions', models.JSONField(blank=True, default=dict)),
                ('family_group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='members', to='core.familygroup')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='family_memberships', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'family_members',
                'ordering': ['-joined_at'],
                'unique_together': {('family_group', 'user')},
            },
        ),
        migrations.CreateModel(
            name='FamilyInvite',
            fields=[
                ('id', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('email', models.EmailField(max_length=254)),
                ('role', models.CharField(default='member', max_length=20)),
                ('invite_code', models.CharField(max_length=50, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('accepted_at', models.DateTimeField(blank=True, null=True)),
                ('accepted_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='accepted_invites', to=settings.AUTH_USER_MODEL)),
                ('family_group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invites', to='core.familygroup')),
                ('invited_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_invites', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'family_invites',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='OrbSyncEvent',
            fields=[
                ('id', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('event_type', models.CharField(choices=[('gesture', 'Gesture'), ('update', 'Update'), ('view', 'View')], max_length=20)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('data', models.JSONField(blank=True, default=dict)),
                ('family_group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sync_events', to='core.familygroup')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orb_sync_events', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'orb_sync_events',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.AddIndex(
            model_name='orbsyncevent',
            index=models.Index(fields=['family_group', '-timestamp'], name='orb_sync_e_family__idx'),
        ),
        migrations.AddIndex(
            model_name='orbsyncevent',
            index=models.Index(fields=['user', '-timestamp'], name='orb_sync_e_user_id_idx'),
        ),
    ]

