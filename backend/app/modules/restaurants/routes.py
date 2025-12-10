"""
Restaurant API routes
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional

from app.core.database import get_db
from app.modules.restaurants.models import Restaurant, MenuItem
from app.modules.restaurants.schemas import (
    RestaurantResponse,
    RestaurantListResponse,
    MenuItemResponse,
    RestaurantCreate
)
from app.shared.schemas import success_response, error_response, paginated_response

router = APIRouter(prefix="/restaurants", tags=["Restaurants"])


@router.get("", response_model=dict)
async def get_restaurants(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    cuisine: Optional[str] = None,
    price_level: Optional[int] = Query(None, ge=1, le=4),
    rating: Optional[float] = Query(None, ge=0, le=5),
    sort_by: Optional[str] = Query("rating", regex="^(rating|price|name)$"),
    sort_order: Optional[str] = Query("desc", regex="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db)
):
    """Get list of restaurants with filters"""
    query = select(Restaurant).where(Restaurant.is_active == True)
    
    # Apply filters
    if search:
        query = query.where(
            or_(
                Restaurant.name.ilike(f"%{search}%"),
                Restaurant.description.ilike(f"%{search}%"),
                Restaurant.cuisine.ilike(f"%{search}%")
            )
        )
    
    if cuisine:
        query = query.where(Restaurant.cuisine.ilike(f"%{cuisine}%"))
    
    if price_level:
        query = query.where(Restaurant.price_level == price_level)
    
    if rating:
        query = query.where(Restaurant.rating >= rating)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply sorting
    if sort_by == "rating":
        order_col = Restaurant.rating
    elif sort_by == "price":
        order_col = Restaurant.price_level
    else:
        order_col = Restaurant.name
    
    if sort_order == "desc":
        query = query.order_by(order_col.desc())
    else:
        query = query.order_by(order_col.asc())
    
    # Apply pagination
    query = query.offset((page - 1) * limit).limit(limit)
    
    result = await db.execute(query)
    restaurants = result.scalars().all()
    
    return paginated_response(
        data=[RestaurantListResponse.model_validate(r).model_dump() for r in restaurants],
        total=total,
        page=page,
        limit=limit,
        message="Lấy danh sách nhà hàng thành công"
    )


@router.get("/search", response_model=dict)
async def search_restaurants(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Search restaurants by name, cuisine, or description"""
    query = select(Restaurant).where(
        Restaurant.is_active == True,
        or_(
            Restaurant.name.ilike(f"%{q}%"),
            Restaurant.description.ilike(f"%{q}%"),
            Restaurant.cuisine.ilike(f"%{q}%")
        )
    ).order_by(Restaurant.rating.desc()).limit(limit)
    
    result = await db.execute(query)
    restaurants = result.scalars().all()
    
    return success_response(
        data=[RestaurantListResponse.model_validate(r).model_dump() for r in restaurants],
        message="Tìm kiếm thành công"
    )


@router.get("/{restaurant_id}", response_model=dict)
async def get_restaurant(
    restaurant_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get restaurant detail by ID"""
    result = await db.execute(
        select(Restaurant).where(
            Restaurant.id == restaurant_id,
            Restaurant.is_active == True
        )
    )
    restaurant = result.scalar_one_or_none()
    
    if not restaurant:
        return error_response("E3002", "Không tìm thấy nhà hàng")
    
    # Get menu items
    menu_result = await db.execute(
        select(MenuItem).where(
            MenuItem.restaurant_id == restaurant_id,
            MenuItem.is_available == True
        ).order_by(MenuItem.category, MenuItem.name)
    )
    menu_items = menu_result.scalars().all()
    
    restaurant_data = RestaurantListResponse.model_validate(restaurant).model_dump()
    restaurant_data["menu"] = [MenuItemResponse.model_validate(m).model_dump() for m in menu_items]
    
    # Add location if available
    if restaurant.latitude and restaurant.longitude:
        restaurant_data["location"] = {
            "lat": restaurant.latitude,
            "lng": restaurant.longitude
        }
    
    return success_response(
        data=restaurant_data,
        message="Lấy thông tin nhà hàng thành công"
    )


@router.get("/{restaurant_id}/menu", response_model=dict)
async def get_restaurant_menu(
    restaurant_id: str,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get menu items for a restaurant"""
    # Check restaurant exists
    rest_result = await db.execute(
        select(Restaurant).where(Restaurant.id == restaurant_id)
    )
    if not rest_result.scalar_one_or_none():
        return error_response("E3002", "Không tìm thấy nhà hàng")
    
    query = select(MenuItem).where(
        MenuItem.restaurant_id == restaurant_id,
        MenuItem.is_available == True
    )
    
    if category:
        query = query.where(MenuItem.category.ilike(f"%{category}%"))
    
    query = query.order_by(MenuItem.category, MenuItem.name)
    
    result = await db.execute(query)
    menu_items = result.scalars().all()
    
    return success_response(
        data=[MenuItemResponse.model_validate(m).model_dump() for m in menu_items],
        message="Lấy menu thành công"
    )
