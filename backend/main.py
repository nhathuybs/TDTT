"""
Smart Travel System - FastAPI Backend
Main application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db, close_db
from app.modules.auth import router as auth_router
from app.modules.users import router as users_router
from app.modules.restaurants import router as restaurants_router
from app.modules.bookings import router as bookings_router
from app.modules.reviews import router as reviews_router
from app.modules.chat import router as chat_router
from app.modules.contact import router as contact_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    await init_db()
    print("✅ Database initialized")
    
    yield
    
    # Shutdown
    await close_db()
    print("👋 Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API for Smart Travel System - Restaurant booking and food discovery platform",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(restaurants_router, prefix="/api")
app.include_router(bookings_router, prefix="/api")
app.include_router(reviews_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(contact_router, prefix="/api")


# Health check endpoint
@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/api/debug/db-info")
async def debug_db_info():
    """Debug endpoint to check database info"""
    import sqlite3
    import os
    from app.core.database import DB_PATH, DATABASE_URL
    
    info = {
        "db_path": DB_PATH,
        "database_url": DATABASE_URL,
        "cwd": os.getcwd(),
        "db_exists": os.path.exists(DB_PATH),
        "db_size_mb": 0,
        "restaurants_total": 0,
        "restaurants_with_gcs_images": 0,
        "sample_images": []
    }
    
    if info["db_exists"]:
        info["db_size_mb"] = round(os.path.getsize(DB_PATH) / (1024 * 1024), 2)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM restaurants")
        info["restaurants_total"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM restaurants WHERE image LIKE '%storage.googleapis%'")
        info["restaurants_with_gcs_images"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT name, image FROM restaurants ORDER BY rating DESC LIMIT 3")
        info["sample_images"] = [{"name": r[0], "image": r[1][:80] if r[1] else None} for r in cursor.fetchall()]
        
        conn.close()
    
    return info


@app.post("/api/admin/migrate-db")
async def migrate_db():
    """Run database migrations to add new columns"""
    from sqlalchemy import text
    from app.core.database import AsyncSessionLocal, engine
    from app.core.config import settings
    
    async with AsyncSessionLocal() as session:
        try:
            # Check if using PostgreSQL
            if settings.CLOUD_SQL_CONNECTION_NAME:
                # PostgreSQL syntax - make user_id nullable
                await session.execute(text("""
                    ALTER TABLE reviews ADD COLUMN IF NOT EXISTS author_name VARCHAR(255)
                """))
                await session.execute(text("""
                    ALTER TABLE reviews ALTER COLUMN user_id DROP NOT NULL
                """))
            else:
                # SQLite - need to recreate table
                # First check if author_name exists
                result = await session.execute(text("PRAGMA table_info(reviews)"))
                columns = [row[1] for row in result.fetchall()]
                if 'author_name' not in columns:
                    # Drop and recreate table with new schema
                    await session.execute(text("DROP TABLE IF EXISTS reviews"))
            await session.commit()
            return {"success": True, "message": "Migration completed"}
        except Exception as e:
            return {"success": False, "error": str(e)}


@app.post("/api/admin/fix-encoding")
async def fix_encoding():
    """Fix UTF-8 encoding issues in database by re-importing from JSON"""
    import json
    from pathlib import Path
    from sqlalchemy import select, delete
    from app.core.database import AsyncSessionLocal
    from app.modules.restaurants.models import Restaurant
    from app.modules.reviews.models import Review
    
    json_path = Path(__file__).parent / "hcm_restaurants_with_local_images.json"
    if not json_path.exists():
        return {"error": "JSON file not found"}
    
    # Load JSON with proper encoding
    with open(json_path, "r", encoding="utf-8") as f:
        restaurants_data = json.load(f)
    
    # Create lookup dict by name
    json_lookup = {}
    for r in restaurants_data:
        name = r.get("name", "")
        if name:
            json_lookup[name] = r
    
    async with AsyncSessionLocal() as session:
        try:
            # Get all restaurants from DB
            result = await session.execute(select(Restaurant))
            db_restaurants = result.scalars().all()
            
            fixed_count = 0
            for db_rest in db_restaurants:
                # Try to find matching restaurant in JSON by comparing patterns
                found_json = None
                for json_name, json_data in json_lookup.items():
                    # Simple match - if DB name contains part of JSON name
                    if json_name and db_rest.name:
                        # Check if the JSON data has same phone or address
                        if json_data.get("phone") == db_rest.phone or json_data.get("address") == db_rest.address:
                            found_json = json_data
                            break
                
                if found_json:
                    # Update with correct UTF-8 data
                    db_rest.name = found_json.get("name", db_rest.name)[:255]
                    db_rest.cuisine = found_json.get("category", db_rest.cuisine)[:100] if found_json.get("category") else db_rest.cuisine
                    db_rest.address = found_json.get("address", db_rest.address)[:500] if found_json.get("address") else db_rest.address
                    db_rest.description = found_json.get("description", "")
                    
                    # Fix specialty
                    food_tags = found_json.get("food_tags") or found_json.get("specialty") or []
                    if isinstance(food_tags, list):
                        db_rest.specialty = food_tags
                    
                    fixed_count += 1
            
            await session.commit()
            return {"success": True, "fixed": fixed_count, "total": len(db_restaurants)}
        except Exception as e:
            await session.rollback()
            return {"success": False, "error": str(e)}


@app.post("/api/admin/seed-data")
async def seed_data(force: bool = False):
    """Seed database with sample restaurant data - only restaurants with images"""
    import json
    from pathlib import Path
    from sqlalchemy import select, func, delete, text
    from app.core.database import AsyncSessionLocal, Base, engine
    from app.modules.restaurants.models import Restaurant, MenuItem
    from app.modules.reviews.models import Review
    
    # Ensure all tables exist (including reviews with new schema)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSessionLocal() as session:
        # Check if data already exists
        result = await session.execute(select(func.count(Restaurant.id)))
        count = result.scalar()
        
        if count > 0 and not force:
            return {"message": f"Database already has {count} restaurants. Use ?force=true to reseed.", "seeded": False}
        
        # Clear existing data if force=true
        if force and count > 0:
            try:
                await session.execute(delete(Review))  # Delete reviews first (FK constraint)
            except Exception:
                pass  # Table might not exist
            await session.execute(delete(Restaurant))
            await session.commit()
        
        # Load JSON data
        json_path = Path(__file__).parent / "hcm_restaurants_with_local_images.json"
        if not json_path.exists():
            return {"error": "JSON file not found", "seeded": False}
        
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        restaurants_data = data if isinstance(data, list) else data.get("restaurants", [])
        
        # Load valid image names (restaurants that have images in GCS)
        valid_images_path = Path(__file__).parent / "valid_image_names.json"
        valid_image_names = set()
        if valid_images_path.exists():
            with open(valid_images_path, "r", encoding="utf-8-sig") as f:
                valid_image_names = set(json.load(f))
        
        # Helper to truncate strings
        def truncate(s, max_len):
            if s and len(s) > max_len:
                return s[:max_len]
            return s
        
        # Import only restaurants with matching images
        import random
        imported = 0
        skipped = 0
        errors = 0
        for r in restaurants_data:
            try:
                # Generate filename from restaurant name
                rest_name = r.get("name", "Unknown")
                filename_base = rest_name.strip().replace(" ", "_")
                
                # Skip if no matching image in GCS
                if valid_image_names and filename_base not in valid_image_names:
                    skipped += 1
                    continue
                
                # Parse price level
                price_level = r.get("price_level", 2)
                if isinstance(price_level, str):
                    price_mapping = {
                        "PRICE_LEVEL_FREE": 1, "PRICE_LEVEL_INEXPENSIVE": 1,
                        "PRICE_LEVEL_MODERATE": 2, "PRICE_LEVEL_EXPENSIVE": 3,
                        "PRICE_LEVEL_VERY_EXPENSIVE": 4
                    }
                    price_level = price_mapping.get(price_level, 2)
                
                # Generate GCS image URLs from restaurant name
                # Convert restaurant name to filename format: replace spaces with _
                import re
                
                GCS_BASE = "https://storage.googleapis.com/smart-travel-images-2025/restaurants/"
                
                # Get restaurant name and convert to filename format
                rest_name = r.get("name", "Unknown")
                # Replace spaces with underscore, keep Vietnamese chars and dashes
                filename_base = rest_name.strip().replace(" ", "_")
                
                # Generate up to 3 image URLs
                images_list = [
                    f"{GCS_BASE}{filename_base}_1.jpg",
                    f"{GCS_BASE}{filename_base}_2.jpg",
                    f"{GCS_BASE}{filename_base}_3.jpg"
                ]
                image_url = images_list[0]
                
                # Ensure specialty is a proper list
                specialty = r.get("specialty") or r.get("food_tags") or []
                if not isinstance(specialty, list):
                    specialty = []
                
                # Generate realistic review count based on rating
                rating = float(r.get("rating") or random.uniform(3.5, 5.0))
                review_count = int(r.get("review_count") or r.get("user_ratings_total") or random.randint(10, 500))
                
                restaurant = Restaurant(
                    name=truncate(rest_name, 255),
                    image=truncate(image_url, 500),
                    images=images_list,  # Generated GCS URLs
                    cuisine=truncate(r.get("cuisine") or r.get("category") or "Vietnamese", 100),
                    rating=round(rating, 1),
                    review_count=review_count,
                    price_level=int(price_level) if price_level else 2,
                    open_time=truncate(r.get("open_time", "07:00"), 10),
                    close_time=truncate(r.get("close_time", "22:00"), 10),
                    specialty=specialty,  # Use validated specialty list
                    description=r.get("description", ""),
                    address=truncate(r.get("address", ""), 500),
                    phone=truncate(r.get("phone", ""), 20),
                    latitude=float(r.get("latitude") or r.get("lat") or 10.7769),
                    longitude=float(r.get("longitude") or r.get("lng") or 106.7009),
                )
                session.add(restaurant)
                await session.flush()  # Get restaurant ID
                
                # Import reviews/comments for this restaurant
                comments = r.get("comments") or []
                for comment in comments[:20]:  # Limit to 20 reviews per restaurant
                    try:
                        review_rating = int(comment.get("rating", 5))
                        if review_rating < 1:
                            review_rating = 1
                        elif review_rating > 5:
                            review_rating = 5
                        
                        review = Review(
                            restaurant_id=restaurant.id,
                            author_name=truncate(comment.get("author", "Khách hàng"), 255),
                            rating=review_rating,
                            content=comment.get("text", "")[:2000] if comment.get("text") else "Đánh giá tốt",
                            visit_date=comment.get("date"),
                            likes=random.randint(0, 50),
                            is_verified=random.choice([True, False]),
                        )
                        session.add(review)
                    except Exception as rev_err:
                        print(f"Error importing review: {rev_err}")
                        continue
                
                imported += 1
                
                # Commit in batches to avoid memory issues
                if imported % 50 == 0:
                    await session.commit()
                    
            except Exception as e:
                errors += 1
                print(f"Error importing {r.get('name')}: {e}")
                await session.rollback()
                continue
        
        await session.commit()
        return {
            "message": f"Seeded {imported} restaurants with images ({skipped} skipped - no images, {errors} errors)", 
            "seeded": True, 
            "imported": imported,
            "skipped": skipped,
            "total": len(restaurants_data)
        }


@app.post("/api/admin/seed-reviews")
async def seed_reviews(count_per_restaurant: int = 5):
    """Seed database with sample reviews for restaurants"""
    import random
    from sqlalchemy import select, func
    from app.core.database import AsyncSessionLocal
    from app.modules.restaurants.models import Restaurant
    from app.modules.auth.models import User
    from app.modules.reviews.models import Review
    
    # Sample Vietnamese review data
    sample_reviews = [
        {"title": "Tuyệt vời!", "content": "Đồ ăn rất ngon, phục vụ chu đáo. Không gian thoáng mát, sạch sẽ. Giá cả hợp lý, chắc chắn sẽ quay lại!", "rating": 5},
        {"title": "Rất hài lòng", "content": "Món ăn đậm đà hương vị Việt Nam. Nhân viên thân thiện và nhiệt tình. Địa điểm dễ tìm.", "rating": 5},
        {"title": "Ngon lắm", "content": "Lần đầu đến nhưng ấn tượng tốt. Món nào cũng ngon, đặc biệt là món đặc sản của quán.", "rating": 5},
        {"title": "Đáng thử", "content": "Quán có nhiều món ngon, giá cả phải chăng. Sẽ giới thiệu cho bạn bè.", "rating": 4},
        {"title": "Khá ổn", "content": "Đồ ăn ngon, không gian ổn. Thời gian chờ hơi lâu vào cuối tuần nhưng chấp nhận được.", "rating": 4},
        {"title": "Ổn áp", "content": "Quán đông khách, chứng tỏ ngon. Món ăn hợp khẩu vị, sẽ quay lại.", "rating": 4},
        {"title": "Tạm được", "content": "Đồ ăn bình thường, giá hơi cao so với khẩu phần. Phục vụ khá chậm.", "rating": 3},
        {"title": "Cần cải thiện", "content": "Món ăn không như mong đợi. Hy vọng quán sẽ cải thiện chất lượng.", "rating": 3},
        {"title": "Xuất sắc!", "content": "Một trong những quán ngon nhất mà tôi từng ăn. Đầu bếp rất có tay nghề!", "rating": 5},
        {"title": "Đồ ăn tuyệt hảo", "content": "Hương vị đậm đà, nguyên liệu tươi ngon. Không gian đẹp, phù hợp cho gia đình.", "rating": 5},
    ]
    
    sample_users = [
        {"name": "Nguyễn Văn An", "email": "an.nguyen@demo.com"},
        {"name": "Trần Thị Bình", "email": "binh.tran@demo.com"},
        {"name": "Lê Hoàng Cường", "email": "cuong.le@demo.com"},
        {"name": "Phạm Minh Dũng", "email": "dung.pham@demo.com"},
        {"name": "Hoàng Thị Em", "email": "em.hoang@demo.com"},
        {"name": "Võ Văn Phúc", "email": "phuc.vo@demo.com"},
        {"name": "Đặng Thị Giang", "email": "giang.dang@demo.com"},
        {"name": "Bùi Văn Hùng", "email": "hung.bui@demo.com"},
        {"name": "Ngô Thị Lan", "email": "lan.ngo@demo.com"},
        {"name": "Trịnh Văn Khoa", "email": "khoa.trinh@demo.com"},
    ]
    
    # Pre-computed bcrypt hash for "password123"
    DEMO_PASSWORD_HASH = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4UxBMCGLZJrDf.FS"
    
    async with AsyncSessionLocal() as session:
        # Create sample users if not exist
        users = []
        for u in sample_users:
            result = await session.execute(select(User).where(User.email == u["email"]))
            user = result.scalar_one_or_none()
            if not user:
                user = User(
                    name=u["name"],
                    email=u["email"],
                    hashed_password=DEMO_PASSWORD_HASH,
                    is_verified=True
                )
                session.add(user)
            users.append(user)
        await session.commit()
        
        # Refresh to get IDs
        for user in users:
            await session.refresh(user)
        
        # Get restaurants (limit to first 100 for demo)
        result = await session.execute(select(Restaurant).limit(100))
        restaurants = result.scalars().all()
        
        if not restaurants:
            return {"error": "No restaurants found. Run seed-data first.", "seeded": False}
        
        # Create reviews for each restaurant
        reviews_created = 0
        for restaurant in restaurants:
            # Random number of reviews per restaurant
            num_reviews = random.randint(2, count_per_restaurant)
            for _ in range(num_reviews):
                review_data = random.choice(sample_reviews)
                user = random.choice(users)
                
                review = Review(
                    user_id=user.id,
                    restaurant_id=restaurant.id,
                    rating=review_data["rating"],
                    title=review_data["title"],
                    content=review_data["content"],
                    likes=random.randint(0, 50),
                    is_verified=random.choice([True, False]),
                    visit_date=f"2025-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
                )
                session.add(review)
                reviews_created += 1
        
        await session.commit()
        return {"message": f"Created {reviews_created} reviews for {len(restaurants)} restaurants", "seeded": True}


@app.post("/api/admin/fix-json-fields")
async def fix_json_fields():
    """Fix corrupted JSON fields in restaurants table"""
    from sqlalchemy import select, text
    from app.core.database import AsyncSessionLocal
    from app.modules.restaurants.models import Restaurant
    
    async with AsyncSessionLocal() as session:
        # Get all restaurants
        result = await session.execute(select(Restaurant))
        restaurants = result.scalars().all()
        
        fixed_count = 0
        for r in restaurants:
            changed = False
            
            # Fix images field
            if r.images is None or not isinstance(r.images, list):
                r.images = []
                changed = True
            
            # Fix specialty field
            if r.specialty is None or not isinstance(r.specialty, list):
                r.specialty = []
                changed = True
            
            if changed:
                fixed_count += 1
        
        await session.commit()
        
        return {
            "message": f"Fixed {fixed_count} restaurants with invalid JSON fields",
            "total_restaurants": len(restaurants)
        }


@app.get("/api/admin/check-data")
async def check_data():
    """Check database data integrity"""
    from sqlalchemy import select, text
    from app.core.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as session:
        # Raw SQL to bypass ORM JSON parsing
        result = await session.execute(text("""
            SELECT id, name, images, specialty 
            FROM restaurants 
            LIMIT 5
        """))
        rows = result.fetchall()
        
        sample_data = []
        for row in rows:
            sample_data.append({
                "id": row[0][:8] + "...",
                "name": row[1],
                "images_raw": str(row[2])[:100] if row[2] else "NULL",
                "specialty_raw": str(row[3])[:100] if row[3] else "NULL"
            })
        
        return {
            "sample_restaurants": sample_data
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
