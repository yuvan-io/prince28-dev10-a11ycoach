"""Document listing, searching, and retrieval endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query

from a11ycoach.api.deps import get_store
from a11ycoach.store import RecordStore

router = APIRouter(prefix="/v1/documents", tags=["documents"])


@router.get("")
def list_documents(
    q: str | None = Query(default=None, description="Search document records"),
    limit: int = Query(default=20, ge=1, description="Maximum number of results"),
    store: RecordStore = Depends(get_store),
) -> dict[str, object]:
    """List and search documents, with a result limit."""
    records = store.search(q)

    return {
        "total": len(records),
        "items": records[:limit],
    }


@router.get("/{document_id}")
def get_document(
    document_id: str,
    store: RecordStore = Depends(get_store),
) -> dict:
    """Retrieve one document by its ID."""
    record = store.get(document_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"No document with id '{document_id}'.",
        )

    return record
