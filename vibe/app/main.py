from contextlib import asynccontextmanager

from fastapi import FastAPI

from .db import db_path, init_db
from .routers import auth, bookings, rooms


def create_app(database_path: str | None = None) -> FastAPI:
    path = database_path or db_path()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        init_db(path)
        yield

    app = FastAPI(
        title="Room Booking API",
        version="0.1.0",
        description="Register, log in, browse rooms, check availability and book time slots.",
        lifespan=lifespan,
    )
    app.state.db_path = path
    app.include_router(auth.router)
    app.include_router(rooms.router)
    app.include_router(bookings.router)

    @app.get("/health", tags=["meta"])
    def health():
        return {"status": "ok"}

    return app


app = create_app()
