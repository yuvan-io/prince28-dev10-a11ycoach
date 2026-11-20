"""Shared dependencies for API routes."""

from fastapi import Request

from a11ycoach.store import RecordStore


def get_store(request: Request) -> RecordStore:
    """Get the record store belonging to this application."""
    return request.app.state.store
