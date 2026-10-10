

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.database.database import get_connection

router = APIRouter(prefix="/buses", tags=["Buses"])


class BusCreate(BaseModel):
    bus_number: str
    route_name: Optional[str] = None
    start_location: str
    end_location: str
    status: str = "active"


class BusUpdate(BaseModel):
    bus_number: Optional[str] = None
    route_name: Optional[str] = None
    start_location: Optional[str] = None
    end_location: Optional[str] = None
    status: Optional[str] = None


def make_route_name(start: str, end: str) -> str:
    return f"{start.strip()} to {end.strip()}"


@router.post("/")
def add_bus(bus: BusCreate):
    start = bus.start_location.strip()
    end = bus.end_location.strip()

    if not start or not end:
        raise HTTPException(
            status_code=400,
            detail="Start location and end location are required"
        )

    route_name = (
        bus.route_name.strip()
        if bus.route_name and bus.route_name.strip()
        else make_route_name(start, end)
    )

    try:
        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO buses
                    (bus_number, route_name, status,
                     start_location, end_location)
                VALUES (?, ?, ?, ?, ?)
                """,
                (bus.bus_number.strip(), route_name,
                 bus.status.strip(), start, end)
            )

            bus_id = cursor.lastrowid

        return {
            "message": "Bus added successfully",
            "id": bus_id,
            "bus_number": bus.bus_number.strip(),
            "route_name": route_name,
            "start_location": start,
            "end_location": end,
            "status": bus.status.strip()
        }

    except Exception as error:
        if "UNIQUE constraint failed" in str(error):
            raise HTTPException(
                status_code=409,
                detail="This bus number already exists"
            )
        raise HTTPException(status_code=500, detail=str(error))


@router.get("/")
def get_buses(
    start_location: Optional[str] = None,
    end_location: Optional[str] = None
):
    query = """
        SELECT id, bus_number, route_name, status,
               start_location, end_location
        FROM buses
        WHERE 1=1
    """
    parameters = []

    if start_location and start_location.strip():
        query += " AND LOWER(TRIM(start_location)) = LOWER(TRIM(?))"
        parameters.append(start_location.strip())

    if end_location and end_location.strip():
        query += " AND LOWER(TRIM(end_location)) = LOWER(TRIM(?))"
        parameters.append(end_location.strip())

    query += " ORDER BY id"

    with get_connection() as connection:
        rows = connection.execute(query, parameters).fetchall()

    return [dict(row) for row in rows]


@router.get("/{bus_id}")
def get_bus(bus_id: int):
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, bus_number, route_name, status,
                   start_location, end_location
            FROM buses
            WHERE id = ?
            """,
            (bus_id,)
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Bus not found")

    return dict(row)


@router.put("/{bus_id}")
def update_bus(bus_id: int, bus: BusUpdate):
    updates = bus.model_dump(exclude_unset=True)

    with get_connection() as connection:
        existing = connection.execute(
            "SELECT * FROM buses WHERE id = ?", (bus_id,)
        ).fetchone()

        if existing is None:
            raise HTTPException(status_code=404, detail="Bus not found")

        current = dict(existing)
        start = updates.get("start_location", current["start_location"])
        end = updates.get("end_location", current["end_location"])

        if start is not None:
            start = start.strip()
        if end is not None:
            end = end.strip()

        if not start or not end:
            raise HTTPException(
                status_code=400,
                detail="Start location and end location cannot be empty"
            )

        if "start_location" in updates or "end_location" in updates:
            updates["start_location"] = start
            updates["end_location"] = end
            updates["route_name"] = make_route_name(start, end)

        if "bus_number" in updates:
            updates["bus_number"] = updates["bus_number"].strip()

        if "status" in updates:
            updates["status"] = updates["status"].strip()

        if updates:
            assignments = ", ".join(f"{key} = ?" for key in updates)
            values = list(updates.values()) + [bus_id]

            try:
                connection.execute(
                    f"UPDATE buses SET {assignments} WHERE id = ?",
                    values
                )
            except Exception as error:
                if "UNIQUE constraint failed" in str(error):
                    raise HTTPException(
                        status_code=409,
                        detail="This bus number already exists"
                    )
                raise HTTPException(status_code=500, detail=str(error))

        updated = connection.execute(
            """
            SELECT id, bus_number, route_name, status,
                   start_location, end_location
            FROM buses WHERE id = ?
            """,
            (bus_id,)
        ).fetchone()

    return dict(updated)


@router.delete("/{bus_id}")
def delete_bus(bus_id: int):
    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM buses WHERE id = ?", (bus_id,)
        )

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Bus not found")

    return {"message": "Bus deleted successfully", "id": bus_id}
