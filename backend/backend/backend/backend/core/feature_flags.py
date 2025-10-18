"""
Centralized Feature Flags System
Prevents mocks from sneaking into production builds
"""
import os
import re
from django.core.exceptions import ImproperlyConfigured
from typing import Tuple


def env_bool(name: str, default: bool = False) -> bool:
    """Parse environment variable as boolean"""
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "y", "on"}


def assert_no_mocks_in_prod(debug: bool, allow_list: Tuple[str, ...] = ()):
    """
    Hard fail if any mock is enabled in production
    Defense-in-depth against mock contamination
    """
    # Any env containing _MOCK=true will be caught
    pattern = re.compile(r".*_MOCK$")
    offenders = []
    
    for k, v in os.environ.items():
        if (pattern.match(k) and 
            v.strip().lower() in {"1", "true", "yes", "y", "on"} and 
            k not in allow_list):
            offenders.append(f"{k}={v}")
    
    if not debug and offenders:
        raise ImproperlyConfigured(
            f"🚨 MOCKS ENABLED IN PRODUCTION: {', '.join(offenders)}\n"
            f"Set these to false/0 or remove from environment for production deployment."
        )


def get_feature_flags():
    """Get all feature flags for debugging/monitoring"""
    flags = {}
    for k in os.environ.keys():
        if k.startswith('USE_') and k.endswith('_MOCK'):
            flags[k] = env_bool(k, False)
    return flags


def print_feature_flags_banner(debug: bool):
    """Print startup banner showing all feature flags"""
    if debug:
        print("[FLAGS] 🛠️  DEBUG=True (development mode)")
    else:
        print("[FLAGS] 🚀 DEBUG=False (production mode)")
    
    flags = get_feature_flags()
    if flags:
        print("[FLAGS] Mock Services Status:")
        for flag, enabled in sorted(flags.items()):
            status = "🔴 ENABLED" if enabled else "🟢 DISABLED"
            print(f"[FLAGS]   {flag}: {status}")
    else:
        print("[FLAGS] ✅ No mock flags found - all services using real data")
