from contextlib import contextmanager
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Generator

from app.core.config import settings
from app.models.db_models import CREATE_TABLES_SQL
from app.schemas.hotel import HotelPlace, ShortlistCreateRequest

class ShortlistController:
    """
    Controller responsible for persistent shortlist CRUD operations in SQLite.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or settings.DB_PATH

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def initialize_database(self) -> None:
        """Initialize the database schema."""
        with self.get_connection() as conn:
            conn.executescript(CREATE_TABLES_SQL)
            conn.commit()

    def get_shortlisted_ids(self) -> set[str]:
        """Return the set of all place_ids currently in the shortlist."""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT place_id FROM shortlist")
            return {row["place_id"] for row in cursor.fetchall()}

    def get_shortlist(self) -> list[HotelPlace]:
        """Fetch all saved places ordered by most recently saved."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT place_id, name, formatted_address, street, city, state, postcode,
                       latitude, longitude, distance_meters, category, website, phone,
                       saved_at
                FROM shortlist
                ORDER BY saved_at DESC
                """
            )
            places = []
            for row in cursor.fetchall():
                dist_m = row["distance_meters"]
                dist_km = round(dist_m / 1000.0, 2) if dist_m is not None else None
                places.append(
                    HotelPlace(
                        place_id=row["place_id"],
                        name=row["name"],
                        formatted_address=row["formatted_address"],
                        street=row["street"],
                        city=row["city"],
                        state=row["state"],
                        postcode=row["postcode"],
                        latitude=row["latitude"],
                        longitude=row["longitude"],
                        distance_meters=dist_m,
                        distance_km=dist_km,
                        category=row["category"],
                        website=row["website"],
                        phone=row["phone"],
                        is_shortlisted=True,
                    )
                )
            return places

    def add_to_shortlist(self, item: ShortlistCreateRequest) -> HotelPlace:
        """Add or update a place in the persistent shortlist."""
        now_iso = datetime.now(timezone.utc).isoformat()
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO shortlist (
                    place_id, name, formatted_address, street, city, state, postcode,
                    latitude, longitude, distance_meters, category, website, phone,
                    search_zip, saved_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(place_id) DO UPDATE SET
                    name=excluded.name,
                    formatted_address=excluded.formatted_address,
                    street=excluded.street,
                    city=excluded.city,
                    state=excluded.state,
                    postcode=excluded.postcode,
                    latitude=excluded.latitude,
                    longitude=excluded.longitude,
                    distance_meters=excluded.distance_meters,
                    category=excluded.category,
                    website=excluded.website,
                    phone=excluded.phone,
                    search_zip=excluded.search_zip,
                    saved_at=excluded.saved_at
                """,
                (
                    item.place_id,
                    item.name,
                    item.formatted_address,
                    item.street,
                    item.city,
                    item.state,
                    item.postcode,
                    item.latitude,
                    item.longitude,
                    item.distance_meters,
                    item.category,
                    item.website,
                    item.phone,
                    item.search_zip,
                    now_iso,
                ),
            )
            conn.commit()

        dist_km = round(item.distance_meters / 1000.0, 2) if item.distance_meters is not None else None
        return HotelPlace(
            place_id=item.place_id,
            name=item.name,
            formatted_address=item.formatted_address,
            street=item.street,
            city=item.city,
            state=item.state,
            postcode=item.postcode,
            latitude=item.latitude,
            longitude=item.longitude,
            distance_meters=item.distance_meters,
            distance_km=dist_km,
            category=item.category,
            website=item.website,
            phone=item.phone,
            is_shortlisted=True,
        )

    def remove_from_shortlist(self, place_id: str) -> bool:
        """Delete a place from the shortlist by place_id. Returns True if deleted, False if not found."""
        with self.get_connection() as conn:
            cursor = conn.execute("DELETE FROM shortlist WHERE place_id = ?", (place_id,))
            conn.commit()
            return cursor.rowcount > 0


_controller_instance: Optional[ShortlistController] = None

def get_shortlist_controller() -> ShortlistController:
    global _controller_instance
    if _controller_instance is None:
        _controller_instance = ShortlistController()
    return _controller_instance
