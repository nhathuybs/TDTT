"""
Chat API routes
"""
import math
import re
import time
import unicodedata
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user_id, get_current_user_id_optional
from app.modules.chat.models import ChatSession, ChatMessage, MessageRole
from app.modules.restaurants.models import Restaurant
from app.modules.chat.schemas import (
    SendMessageRequest,
    SendMessageResponse,
    ChatMessageResponse,
    ChatSessionResponse,
    ChatSessionDetailResponse
)
from app.shared.schemas import success_response, error_response
from typing import Optional, Any

router = APIRouter(prefix="/chat", tags=["Chat"])


# Simple chatbot responses (in production, integrate with AI service)
CHATBOT_RESPONSES = {
    "xin chào": "Xin chào! Tôi là trợ lý ảo của Smart Travel System. Tôi có thể giúp bạn tìm nhà hàng, đặt bàn, hoặc trả lời các câu hỏi về ẩm thực. Bạn cần gì?",
    "hello": "Xin chào! Tôi có thể giúp gì cho bạn hôm nay?",
    "tìm nhà hàng": "Bạn muốn tìm nhà hàng loại nào? Phở, bún, bánh mì, hay hải sản?",
    "đặt bàn": "Để đặt bàn, bạn cần cho tôi biết: 1) Nhà hàng bạn muốn đặt, 2) Ngày giờ, 3) Số khách. Hoặc bạn có thể vào trang nhà hàng và nhấn nút 'Đặt bàn'.",
    "phở": "Tôi tìm thấy một số quán phở ngon:\n\n1. **Phở Hà Nội** - Rating: 4.8⭐\n2. **Phở Sài Gòn** - Rating: 4.5⭐\n\nBạn muốn xem chi tiết quán nào?",
    "cảm ơn": "Không có gì! Nếu cần gì thêm, đừng ngại hỏi tôi nhé! 😊",
    "default": "Tôi hiểu bạn đang hỏi về '{query}'. Tôi có thể giúp bạn:\n\n• Tìm nhà hàng theo loại ẩm thực\n• Đặt bàn nhà hàng\n• Xem đánh giá và menu\n• Tìm đường đến nhà hàng\n\nBạn muốn tôi giúp gì?"
}


def get_chatbot_response(message: str) -> tuple[str, list]:
    """Simple chatbot logic - replace with AI in production"""
    message_lower = message.lower().strip()
    
    suggestions = []
    
    for key, response in CHATBOT_RESPONSES.items():
        if key in message_lower:
            if key == "phở":
                suggestions = ["Xem Phở Hà Nội", "Đặt bàn ngay", "Tìm quán khác"]
            elif key == "tìm nhà hàng":
                suggestions = ["Phở", "Bún", "Bánh mì", "Hải sản", "Cơm"]
            elif key in ["xin chào", "hello"]:
                suggestions = ["Tìm nhà hàng", "Đặt bàn", "Xem đánh giá"]
            return response, suggestions
    
    return CHATBOT_RESPONSES["default"].format(query=message), ["Tìm nhà hàng", "Đặt bàn", "Liên hệ hỗ trợ"]


_TOKEN_RE_ASCII = re.compile(r"[a-z0-9]+")
_TOKEN_RE_UNICODE = re.compile(r"[\w]+", flags=re.UNICODE)
_DISTRICT_RE_ASCII = re.compile(r"\b(?:quan|q)\s*(\d{1,2})\b")
_DISTRICT_RE_VI = re.compile(r"\bquận\s*(\d{1,2})\b")
_CACHE_TTL_SECONDS = 300
_RESTAURANT_INDEX_CACHE: dict[str, Any] = {"ts": 0.0, "items": []}
_ADDRESS_STOP_TOKENS_ASCII = {
    # Common location words that would cause false matches (e.g. "thành phố").
    "thanh",
    "pho",
    "viet",
    "nam",
    "vietnam",
    "tp",
    "tphcm",
    "hcm",
    "ho",
    "chi",
    "minh",
    "city",
}


def _normalize_text(text: Any) -> str:
    raw = str(text or "")
    normalized = unicodedata.normalize("NFKD", raw)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return normalized.lower()


def _tokenize_ascii(text: Any) -> set[str]:
    norm = _normalize_text(text)
    tokens = set(_TOKEN_RE_ASCII.findall(norm))
    filtered = {t for t in tokens if len(t) >= 2 and not t.isdigit()}

    for num in _DISTRICT_RE_ASCII.findall(norm):
        filtered.add(f"quan{num}")

    return filtered


