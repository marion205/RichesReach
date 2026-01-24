# core/pii_scrubber.py
"""
PII (Personally Identifiable Information) Scrubbing Utility
Removes sensitive data before sending to external AI APIs.

This is critical for FinTech compliance and data privacy.
Implements the "FinTech Sandbox" security pattern.
"""
import re
import logging
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class PIIScrubber:
    """
    Scrubs PII from text and structured data before sending to AI APIs.
    
    Implements:
    - SSN detection and masking
    - Credit card number detection and masking
    - Full account number masking (partial reveal only)
    - Name detection and replacement
    - Email masking
    - Phone number masking
    - Address masking
    """
    
    # Patterns for PII detection
    SSN_PATTERN = re.compile(r'\b\d{3}-?\d{2}-?\d{4}\b')
    CREDIT_CARD_PATTERN = re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b')
    ACCOUNT_NUMBER_PATTERN = re.compile(r'\b\d{10,}\b')  # 10+ digit numbers (likely account numbers)
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    PHONE_PATTERN = re.compile(r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b')
    
    # Common name patterns (basic - can be enhanced with NER)
    COMMON_NAMES = [
        'john', 'jane', 'smith', 'johnson', 'williams', 'brown', 'jones',
        'garcia', 'miller', 'davis', 'rodriguez', 'martinez', 'hernandez',
        'lopez', 'wilson', 'anderson', 'thomas', 'taylor', 'moore'
    ]
    
    def __init__(self, enable_strict_mode: bool = True):
        """
        Initialize PII scrubber.
        
        Args:
            enable_strict_mode: If True, uses more aggressive scrubbing
        """
        self.strict_mode = enable_strict_mode
        self.scrubbed_count = 0
        self.scrubbed_types = {}
    
    def scrub_text(self, text: str, preserve_structure: bool = True) -> str:
        """
        Scrub PII from text string.
        
        Args:
            text: Input text to scrub
            preserve_structure: If True, replaces with placeholders. If False, removes entirely.
            
        Returns:
            Scrubbed text with PII masked or removed
        """
        if not text or not isinstance(text, str):
            return text
        
        scrubbed = text
        
        # SSN scrubbing
        ssn_matches = self.SSN_PATTERN.findall(scrubbed)
        if ssn_matches:
            self.scrubbed_count += len(ssn_matches)
            self.scrubbed_types['ssn'] = self.scrubbed_types.get('ssn', 0) + len(ssn_matches)
            if preserve_structure:
                scrubbed = self.SSN_PATTERN.sub('[SSN-REDACTED]', scrubbed)
            else:
                scrubbed = self.SSN_PATTERN.sub('', scrubbed)
        
        # Credit card scrubbing
        cc_matches = self.CREDIT_CARD_PATTERN.findall(scrubbed)
        if cc_matches:
            self.scrubbed_count += len(cc_matches)
            self.scrubbed_types['credit_card'] = self.scrubbed_types.get('credit_card', 0) + len(cc_matches)
            if preserve_structure:
                scrubbed = self.CREDIT_CARD_PATTERN.sub('[CARD-REDACTED]', scrubbed)
            else:
                scrubbed = self.CREDIT_CARD_PATTERN.sub('', scrubbed)
        
        # Account number scrubbing (10+ digits)
        account_matches = self.ACCOUNT_NUMBER_PATTERN.findall(scrubbed)
        if account_matches:
            # Filter out likely non-account numbers (dates, years, etc.)
            filtered = [m for m in account_matches if not self._is_likely_date_or_year(m)]
            if filtered:
                self.scrubbed_count += len(filtered)
                self.scrubbed_types['account_number'] = self.scrubbed_types.get('account_number', 0) + len(filtered)
                for match in filtered:
                    if preserve_structure:
                        # Show last 4 digits only (common practice)
                        masked = f"****{match[-4:]}" if len(match) >= 4 else "[ACCOUNT-REDACTED]"
                        scrubbed = scrubbed.replace(match, masked)
                    else:
                        scrubbed = scrubbed.replace(match, '[ACCOUNT-REDACTED]')
        
        # Email scrubbing
        email_matches = self.EMAIL_PATTERN.findall(scrubbed)
        if email_matches:
            self.scrubbed_count += len(email_matches)
            self.scrubbed_types['email'] = self.scrubbed_types.get('email', 0) + len(email_matches)
            if preserve_structure:
                scrubbed = self.EMAIL_PATTERN.sub('[EMAIL-REDACTED]', scrubbed)
            else:
                scrubbed = self.EMAIL_PATTERN.sub('', scrubbed)
        
        # Phone number scrubbing
        phone_matches = self.PHONE_PATTERN.findall(scrubbed)
        if phone_matches:
            self.scrubbed_count += len(phone_matches)
            self.scrubbed_types['phone'] = self.scrubbed_types.get('phone', 0) + len(phone_matches)
            if preserve_structure:
                scrubbed = self.PHONE_PATTERN.sub('[PHONE-REDACTED]', scrubbed)
            else:
                scrubbed = self.PHONE_PATTERN.sub('', scrubbed)
        
        # Name scrubbing (basic - can be enhanced with NER)
        if self.strict_mode:
            scrubbed = self._scrub_names(scrubbed, preserve_structure)
        
        return scrubbed.strip()
    
    def scrub_dict(self, data: Dict[str, Any], sensitive_keys: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Scrub PII from dictionary/JSON structure.
        
        Args:
            data: Dictionary to scrub
            sensitive_keys: List of keys that should always be scrubbed (e.g., ['ssn', 'account_number'])
            
        Returns:
            Scrubbed dictionary
        """
        if not isinstance(data, dict):
            return data
        
        sensitive_keys = sensitive_keys or ['ssn', 'social_security', 'account_number', 
                                           'account_id', 'credit_card', 'card_number',
                                           'email', 'phone', 'phone_number', 'address',
                                           'full_name', 'first_name', 'last_name']
        
        scrubbed = {}
        for key, value in data.items():
            key_lower = key.lower()
            
            # Always scrub known sensitive keys
            if any(sk in key_lower for sk in sensitive_keys):
                scrubbed[key] = '[REDACTED]'
                self.scrubbed_count += 1
                self.scrubbed_types[key_lower] = self.scrubbed_types.get(key_lower, 0) + 1
            elif isinstance(value, str):
                scrubbed[key] = self.scrub_text(value)
            elif isinstance(value, dict):
                scrubbed[key] = self.scrub_dict(value, sensitive_keys)
            elif isinstance(value, list):
                scrubbed[key] = self.scrub_list(value, sensitive_keys)
            else:
                scrubbed[key] = value
        
        return scrubbed
    
    def scrub_list(self, data: List[Any], sensitive_keys: Optional[List[str]] = None) -> List[Any]:
        """
        Scrub PII from list structure.
        
        Args:
            data: List to scrub
            sensitive_keys: List of keys that should always be scrubbed
            
        Returns:
            Scrubbed list
        """
        if not isinstance(data, list):
            return data
        
        return [self.scrub_dict(item, sensitive_keys) if isinstance(item, dict)
                else self.scrub_text(item) if isinstance(item, str)
                else item for item in data]
    
    def _is_likely_date_or_year(self, text: str) -> bool:
        """Check if a number string is likely a date or year, not an account number."""
        # Years (1900-2099)
        if len(text) == 4 and text.isdigit():
            year = int(text)
            if 1900 <= year <= 2099:
                return True
        
        # Common date patterns
        if len(text) == 8 and text.isdigit():
            # Could be YYYYMMDD or MMDDYYYY
            return True
        
        return False
    
    def _scrub_names(self, text: str, preserve_structure: bool) -> str:
        """
        Basic name scrubbing (can be enhanced with NER models).
        This is a simple heuristic - for production, consider using spaCy NER.
        """
        # This is a basic implementation
        # For production, use a proper NER model (spaCy, transformers, etc.)
        words = text.split()
        scrubbed_words = []
        
        for word in words:
            # Remove punctuation for matching
            clean_word = re.sub(r'[^\w]', '', word.lower())
            if clean_word in self.COMMON_NAMES and len(word) > 2:
                if preserve_structure:
                    scrubbed_words.append('[NAME-REDACTED]')
                else:
                    continue  # Skip the word
                self.scrubbed_count += 1
                self.scrubbed_types['name'] = self.scrubbed_types.get('name', 0) + 1
            else:
                scrubbed_words.append(word)
        
        return ' '.join(scrubbed_words)
    
    def get_scrubbing_stats(self) -> Dict[str, Any]:
        """Get statistics about scrubbing operations."""
        return {
            'total_scrubbed': self.scrubbed_count,
            'types_scrubbed': self.scrubbed_types.copy(),
            'strict_mode': self.strict_mode
        }
    
    def reset_stats(self):
        """Reset scrubbing statistics."""
        self.scrubbed_count = 0
        self.scrubbed_types = {}


# Singleton instance for reuse
_default_scrubber = PIIScrubber()


def scrub_pii(data: Union[str, Dict, List], **kwargs) -> Union[str, Dict, List]:
    """
    Convenience function to scrub PII from data.
    
    Args:
        data: Text, dict, or list to scrub
        **kwargs: Additional arguments passed to scrubber
        
    Returns:
        Scrubbed data
    """
    if isinstance(data, str):
        return _default_scrubber.scrub_text(data, **kwargs)
    elif isinstance(data, dict):
        return _default_scrubber.scrub_dict(data, **kwargs)
    elif isinstance(data, list):
        return _default_scrubber.scrub_list(data, **kwargs)
    else:
        return data

