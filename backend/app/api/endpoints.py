from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status, Path

from app.core.config import settings
from app.controllers.shortlist_controller import ShortlistController, get_shortlist_controller
from app.services.geoapify_service import (
    GeoapifyService,
    get_geoapify_service,
    InvalidZipCodeError,
    UnresolvedZipCodeError,
    GeoapifyServiceError,
)
from app.schemas.hotel import (
    HotelSearchResponse,
    HotelPlace,
    ShortlistCreateRequest,
    ShortlistResponse,
    GenericMessageResponse,
)

router = APIRouter(tags=["Hotel Discovery API"])

@router.get(
    "/hotels/search",
    response_model=HotelSearchResponse,
    summary="Search hotels by 5-digit U.S. ZIP code",
    description="Resolves U.S. ZIP code to a postcode location and retrieves hotels within 5 km of that point.",
)
async def search_hotels_by_zip(
    zip_code: str = Query(
        ...,
        description="Five-digit U.S. ZIP code including leading zeros (e.g. 90210, 02138)",
        examples=["90210", "02138", "10001", "01001"],
    ),
    geo_service: GeoapifyService = Depends(get_geoapify_service),
    db_controller: ShortlistController = Depends(get_shortlist_controller),
) -> HotelSearchResponse:
    try:
        shortlisted_ids = db_controller.get_shortlisted_ids()
        response = await geo_service.search_hotels_by_zip(
            zip_code=zip_code,
            shortlisted_ids=shortlisted_ids,
        )
        return response

    except InvalidZipCodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_type": "invalid_input",
                "message": str(exc),
                "zip_code": zip_code,
            },
        ) from exc

    except UnresolvedZipCodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_type": "unresolved_zip",
                "message": str(exc),
                "zip_code": zip_code,
            },
        ) from exc

    except GeoapifyServiceError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "error_type": "service_failure",
                "message": str(exc),
                "zip_code": zip_code,
            },
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_type": "service_failure",
                "message": f"Unexpected server error during search: {str(exc)}",
                "zip_code": zip_code,
            },
        ) from exc


@router.get(
    "/shortlist",
    response_model=ShortlistResponse,
    summary="Get persistent shortlist",
    description="Returns all traveler-saved hotels stored in SQLite.",
)
async def get_shortlist(
    db_controller: ShortlistController = Depends(get_shortlist_controller),
) -> ShortlistResponse:
    try:
        items = db_controller.get_shortlist()
        return ShortlistResponse(shortlist=items, total=len(items))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch shortlist: {str(exc)}",
        ) from exc


@router.post(
    "/shortlist",
    response_model=HotelPlace,
    status_code=status.HTTP_201_CREATED,
    summary="Save a hotel to shortlist",
    description="Persists a selected hotel to the SQLite shortlist database.",
)
async def add_to_shortlist(
    payload: ShortlistCreateRequest,
    db_controller: ShortlistController = Depends(get_shortlist_controller),
) -> HotelPlace:
    try:
        saved = db_controller.add_to_shortlist(payload)
        return saved
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add hotel to shortlist: {str(exc)}",
        ) from exc


@router.delete(
    "/shortlist/{place_id}",
    response_model=GenericMessageResponse,
    summary="Remove a hotel from shortlist",
    description="Deletes a hotel from SQLite shortlist by place_id.",
)
async def remove_from_shortlist(
    place_id: str = Path(..., description="Unique ID of the hotel to remove"),
    db_controller: ShortlistController = Depends(get_shortlist_controller),
) -> GenericMessageResponse:
    try:
        deleted = db_controller.remove_from_shortlist(place_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hotel with place_id '{place_id}' was not found in shortlist.",
            )
        return GenericMessageResponse(message=f"Hotel '{place_id}' removed from shortlist.", status="deleted")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove hotel from shortlist: {str(exc)}",
        ) from exc