def _tokenize_vi(text: Any) -> set[str]:
    raw = str(text or "").lower()
    tokens = set(_TOKEN_RE_UNICODE.findall(raw))
    filtered: set[str] = set()
    for t in tokens:
        if not t or t.isdigit() or len(t) < 2:
            continue
        if "_" in t:
            continue
        filtered.add(t)

    for num in _DISTRICT_RE_VI.findall(raw):
        filtered.add(f"quận{num}")

    return filtered


_ADDRESS_STOP_TOKENS_VI = {
    "thành",
    "phố",
    "việt",
    "nam",
    "vietnam",
    "tp",
    "tphcm",
    "hcm",
    "hồ",
    "chí",
    "minh",
    "city",
}


def _has_diacritics(text: str) -> bool:
    return any(ord(ch) > 127 for ch in (text or ""))


_QUERY_STOP_TOKENS_ASCII = {
    "quan",
    "gia",
    "re",
    "ngon",
    "tot",
    "an",
    "tim",
    "goi",
    "y",
    "gan",
    "o",
    "tai",
    "cho",
    "toi",
    "minh",
    "muon",
    "can",
    "nha",
    "hang",
}

_QUERY_STOP_TOKENS_VI = {
    "quán",
    "quận",
    "giá",
    "rẻ",
    "ngon",
    "tốt",
    "ăn",
    "tìm",
    "gợi",
    "ý",
    "gần",
    "ở",
    "tại",
    "cho",
    "tôi",
    "mình",
    "muốn",
    "cần",
    "nhà",
    "hàng",
}

_FOOD_KEYWORDS_ASCII = {
    "pho",
    "bun",
    "banh",
    "mi",
    "com",
    "tam",
    "lau",
    "nuong",
    "chay",
    "cafe",
    "tra",
    "pizza",
    "sushi",
}


def _detect_price_preference(query_tokens: set[str]) -> tuple[Optional[int], Optional[int]]:
    # Returns (min_price_level, max_price_level)
    if {"re", "binh", "dan", "gia", "tiet"}.intersection(query_tokens):
        return None, 2
    if {"cao", "cap", "sang", "trong", "fine", "dining"}.intersection(query_tokens):
        return 3, None
    return None, None


async def _get_restaurant_index(db: AsyncSession) -> list[dict[str, Any]]:
    now = time.time()
    cached = _RESTAURANT_INDEX_CACHE
    if cached.get("items") and now - float(cached.get("ts") or 0) < _CACHE_TTL_SECONDS:
        return cached["items"]

    result = await db.execute(
        select(
            Restaurant.id,
            Restaurant.name,
            Restaurant.cuisine,
            Restaurant.address,
            Restaurant.description,
            Restaurant.specialty,
            Restaurant.price_level,
            Restaurant.rating,
            Restaurant.review_count,
            Restaurant.image,
            Restaurant.images,
            Restaurant.latitude,
            Restaurant.longitude,
        ).where(Restaurant.is_active == True)
    )
    items: list[dict[str, Any]] = []
    for row in result.fetchall():
        rid = str(row[0])
        name = row[1] or ""
        cuisine = row[2] or ""
        address = row[3] or ""
        description = row[4] or ""
        specialty = row[5] if isinstance(row[5], list) else []
        price_level = int(row[6] or 2)
        rating = float(row[7] or 0.0)
        review_count = int(row[8] or 0)
        image = row[9] or ""
        images = row[10] if isinstance(row[10], list) else []
        latitude = row[11]
        longitude = row[12]

        food_tokens_ascii = (
            _tokenize_ascii(name)
            | _tokenize_ascii(cuisine)
            | _tokenize_ascii(description)
            | _tokenize_ascii(" ".join([str(t) for t in specialty if t]))
        )
        address_tokens_ascii = _tokenize_ascii(address) - _ADDRESS_STOP_TOKENS_ASCII
        tokens_ascii = food_tokens_ascii | address_tokens_ascii

        address_tokens_vi = _tokenize_vi(address) - _ADDRESS_STOP_TOKENS_VI
        tokens_vi = (
            _tokenize_vi(name)
            | _tokenize_vi(cuisine)
            | _tokenize_vi(description)
            | _tokenize_vi(" ".join([str(t) for t in specialty if t]))
            | address_tokens_vi
        )
        items.append(
            {
                "id": rid,
                "name": name,
                "cuisine": cuisine,
                "address": address,
                "description": description,
                "specialty": specialty,
                "price_level": price_level,
                "rating": rating,
                "review_count": review_count,
                "image": image,
                "images": images,
                "latitude": latitude,
                "longitude": longitude,
                "tokens_ascii": tokens_ascii,
                "tokens_vi": tokens_vi,
                "food_tokens_ascii": food_tokens_ascii,
            }
        )

    _RESTAURANT_INDEX_CACHE["ts"] = now
    _RESTAURANT_INDEX_CACHE["items"] = items
    return items


