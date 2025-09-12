"""
User Feedback Service for ML System
Integrates user preferences, feedback, and learning patterns
"""

import os
import logging
import json
import time
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)

class FeedbackType(Enum):
    """Types of user feedback"""
    PORTFOLIO_PREFERENCE = "portfolio_preference"
    RISK_ADJUSTMENT = "risk_adjustment"
    ESG_PREFERENCE = "esg_preference"
    ALGORITHM_FEEDBACK = "algorithm_feedback"
    PREDICTION_ACCURACY = "prediction_accuracy"
    USER_EXPERIENCE = "user_experience"
    FEATURE_REQUEST = "feature_request"
    BUG_REPORT = "bug_report"

class LearningPattern(Enum):
    """Types of learning patterns"""
    PORTFOLIO_CHANGES = "portfolio_changes"
    RISK_TOLERANCE_EVOLUTION = "risk_tolerance_evolution"
    GOAL_ADJUSTMENTS = "goal_adjustments"
    FEATURE_USAGE = "feature_usage"
    DECISION_PATTERNS = "decision_patterns"

class UserPreference(Enum):
    """Types of user preferences"""
    INVESTMENT_STYLE = "investment_style"
    ESG_FOCUS = "esg_focus"
    RISK_APPETITE = "risk_appetite"
    TIME_HORIZON = "time_horizon"
    ASSET_CLASS_PREFERENCE = "asset_class_preference"
    TRADING_FREQUENCY = "trading_frequency"

@dataclass
class UserFeedback:
    """User feedback data structure"""
    user_id: str
    feedback_type: FeedbackType
    content: str
    rating: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class UserPreferenceData:
    """User preference data structure"""
    user_id: str
    preference_type: UserPreference
    value: Any
    confidence: float = 1.0
    last_updated: datetime = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()

@dataclass
class LearningPatternData:
    """Learning pattern data structure"""
    user_id: str
    pattern_type: LearningPattern
    data: Dict[str, Any]
    frequency: int = 1
    first_seen: datetime = None
    last_seen: datetime = None
    
    def __post_init__(self):
        if self.first_seen is None:
            self.first_seen = datetime.now()
        if self.last_seen is None:
            self.last_seen = datetime.now()

