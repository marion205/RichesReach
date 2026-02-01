"""
No-Code Scanner Builder Service
Allows users to build custom stock scanners using drag-drop interface.
Similar to TrendSpider's visual scanner builder.
"""
import logging
from typing import Dict, List, Optional, Any
from django.db import models
from django.utils import timezone
import json

logger = logging.getLogger(__name__)


class ScannerFilter(models.Model):
    """Individual filter in a scanner"""
    scanner = models.ForeignKey('Scanner', on_delete=models.CASCADE, related_name='filters')
    filter_type = models.CharField(max_length=50)  # 'price', 'volume', 'rsi', 'macd', etc.
    operator = models.CharField(max_length=20)  # '>', '<', '>=', '<=', '==', 'between'
    value = models.JSONField()  # Filter value(s)
    order = models.IntegerField(default=0)  # Display order
    
    class Meta:
        ordering = ['order']
    
    def evaluate(self, stock_data: Dict[str, Any]) -> bool:
        """Evaluate if stock passes this filter"""
        try:
            stock_value = stock_data.get(self.filter_type)
            if stock_value is None:
                return False
            
            if self.operator == '>':
                return float(stock_value) > float(self.value)
            elif self.operator == '<':
                return float(stock_value) < float(self.value)
            elif self.operator == '>=':
                return float(stock_value) >= float(self.value)
            elif self.operator == '<=':
                return float(stock_value) <= float(self.value)
            elif self.operator == '==':
                return float(stock_value) == float(self.value)
            elif self.operator == 'between':
                min_val, max_val = self.value
                return float(min_val) <= float(stock_value) <= float(max_val)
            else:
                return False
        except Exception as e:
            logger.error(f"Error evaluating filter: {e}")
            return False


class Scanner(models.Model):
    """User-created stock scanner"""
    user = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='scanners')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    filters = models.ManyToManyField(ScannerFilter, related_name='scanners')
    sort_by = models.CharField(max_length=50, default='score')  # 'score', 'volume', 'price_change', etc.
    sort_direction = models.CharField(max_length=10, default='desc')  # 'asc' or 'desc'
    limit = models.IntegerField(default=20)  # Max results
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Sharing
    is_public = models.BooleanField(default=False)
    share_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    
    def run_scan(self, stocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run scanner on list of stocks"""
        results = []
        
        for stock in stocks:
            # Evaluate all filters
            passes = all(
                filter_obj.evaluate(stock)
                for filter_obj in self.filters.all()
            )
            
            if passes:
                results.append(stock)
        
        # Sort results
        reverse = self.sort_direction == 'desc'
        try:
            results.sort(key=lambda x: x.get(self.sort_by, 0), reverse=reverse)
        except:
            pass
        
        # Limit results
        return results[:self.limit]


class ScannerBuilderService:
    """
    Service for building and managing custom scanners.
    Provides no-code interface for creating filters.
    """
    
    AVAILABLE_FILTERS = {
        'price': {
            'name': 'Price',
            'type': 'number',
            'operators': ['>', '<', '>=', '<=', 'between']
        },
        'volume': {
            'name': 'Volume',
            'type': 'number',
            'operators': ['>', '<', '>=', '<=', 'between']
        },
        'rsi': {
            'name': 'RSI',
            'type': 'number',
            'operators': ['>', '<', '>=', '<=', 'between'],
            'default_range': (0, 100)
        },
        'macd': {
            'name': 'MACD',
            'type': 'number',
            'operators': ['>', '<', '>=', '<=']
        },
        'market_cap': {
            'name': 'Market Cap',
            'type': 'number',
            'operators': ['>', '<', '>=', '<=', 'between']
        },
        'pe_ratio': {
            'name': 'P/E Ratio',
            'type': 'number',
            'operators': ['>', '<', '>=', '<=', 'between']
        },
        'sector': {
            'name': 'Sector',
            'type': 'select',
            'operators': ['==']
        },
        'ml_score': {
            'name': 'ML Score',
            'type': 'number',
            'operators': ['>', '<', '>=', '<=', 'between'],
            'default_range': (0, 10)
        },
        'sentiment': {
            'name': 'Social Sentiment',
            'type': 'number',
            'operators': ['>', '<', '>=', '<=', 'between'],
            'default_range': (-1, 1)
        }
    }
    
    def create_scanner(
        self,
        user_id: int,
        name: str,
        filters: List[Dict[str, Any]],
        description: str = '',
        sort_by: str = 'score',
        sort_direction: str = 'desc',
        limit: int = 20
    ) -> Scanner:
        """Create a new scanner"""
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=user_id)
            
            scanner = Scanner.objects.create(
                user=user,
                name=name,
                description=description,
                sort_by=sort_by,
                sort_direction=sort_direction,
                limit=limit
            )
            
            # Create filters
            for i, filter_data in enumerate(filters):
                ScannerFilter.objects.create(
                    scanner=scanner,
                    filter_type=filter_data['type'],
                    operator=filter_data['operator'],
                    value=filter_data['value'],
                    order=i
                )
            
            logger.info(f"Created scanner '{name}' for user {user_id} with {len(filters)} filters")
            return scanner
            
        except Exception as e:
            logger.error(f"Error creating scanner: {e}")
            raise
    
    def get_available_filters(self) -> Dict[str, Any]:
        """Get list of available filters for UI"""
        return self.AVAILABLE_FILTERS
    
    def validate_filter(self, filter_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a filter configuration"""
        errors = []
        
        filter_type = filter_data.get('type')
        if filter_type not in self.AVAILABLE_FILTERS:
            errors.append(f"Unknown filter type: {filter_type}")
            return {'valid': False, 'errors': errors}
        
        filter_config = self.AVAILABLE_FILTERS[filter_type]
        operator = filter_data.get('operator')
        
        if operator not in filter_config['operators']:
            errors.append(f"Invalid operator '{operator}' for {filter_type}")
        
        value = filter_data.get('value')
        if filter_config['type'] == 'number':
            try:
                if operator == 'between':
                    if not isinstance(value, list) or len(value) != 2:
                        errors.append("Between operator requires [min, max] array")
                else:
                    float(value)
            except:
                errors.append(f"Invalid value for {filter_type}: {value}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }

