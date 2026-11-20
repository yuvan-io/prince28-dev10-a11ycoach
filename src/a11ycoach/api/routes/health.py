"""Health and readiness endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from a11ycoach.api.deps import get_store
from a11ycoach.store import RecordStore

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    """Confirm that the application is running."""
    return {"status": "ok"}


@router.get("/ready")
def readiness(
    store: RecordStore = Depends(get_store),
) -> dict[str, object]:
    """Report whether the record data has loaded."""
    if not store.ready:
        raise HTTPException(
            status_code=503,
            detail="Record data has not been loaded.",
        )

    return {
        "status": "ready",
        "checks": {"records_loaded": True},
    }