class UserFeedbackService:
    """
    Service for managing user feedback, preferences, and learning patterns
    """
    
    def __init__(self, db_path: str = "user_feedback.db"):
        self.db_path = db_path
        self.preference_weights = {
            'recent': 0.4,      # Recent preferences have higher weight
            'frequency': 0.3,    # Frequently expressed preferences
            'confidence': 0.2,   # User confidence in preference
            'consistency': 0.1   # Consistency across time
        }
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize user feedback database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create user feedback table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    feedback_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    rating REAL,
                    metadata TEXT,
                    timestamp TEXT NOT NULL
                )
            ''')
            
            # Create user preferences table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    preference_type TEXT NOT NULL,
                    value TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    last_updated TEXT NOT NULL,
                    metadata TEXT
                )
            ''')
            
            # Create learning patterns table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    pattern_type TEXT NOT NULL,
                    data TEXT NOT NULL,
                    frequency INTEGER NOT NULL,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL
                )
            ''')
            
            # Create user profiles table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT UNIQUE NOT NULL,
                    profile_data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_updated TEXT NOT NULL
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_feedback_user ON user_feedback(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_feedback_type ON user_feedback(feedback_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_preferences_user ON user_preferences(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_patterns_user ON learning_patterns(user_id)')
            
            conn.commit()
            conn.close()
            
            logger.info("User feedback database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing user feedback database: {e}")
    
    def submit_feedback(self, user_id: str, feedback_type: FeedbackType, 
                       content: str, rating: Optional[float] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Submit user feedback
        
        Args:
            user_id: User identifier
            feedback_type: Type of feedback
            content: Feedback content
            rating: Optional rating (0-10)
            metadata: Additional metadata
            
        Returns:
            True if feedback submitted successfully
        """
        try:
            feedback = UserFeedback(
                user_id=user_id,
                feedback_type=feedback_type,
                content=content,
                rating=rating,
                metadata=metadata
            )
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO user_feedback (user_id, feedback_type, content, rating, metadata, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                feedback.user_id,
                feedback.feedback_type.value,
                feedback.content,
                feedback.rating,
                json.dumps(feedback.metadata) if feedback.metadata else None,
                feedback.timestamp.isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Feedback submitted for user {user_id}: {feedback_type.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error submitting feedback: {e}")
            return False
    
    def update_preference(self, user_id: str, preference_type: UserPreference,
                         value: Any, confidence: float = 1.0,
                         metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update user preference
        
        Args:
            user_id: User identifier
            preference_type: Type of preference
            value: Preference value
            confidence: User confidence (0-1)
            metadata: Additional metadata
            
        Returns:
            True if preference updated successfully
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if preference exists
            cursor.execute('''
                SELECT id FROM user_preferences 
                WHERE user_id = ? AND preference_type = ?
            ''', (user_id, preference_type.value))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing preference
                cursor.execute('''
                    UPDATE user_preferences 
                    SET value = ?, confidence = ?, last_updated = ?, metadata = ?
                    WHERE user_id = ? AND preference_type = ?
                ''', (
                    json.dumps(value),
                    confidence,
                    datetime.now().isoformat(),
                    json.dumps(metadata) if metadata else None,
                    user_id,
                    preference_type.value
                ))
            else:
                # Create new preference
                cursor.execute('''
                    INSERT INTO user_preferences (user_id, preference_type, value, confidence, last_updated, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    preference_type.value,
                    json.dumps(value),
                    confidence,
                    datetime.now().isoformat(),
                    json.dumps(metadata) if metadata else None
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Preference updated for user {user_id}: {preference_type.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating preference: {e}")
            return False
    
    def record_learning_pattern(self, user_id: str, pattern_type: LearningPattern,
                              data: Dict[str, Any]) -> bool:
        """
        Record a learning pattern
        
        Args:
            user_id: User identifier
            pattern_type: Type of pattern
            data: Pattern data
            frequency: Pattern frequency
            
        Returns:
            True if pattern recorded successfully
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if pattern exists
            cursor.execute('''
                SELECT id, frequency, data FROM learning_patterns 
                WHERE user_id = ? AND pattern_type = ?
            ''', (user_id, pattern_type.value))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing pattern
                pattern_id, current_freq, existing_data = existing
                
                # Merge data and increment frequency
                merged_data = json.loads(existing_data)
                merged_data.update(data)
                
                cursor.execute('''
                    UPDATE learning_patterns 
                    SET data = ?, frequency = ?, last_seen = ?
                    WHERE id = ?
                ''', (
                    json.dumps(merged_data),
                    current_freq + 1,
                    datetime.now().isoformat(),
                    pattern_id
                ))
            else:
                # Create new pattern
                cursor.execute('''
                    INSERT INTO learning_patterns (user_id, pattern_type, data, frequency, first_seen, last_seen)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    pattern_type.value,
                    json.dumps(data),
                    1,
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Learning pattern recorded for user {user_id}: {pattern_type.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error recording learning pattern: {e}")
            return False
    
    def get_user_preferences(self, user_id: str, 
                           preference_type: Optional[UserPreference] = None) -> List[UserPreferenceData]:
        """
        Get user preferences
        
        Args:
            user_id: User identifier
            preference_type: Optional filter by preference type
            
        Returns:
            List of user preferences
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if preference_type:
                cursor.execute('''
                    SELECT * FROM user_preferences 
                    WHERE user_id = ? AND preference_type = ?
                    ORDER BY last_updated DESC
                ''', (user_id, preference_type.value))
            else:
                cursor.execute('''
                    SELECT * FROM user_preferences 
                    WHERE user_id = ?
                    ORDER BY last_updated DESC
                ''', (user_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            preferences = []
            for row in rows:
                preference = UserPreferenceData(
                    user_id=row[1],
                    preference_type=UserPreference(row[2]),
                    value=json.loads(row[3]),
                    confidence=row[4],
                    last_updated=datetime.fromisoformat(row[5]),
                    metadata=json.loads(row[6]) if row[6] else None
                )
                preferences.append(preference)
            
            return preferences
            
        except Exception as e:
            logger.error(f"Error getting user preferences: {e}")
            return []
    
    def get_learning_patterns(self, user_id: str,
                            pattern_type: Optional[LearningPattern] = None) -> List[LearningPatternData]:
        """
        Get user learning patterns
        
        Args:
            user_id: User identifier
            pattern_type: Optional filter by pattern type
            
        Returns:
            List of learning patterns
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if pattern_type:
                cursor.execute('''
                    SELECT * FROM learning_patterns 
                    WHERE user_id = ? AND pattern_type = ?
                    ORDER BY last_seen DESC
                ''', (user_id, pattern_type.value))
            else:
                cursor.execute('''
                    SELECT * FROM learning_patterns 
                    WHERE user_id = ?
                    ORDER BY last_seen DESC
                ''', (user_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            patterns = []
            for row in rows:
                pattern = LearningPatternData(
                    user_id=row[1],
                    pattern_type=LearningPattern(row[2]),
                    data=json.loads(row[3]),
                    frequency=row[4],
                    first_seen=datetime.fromisoformat(row[5]),
                    last_seen=datetime.fromisoformat(row[6])
                )
                patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error getting learning patterns: {e}")
            return []
    
    def get_user_feedback(self, user_id: str,
                         feedback_type: Optional[FeedbackType] = None,
                         start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None) -> List[UserFeedback]:
        """
        Get user feedback
        
        Args:
            user_id: User identifier
            feedback_type: Optional filter by feedback type
            start_time: Start time filter
            end_time: End time filter
            
        Returns:
            List of user feedback
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = "SELECT * FROM user_feedback WHERE user_id = ?"
            params = [user_id]
            
            if feedback_type:
                query += " AND feedback_type = ?"
                params.append(feedback_type.value)
            
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time.isoformat())
            
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time.isoformat())
            
            query += " ORDER BY timestamp DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            feedback_list = []
            for row in rows:
                feedback = UserFeedback(
                    user_id=row[1],
                    feedback_type=FeedbackType(row[2]),
                    content=row[3],
                    rating=row[4],
                    metadata=json.loads(row[5]) if row[5] else None,
                    timestamp=datetime.fromisoformat(row[6])
                )
                feedback_list.append(feedback)
            
            return feedback_list
            
        except Exception as e:
            logger.error(f"Error getting user feedback: {e}")
            return []
    
    def get_preference_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive preference summary for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            Preference summary dictionary
        """
        try:
            preferences = self.get_user_preferences(user_id)
            patterns = self.get_learning_patterns(user_id)
            feedback = self.get_user_feedback(user_id)
            
            summary = {
                'user_id': user_id,
                'preferences': {},
                'learning_patterns': {},
                'feedback_summary': {},
                'last_updated': None
            }
            
            # Process preferences
            for pref in preferences:
                pref_type = pref.preference_type.value
                if pref_type not in summary['preferences']:
                    summary['preferences'][pref_type] = []
                
                summary['preferences'][pref_type].append({
                    'value': pref.value,
                    'confidence': pref.confidence,
                    'last_updated': pref.last_updated.isoformat()
                })
                
                if summary['last_updated'] is None or pref.last_updated > summary['last_updated']:
                    summary['last_updated'] = pref.last_updated
            
            # Process learning patterns
            for pattern in patterns:
                pattern_type = pattern.pattern_type.value
                if pattern_type not in summary['learning_patterns']:
                    summary['learning_patterns'][pattern_type] = []
                
                summary['learning_patterns'][pattern_type].append({
                    'data': pattern.data,
                    'frequency': pattern.frequency,
                    'first_seen': pattern.first_seen.isoformat(),
                    'last_seen': pattern.last_seen.isoformat()
                })
            
            # Process feedback
            if feedback:
                feedback_types = {}
                ratings = []
                
                for fb in feedback:
                    fb_type = fb.feedback_type.value
                    if fb_type not in feedback_types:
                        feedback_types[fb_type] = 0
                    feedback_types[fb_type] += 1
                    
                    if fb.rating is not None:
                        ratings.append(fb.rating)
                
                summary['feedback_summary'] = {
                    'total_feedback': len(feedback),
                    'feedback_types': feedback_types,
                    'average_rating': np.mean(ratings) if ratings else None,
                    'rating_count': len(ratings)
                }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting preference summary: {e}")
            return {'error': str(e)}
    
    def get_adaptive_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        Get adaptive preferences based on user behavior and feedback
        
        Args:
            user_id: User identifier
            
        Returns:
            Adaptive preferences dictionary
        """
        try:
            preferences = self.get_user_preferences(user_id)
            patterns = self.get_learning_patterns(user_id)
            feedback = self.get_user_feedback(user_id)
            
            adaptive_prefs = {}
            
            # Analyze portfolio changes pattern
            portfolio_patterns = [p for p in patterns if p.pattern_type == LearningPattern.PORTFOLIO_CHANGES]
            if portfolio_patterns:
                portfolio_data = portfolio_patterns[0].data
                adaptive_prefs['portfolio_behavior'] = {
                    'rebalancing_frequency': portfolio_data.get('rebalancing_frequency', 'monthly'),
                    'allocation_changes': portfolio_data.get('allocation_changes', 'moderate'),
                    'risk_adjustments': portfolio_data.get('risk_adjustments', 'conservative')
                }
            
            # Analyze risk tolerance evolution
            risk_patterns = [p for p in patterns if p.pattern_type == LearningPattern.RISK_TOLERANCE_EVOLUTION]
            if risk_patterns:
                risk_data = risk_patterns[0].data
                adaptive_prefs['risk_evolution'] = {
                    'initial_risk': risk_data.get('initial_risk', 'moderate'),
                    'current_risk': risk_data.get('current_risk', 'moderate'),
                    'risk_trend': risk_data.get('risk_trend', 'stable'),
                    'adjustment_frequency': risk_data.get('adjustment_frequency', 'low')
                }
            
            # Analyze ESG preferences
            esg_prefs = [p for p in preferences if p.preference_type == UserPreference.ESG_FOCUS]
            if esg_prefs:
                esg_data = esg_prefs[0]
                adaptive_prefs['esg_preferences'] = {
                    'focus_areas': esg_data.value.get('focus_areas', []),
                    'importance_level': esg_data.value.get('importance_level', 'medium'),
                    'exclusion_criteria': esg_data.value.get('exclusion_criteria', [])
                }
            
            # Analyze feedback sentiment
            if feedback:
                recent_feedback = [f for f in feedback if f.timestamp > datetime.now() - timedelta(days=30)]
                if recent_feedback:
                    ratings = [f.rating for f in recent_feedback if f.rating is not None]
                    if ratings:
                        avg_rating = np.mean(ratings)
                        adaptive_prefs['satisfaction'] = {
                            'recent_rating': avg_rating,
                            'rating_trend': 'improving' if avg_rating > 7.0 else 'stable' if avg_rating > 5.0 else 'declining',
                            'feedback_count': len(recent_feedback)
                        }
            
            return adaptive_prefs
            
        except Exception as e:
            logger.error(f"Error getting adaptive preferences: {e}")
            return {'error': str(e)}
    
    def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> bool:
        """
        Update user profile
        
        Args:
            user_id: User identifier
            profile_data: Profile data dictionary
            
        Returns:
            True if profile updated successfully
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if profile exists
            cursor.execute('SELECT id FROM user_profiles WHERE user_id = ?', (user_id,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing profile
                cursor.execute('''
                    UPDATE user_profiles 
                    SET profile_data = ?, last_updated = ?
                    WHERE user_id = ?
                ''', (
                    json.dumps(profile_data),
                    datetime.now().isoformat(),
                    user_id
                ))
            else:
                # Create new profile
                cursor.execute('''
                    INSERT INTO user_profiles (user_id, profile_data, created_at, last_updated)
                    VALUES (?, ?, ?, ?)
                ''', (
                    user_id,
                    json.dumps(profile_data),
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"User profile updated for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            return False
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile
        
        Args:
            user_id: User identifier
            
        Returns:
            User profile dictionary or None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT profile_data FROM user_profiles WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return json.loads(row[0])
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return None
    
    def export_user_data(self, user_id: str, filepath: str) -> bool:
        """
        Export user data to JSON file
        
        Args:
            user_id: User identifier
            filepath: Path to export file
            
        Returns:
            True if export successful
        """
        try:
            # Get all user data
            preferences = self.get_user_preferences(user_id)
            patterns = self.get_learning_patterns(user_id)
            feedback = self.get_user_feedback(user_id)
            profile = self.get_user_profile(user_id)
            
            # Prepare export data
            export_data = {
                'user_id': user_id,
                'export_timestamp': datetime.now().isoformat(),
                'preferences': [asdict(p) for p in preferences],
                'learning_patterns': [asdict(p) for p in patterns],
                'feedback': [asdict(f) for f in feedback],
                'profile': profile
            }
            
            # Convert datetime objects to strings
            for item in export_data['preferences']:
                if 'last_updated' in item and hasattr(item['last_updated'], 'isoformat'):
                    item['last_updated'] = item['last_updated'].isoformat()
            
            for item in export_data['learning_patterns']:
                if 'first_seen' in item and hasattr(item['first_seen'], 'isoformat'):
                    item['first_seen'] = item['first_seen'].isoformat()
                if 'last_seen' in item and hasattr(item['last_seen'], 'isoformat'):
                    item['last_seen'] = item['last_seen'].isoformat()
            
            for item in export_data['feedback']:
                if 'timestamp' in item and hasattr(item['timestamp'], 'isoformat'):
                    item['timestamp'] = item['timestamp'].isoformat()
            
            # Write to file
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"User data exported to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting user data: {e}")
            return False
    
    def get_system_insights(self) -> Dict[str, Any]:
        """
        Get system-wide insights from user data
        
        Returns:
            System insights dictionary
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            insights = {
                'total_users': 0,
                'total_feedback': 0,
                'total_preferences': 0,
                'popular_preferences': {},
                'feedback_sentiment': {},
                'learning_patterns': {}
            }
            
            # Get total counts
            cursor.execute('SELECT COUNT(DISTINCT user_id) FROM user_profiles')
            insights['total_users'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM user_feedback')
            insights['total_feedback'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM user_preferences')
            insights['total_preferences'] = cursor.fetchone()[0]
            
            # Get popular preferences
            cursor.execute('''
                SELECT preference_type, COUNT(*) as count
                FROM user_preferences
                GROUP BY preference_type
                ORDER BY count DESC
                LIMIT 5
            ''')
            
            for row in cursor.fetchall():
                insights['popular_preferences'][row[0]] = row[1]
            
            # Get feedback sentiment
            cursor.execute('''
                SELECT AVG(rating) as avg_rating, COUNT(*) as count
                FROM user_feedback
                WHERE rating IS NOT NULL
            ''')
            
            rating_data = cursor.fetchone()
            if rating_data[0]:
                insights['feedback_sentiment'] = {
                    'average_rating': rating_data[0],
                    'total_ratings': rating_data[1]
                }
            
            # Get learning pattern insights
            cursor.execute('''
                SELECT pattern_type, COUNT(*) as count
                FROM learning_patterns
                GROUP BY pattern_type
                ORDER BY count DESC
            ''')
            
            for row in cursor.fetchall():
                insights['learning_patterns'][row[0]] = row[1]
            
            conn.close()
            return insights
            
        except Exception as e:
            logger.error(f"Error getting system insights: {e}")
            return {'error': str(e)}
    
    def cleanup_old_data(self, days_to_keep: int = 365):
        """
        Clean up old user data
        
        Args:
            days_to_keep: Number of days of data to keep
        """
        try:
            cutoff_time = datetime.now() - timedelta(days=days_to_keep)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Delete old feedback
            cursor.execute('DELETE FROM user_feedback WHERE timestamp < ?', (cutoff_time.isoformat(),))
            feedback_deleted = cursor.rowcount
            
            # Delete old learning patterns
            cursor.execute('DELETE FROM learning_patterns WHERE last_seen < ?', (cutoff_time.isoformat(),))
            patterns_deleted = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            logger.info(f"Cleaned up old user data: {feedback_deleted} feedback, {patterns_deleted} patterns")
            
        except Exception as e:
            logger.error(f"Error cleaning up old user data: {e}")
