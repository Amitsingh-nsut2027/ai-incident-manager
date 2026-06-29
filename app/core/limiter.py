"""Rate limiter (Phase 21).

Limits requests per client IP to stop brute-force and denial-of-service abuse.
Endpoints opt in with @limiter.limit("5/minute"). Tests disable it via
limiter.enabled = False.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# key_func decides "who" a request is rate-limited against — here, the client IP.
limiter = Limiter(key_func=get_remote_address)
