"""Vector store API routes for direct Qdrant operations."""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.vector import (
    DEFAULT_COLLECTION_NAME,
    count_points,
    delete_collection,
    delete_point,
    get_point,
    list_collections,
    recreate_collection,
    scroll,
    search,
    upsert_point,
    vector_store_health,
)

router = APIRouter(prefix="/api/v1/vectors", tags=["vectors"])


class PointUpsert(BaseModel):
    collection: str = DEFAULT_COLLECTION_NAME
    point_id: str
    text: str | None = None
    vector: list[float] | None = None
    payload: dict[str, Any] | None = None


class SearchRequest(BaseModel):
    collection: str = DEFAULT_COLLECTION_NAME
    query_text: str | None = None
    query_vector: list[float] | None = None
    filters: dict[str, Any] | None = None
    limit: int = 10
    score_threshold: float | None = None


class ScrollRequest(BaseModel):
    collection: str = DEFAULT_COLLECTION_NAME
    filters: dict[str, Any] | None = None
    limit: int = 100
    offset: str | None = None


@router.get("/health")
async def health():
    return await vector_store_health()


@router.get("/collections")
async def get_collections():
    return {"collections": await list_collections()}


@router.post("/collections/{name}/recreate")
async def recreate(name: str):
    await recreate_collection(name)
    return {"success": True, "collection": name}


@router.delete("/collections/{name}")
async def remove_collection(name: str):
    await delete_collection(name)
    return {"success": True, "collection": name}


@router.post("/points")
async def create_point(body: PointUpsert):
    pid = await upsert_point(
        collection=body.collection,
        point_id=body.point_id,
        vector=body.vector,
        payload=body.payload,
        text=body.text,
    )
    return {"success": True, "point_id": pid}


@router.get("/points/{point_id}")
async def read_point(point_id: str, collection: str = DEFAULT_COLLECTION_NAME):
    point = await get_point(collection, point_id)
    if point is None:
        raise HTTPException(status_code=404, detail=f"Point {point_id} not found")
    return {"success": True, "point": point}


@router.delete("/points/{point_id}")
async def remove_point(point_id: str, collection: str = DEFAULT_COLLECTION_NAME):
    await delete_point(collection, point_id)
    return {"success": True, "point_id": point_id}


@router.get("/count")
async def point_count(collection: str = DEFAULT_COLLECTION_NAME):
    count = await count_points(collection)
    return {"success": True, "count": count}


@router.post("/search")
async def search_points(body: SearchRequest):
    results = await search(
        collection=body.collection,
        query_text=body.query_text,
        query_vector=body.query_vector,
        filters=body.filters,
        limit=body.limit,
        score_threshold=body.score_threshold,
    )
    return {"success": True, "results": results}


@router.post("/scroll")
async def scroll_points(body: ScrollRequest):
    points, next_offset = await scroll(
        collection=body.collection,
        filters=body.filters,
        limit=body.limit,
        offset=body.offset,
    )
    return {
        "success": True,
        "points": points,
        "next_offset": next_offset,
    }
