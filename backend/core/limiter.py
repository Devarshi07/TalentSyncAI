"""
Rate limiter — properly wired into the FastAPI app.
Uses slowapi with per-IP limiting.
"""
import config
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

rate_limit = f"{config.RATE_LIMIT_PER_MINUTE}/minute" if config.RATE_LIMIT_ENABLED else "10000/minute"
limiter = Limiter(key_func=get_remote_address, default_limits=[rate_limit])


def setup_rate_limiting(app):
    """Attach the rate limiter to the FastAPI app."""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
