"""Health check endpoint.

Every production service exposes one so orchestrators (Kubernetes) and monitors
(Prometheus, load balancers) can check "is this service alive?".
"""

from fastapi import APIRouter

router = APIRouter(tags=["system"])


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
