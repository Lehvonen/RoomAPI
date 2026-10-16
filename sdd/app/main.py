"""App factory. Only specific time-conversion errors become 422; there is no catch-all handler (research R5)."""

from dataclasses import replace

from fastapi import FastAPI

from .config import get_settings
from .db import init_db, make_engine, make_sessionmaker
from .routers import auth, bookings, rooms


def create_app(db_path: str | None = None) -> FastAPI:
    settings = get_settings()  # refuses to start without ROOMAPI_SECRET_KEY
    if db_path is not None:
        settings = replace(settings, db_path=db_path)

    engine = make_engine(settings.db_path)
    init_db(engine)

    app = FastAPI(
        title="Room Booking API (SDD)",
        version="0.1.0",
        description="Book meeting rooms. Built from specs/001-room-booking-api with Spec Kit.",
    )
    app.state.settings = settings
    app.state.engine = engine
    app.state.sessionmaker = make_sessionmaker(engine)

    app.include_router(auth.router)
    app.include_router(rooms.router)
    app.include_router(bookings.router)

    @app.get("/health", tags=["meta"])
    def health() -> dict[str, str]:
        """Unauthenticated health check (NFR-002)."""
        return {"status": "ok"}

    return app


def __getattr__(name: str):
    # `uvicorn app.main:app` builds the app on first access, so importing this
    # module (e.g. in tests) doesn't need ROOMAPI_SECRET_KEY.
    if name == "app":
        return create_app()
    raise AttributeError(name)
