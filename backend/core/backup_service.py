import os
import json
import logging
from datetime import datetime, timedelta
from django.conf import settings
from django.core.management import call_command
from django.core.files.storage import default_storage
from django.db import connection
from .models import User, Stock, Watchlist, Portfolio, StockDiscussion, DiscussionComment, Follow
import boto3
from botocore.exceptions import ClientError
logger = logging.getLogger(__name__)
class DataBackupService:
"""Service for backing up user data and ensuring data persistence"""
def __init__(self):
self.backup_dir = os.path.join(settings.BASE_DIR, 'backups')
self.ensure_backup_dir()
def ensure_backup_dir(self):
"""Ensure backup directory exists"""
if not os.path.exists(self.backup_dir):
os.makedirs(self.backup_dir)
def create_full_backup(self):
"""Create a full backup of all data"""
try:
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
backup_name = f'full_backup_{timestamp}'
logger.info(f"Starting full backup: {backup_name}")
# Create backup directory for this backup
backup_path = os.path.join(self.backup_dir, backup_name)
os.makedirs(backup_path, exist_ok=True)
# Backup database
self.backup_database(backup_path)
# Backup user data
self.backup_user_data(backup_path)
# Backup media files
self.backup_media_files(backup_path)
# Create backup manifest
self.create_backup_manifest(backup_path, backup_name)
logger.info(f"Full backup completed: {backup_name}")
return backup_name
except Exception as e:
logger.error(f"Error creating full backup: {e}")
raise
def backup_database(self, backup_path):
"""Backup database using Django's dumpdata command"""
try:
db_backup_path = os.path.join(backup_path, 'database.json')
# Use Django's dumpdata command
with open(db_backup_path, 'w') as f:
call_command('dumpdata', stdout=f, indent=2)
logger.info(f"Database backup created: {db_backup_path}")
except Exception as e:
logger.error(f"Error backing up database: {e}")
raise
def backup_user_data(self, backup_path):
"""Backup user-specific data"""
try:
users_data = []
for user in User.objects.all():
user_data = {
'id': user.id,
'email': user.email,
'name': user.name,
'created_at': user.created_at.isoformat(),
'last_login': user.last_login.isoformat() if user.last_login else None,
'watchlists': [],
'portfolios': [],
'discussions': [],
'follows': []
}
# Backup watchlists
for watchlist in user.watchlist_set.all():
user_data['watchlists'].append({
'id': watchlist.id,
'stock_symbol': watchlist.stock.symbol,
'created_at': watchlist.created_at.isoformat()
})
# Backup portfolios
for portfolio in user.portfolio_set.all():
user_data['portfolios'].append({
'id': portfolio.id,
'name': portfolio.name,
'total_value': float(portfolio.total_value),
'created_at': portfolio.created_at.isoformat()
})
# Backup discussions
for discussion in user.discussions.all():
user_data['discussions'].append({
'id': discussion.id,
'title': discussion.title,
'content': discussion.content,
'visibility': discussion.visibility,
'created_at': discussion.created_at.isoformat()
})
# Backup follows
for follow in user.following.all():
user_data['follows'].append({
'id': follow.id,
'following_user_id': follow.following.id,
'created_at': follow.created_at.isoformat()
})
users_data.append(user_data)
# Save user data to file
users_backup_path = os.path.join(backup_path, 'users_data.json')
with open(users_backup_path, 'w') as f:
json.dump(users_data, f, indent=2)
logger.info(f"User data backup created: {users_backup_path}")
except Exception as e:
logger.error(f"Error backing up user data: {e}")
raise
def backup_media_files(self, backup_path):
"""Backup media files (profile pictures, etc.)"""
try:
media_backup_path = os.path.join(backup_path, 'media')
os.makedirs(media_backup_path, exist_ok=True)
# Backup profile pictures
for user in User.objects.exclude(profile_pic__isnull=True).exclude(profile_pic=''):
if user.profile_pic:
try:
# Copy profile picture to backup
source_path = user.profile_pic.path
filename = os.path.basename(source_path)
dest_path = os.path.join(media_backup_path, f'user_{user.id}_{filename}')
with open(source_path, 'rb') as src, open(dest_path, 'wb') as dst:
dst.write(src.read())
except Exception as e:
logger.warning(f"Could not backup profile picture for user {user.id}: {e}")
logger.info(f"Media files backup created: {media_backup_path}")
except Exception as e:
logger.error(f"Error backing up media files: {e}")
raise
def create_backup_manifest(self, backup_path, backup_name):
"""Create a manifest file for the backup"""
try:
manifest = {
'backup_name': backup_name,
'created_at': datetime.now().isoformat(),
'backup_type': 'full',
'database_size': self.get_file_size(os.path.join(backup_path, 'database.json')),
'users_count': User.objects.count(),
'stocks_count': Stock.objects.count(),
'discussions_count': StockDiscussion.objects.count(),
'comments_count': DiscussionComment.objects.count(),
'files': []
}
# List all files in backup
for root, dirs, files in os.walk(backup_path):
for file in files:
file_path = os.path.join(root, file)
relative_path = os.path.relpath(file_path, backup_path)
manifest['files'].append({
'path': relative_path,
'size': os.path.getsize(file_path)
})
manifest_path = os.path.join(backup_path, 'manifest.json')
with open(manifest_path, 'w') as f:
json.dump(manifest, f, indent=2)
logger.info(f"Backup manifest created: {manifest_path}")
except Exception as e:
logger.error(f"Error creating backup manifest: {e}")
raise
def get_file_size(self, file_path):
"""Get file size in bytes"""
try:
return os.path.getsize(file_path)
except:
return 0
def cleanup_old_backups(self, days_to_keep=30):
"""Clean up old backup files"""
try:
cutoff_date = datetime.now() - timedelta(days=days_to_keep)
for item in os.listdir(self.backup_dir):
item_path = os.path.join(self.backup_dir, item)
if os.path.isdir(item_path):
# Check if backup is older than cutoff date
item_time = datetime.fromtimestamp(os.path.getctime(item_path))
if item_time < cutoff_date:
logger.info(f"Removing old backup: {item}")
import shutil
shutil.rmtree(item_path)
logger.info("Old backups cleanup completed")
except Exception as e:
logger.error(f"Error cleaning up old backups: {e}")
def restore_from_backup(self, backup_name):
"""Restore data from a backup"""
try:
backup_path = os.path.join(self.backup_dir, backup_name)
if not os.path.exists(backup_path):
raise ValueError(f"Backup not found: {backup_name}")
# Check manifest
manifest_path = os.path.join(backup_path, 'manifest.json')
if os.path.exists(manifest_path):
with open(manifest_path, 'r') as f:
manifest = json.load(f)
logger.info(f"Restoring from backup: {manifest['backup_name']}")
# Restore database
db_backup_path = os.path.join(backup_path, 'database.json')
if os.path.exists(db_backup_path):
with open(db_backup_path, 'r') as f:
call_command('loaddata', db_backup_path)
logger.info("Database restored successfully")
logger.info(f"Restore completed from backup: {backup_name}")
except Exception as e:
logger.error(f"Error restoring from backup: {e}")
raise
def verify_data_integrity(self):
"""Verify data integrity and consistency"""
try:
issues = []
# Check for orphaned records
orphaned_watchlists = Watchlist.objects.filter(stock__isnull=True)
if orphaned_watchlists.exists():
issues.append(f"Found {orphaned_watchlists.count()} orphaned watchlist items")
orphaned_comments = DiscussionComment.objects.filter(discussion__isnull=True)
if orphaned_comments.exists():
issues.append(f"Found {orphaned_comments.count()} orphaned comments")
# Check for duplicate follows
duplicate_follows = Follow.objects.values('follower', 'following').annotate(
count=models.Count('id')
).filter(count__gt=1)
if duplicate_follows.exists():
issues.append(f"Found {duplicate_follows.count()} duplicate follow relationships")
# Check for invalid data
invalid_users = User.objects.filter(email__isnull=True)
if invalid_users.exists():
issues.append(f"Found {invalid_users.count()} users without email")
if issues:
logger.warning(f"Data integrity issues found: {issues}")
return False, issues
else:
logger.info("Data integrity check passed")
return True, []
except Exception as e:
logger.error(f"Error verifying data integrity: {e}")
return False, [str(e)]
def get_backup_status(self):
"""Get status of all backups"""
try:
backups = []
for item in os.listdir(self.backup_dir):
item_path = os.path.join(self.backup_dir, item)
if os.path.isdir(item_path):
manifest_path = os.path.join(item_path, 'manifest.json')
if os.path.exists(manifest_path):
with open(manifest_path, 'r') as f:
manifest = json.load(f)
backups.append(manifest)
else:
# Legacy backup without manifest
backups.append({
'backup_name': item,
'created_at': datetime.fromtimestamp(os.path.getctime(item_path)).isoformat(),
'backup_type': 'legacy'
})
# Sort by creation date (newest first)
backups.sort(key=lambda x: x['created_at'], reverse=True)
return backups
except Exception as e:
logger.error(f"Error getting backup status: {e}")
return []
# Global instance
backup_service = DataBackupService()