def _build_google_maps_url(place_id: str, lat: Any = None, lng: Any = None) -> str:
    if place_id:
        return f"https://www.google.com/maps/search/?api=1&query_place_id={place_id}"
    if lat is not None and lng is not None:
        return f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"
    return ""


def _score_restaurant(item: dict[str, Any], query_tokens: set[str], min_price: Optional[int], max_price: Optional[int]) -> float:
    if not query_tokens:
        match_score = 0.0
    else:
        match_score = (len(query_tokens.intersection(item.get("tokens_ascii", set()))) / max(1, len(query_tokens))) * 100.0

    rating = float(item.get("rating") or 0.0)
    review_count = int(item.get("review_count") or 0)
    popularity = rating * 10.0 + math.log10(review_count + 1) * 8.0

    price_level = int(item.get("price_level") or 2)
    if min_price is not None and price_level < min_price:
        match_score -= 15.0
    if max_price is not None and price_level > max_price:
        match_score -= 15.0

    return match_score * 2.5 + popularity


class RecommendRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(6, ge=1, le=12)


@router.post("/recommend", response_model=dict)
async def recommend_restaurants(
    request: RecommendRequest,
    db: AsyncSession = Depends(get_db),
):
    raw_message = str(request.message or "").strip()
    query_norm = _normalize_text(raw_message)
    query_tokens_ascii = _tokenize_ascii(raw_message)
    query_tokens_vi = _tokenize_vi(raw_message)
    use_vi = _has_diacritics(raw_message) and bool(query_tokens_vi)

    query_tokens_ascii_match = {t for t in query_tokens_ascii if t not in _QUERY_STOP_TOKENS_ASCII}
    query_tokens_vi_match = {t for t in query_tokens_vi if t not in _QUERY_STOP_TOKENS_VI}
    if not query_tokens_ascii_match:
        query_tokens_ascii_match = query_tokens_ascii
    if not query_tokens_vi_match:
        query_tokens_vi_match = query_tokens_vi

    query_tokens_for_price = query_tokens_ascii or query_tokens_vi
    min_price, max_price = _detect_price_preference(query_tokens_for_price)

    index = await _get_restaurant_index(db)
    query_food_tokens = query_tokens_ascii_match.intersection(_FOOD_KEYWORDS_ASCII)
    candidates = index
    if query_food_tokens:
        filtered = [item for item in index if query_food_tokens.intersection(item.get("food_tokens_ascii", set()))]
        # Only apply the hard filter when we still have enough candidates.
        if len(filtered) >= 25:
            candidates = filtered

    def score(item: dict[str, Any]) -> float:
        if use_vi:
            tokens = item.get("tokens_vi", set())
            q = query_tokens_vi_match
            match = (len(q.intersection(tokens)) / max(1, len(q))) * 100.0
            # Small boost for exact diacritics match.
            popularity = float(item.get("rating") or 0.0) * 10.0 + math.log10(int(item.get("review_count") or 0) + 1) * 8.0
            price_level = int(item.get("price_level") or 2)
            if min_price is not None and price_level < min_price:
                match -= 15.0
            if max_price is not None and price_level > max_price:
                match -= 15.0
            return match * 3.0 + popularity

        return _score_restaurant(item, query_tokens_ascii_match, min_price, max_price)

    ranked = sorted(candidates, key=score, reverse=True)

    picked: list[dict[str, Any]] = []
    for item in ranked:
        if len(picked) >= request.limit:
            break
        # Skip entries without any image to keep results attractive.
        if not item.get("image") and not item.get("images"):
            continue

        rid = item["id"]
        picked.append(
            {
                "id": rid,
                "name": item.get("name") or "",
                "cuisine": item.get("cuisine") or "",
                "address": item.get("address") or "",
                "rating": float(item.get("rating") or 0.0),
                "review_count": int(item.get("review_count") or 0),
                "price_level": int(item.get("price_level") or 2),
                "image": item.get("image") or (item.get("images") or [""])[0],
                "google_maps_url": _build_google_maps_url(rid, item.get("latitude"), item.get("longitude")),
            }
        )

    if not picked:
        reply = (
            "Mình chưa tìm được nhà hàng phù hợp với mô tả của bạn.\n"
            "Bạn thử thêm món bạn muốn ăn, khu vực (quận/huyện) hoặc mức giá nhé."
        )
    else:
        lines = [
            "Mình gợi ý một vài nhà hàng phù hợp:",
            "",
        ]
        for idx, r in enumerate(picked, start=1):
            price = "$" * int(r.get("price_level") or 2)
            lines.append(
                f"{idx}. {r.get('name')} • {r.get('rating'):.1f}⭐ ({r.get('review_count')} đánh giá) • {price}"
            )
        lines.append("")
        lines.append("Bạn muốn mình lọc theo khu vực/mức giá/món ăn cụ thể hơn không?")
        reply = "\n".join(lines)

    return success_response(
        data={
            "reply": reply,
            "restaurants": picked,
            "query": query_norm,
        },
        message="OK",
    )


@router.post("/message", response_model=dict)
async def send_message(
    request: SendMessageRequest,
    user_id: Optional[str] = Depends(get_current_user_id_optional),
    db: AsyncSession = Depends(get_db)
):
    """Send a message to chatbot"""
    # Get or create chat session
    if request.chat_id:
        result = await db.execute(
            select(ChatSession).where(ChatSession.id == request.chat_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            return error_response("E3001", "Không tìm thấy phiên chat")
    else:
        # Create new session
        session = ChatSession(
            user_id=user_id,
            title=request.message[:50] + "..." if len(request.message) > 50 else request.message
        )
        db.add(session)
        await db.flush()
    
    # Save user message
    user_message = ChatMessage(
        session_id=session.id,
        role=MessageRole.USER,
        content=request.message
    )
    db.add(user_message)
    await db.flush()
    
    # Generate bot response
    bot_response, suggestions = get_chatbot_response(request.message)
    
    # Save bot message
    bot_message = ChatMessage(
        session_id=session.id,
        role=MessageRole.ASSISTANT,
        content=bot_response,
        message_metadata={"suggestions": suggestions}
    )
    db.add(bot_message)
    await db.flush()
    await db.refresh(bot_message)
    
    # Update session
    session.updated_at = datetime.utcnow()
    await db.flush()
    
    return success_response(
        data={
            "chat_id": session.id,
            "message": {
                "id": bot_message.id,
                "chat_id": session.id,
                "role": bot_message.role.value,
                "content": bot_message.content,
                "timestamp": bot_message.created_at.isoformat(),
                "metadata": bot_message.message_metadata
            },
            "suggestions": suggestions
        },
        message="OK"
    )


@router.get("/history", response_model=dict)
async def get_chat_history(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get user's chat history"""
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .order_by(ChatSession.updated_at.desc())
    )
    sessions = result.scalars().all()
    
    return success_response(
        data=[{
            "id": s.id,
            "title": s.title,
            "updated_at": s.updated_at.isoformat()
        } for s in sessions],
        message="Lấy lịch sử chat thành công"
    )


@router.get("/{chat_id}", response_model=dict)
async def get_chat_session(
    chat_id: str,
    user_id: Optional[str] = Depends(get_current_user_id_optional),
    db: AsyncSession = Depends(get_db)
):
    """Get chat session with messages"""
    result = await db.execute(
        select(ChatSession).where(ChatSession.id == chat_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        return error_response("E3001", "Không tìm thấy phiên chat")
    
    # Get messages
    msg_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == chat_id)
        .order_by(ChatMessage.created_at)
    )
    messages = msg_result.scalars().all()
    
    return success_response(
        data={
            "id": session.id,
            "title": session.title,
            "messages": [{
                "id": m.id,
                "role": m.role.value,
                "content": m.content,
                "timestamp": m.created_at.isoformat(),
                "metadata": m.message_metadata
            } for m in messages]
        },
        message="Lấy phiên chat thành công"
    )


@router.delete("/{chat_id}", response_model=dict)
async def delete_chat_session(
    chat_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Delete a chat session"""
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == chat_id,
            ChatSession.user_id == user_id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        return error_response("E3001", "Không tìm thấy phiên chat")
    
    # Delete messages first
    msg_result = await db.execute(
        select(ChatMessage).where(ChatMessage.session_id == chat_id)
    )
    for msg in msg_result.scalars().all():
        await db.delete(msg)
    
    await db.delete(session)
    await db.flush()
    
    return success_response(
        data=None,
        message="Xóa phiên chat thành công"
    )
