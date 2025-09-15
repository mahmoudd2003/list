# -*- coding: utf-8 -*-
"""
places_core.py
Reusable core functions for fetching Google Places (New) data and publishing to WordPress.
"""

import datetime
import html
from typing import Dict, List, Optional, Tuple

import requests

# -----------------------------
# City presets (expandable)
# -----------------------------
CITY_PRESETS = {
    # KSA
    "riyadh":   {"lat": 24.7136, "lng": 46.6753, "radius": 30000, "regionCode": "SA", "ar": "الرياض"},
    "jeddah":   {"lat": 21.4858, "lng": 39.1925, "radius": 30000, "regionCode": "SA", "ar": "جدة"},
    "dammam":   {"lat": 26.4207, "lng": 50.0888, "radius": 30000, "regionCode": "SA", "ar": "الدمام"},
    "khobar":   {"lat": 26.2172, "lng": 50.1971, "radius": 25000, "regionCode": "SA", "ar": "الخبر"},
    "makkah":   {"lat": 21.3891, "lng": 39.8579, "radius": 25000, "regionCode": "SA", "ar": "مكة"},
    "madinah":  {"lat": 24.5247, "lng": 39.5692, "radius": 25000, "regionCode": "SA", "ar": "المدينة"},
    # UAE
    "dubai":    {"lat": 25.2048, "lng": 55.2708, "radius": 30000, "regionCode": "AE", "ar": "دبي"},
    "abudhabi": {"lat": 24.4539, "lng": 54.3773, "radius": 30000, "regionCode": "AE", "ar": "أبوظبي"},
    "sharjah":  {"lat": 25.3463, "lng": 55.4209, "radius": 25000, "regionCode": "AE", "ar": "الشارقة"},
}

# -----------------------------
# Restaurant categories (expandable)
# -----------------------------
CATEGORIES = {
    "burger": "برجر",
    "pizza": "بيتزا",
    "sushi": "سوشي",
    "seafood": "مأكولات بحرية",
    "steakhouse": "ستيك هاوس",
    "shawarma": "شاورما",
    "mandi": "مندي",
    "breakfast": "فطور",
    "cafes": "كافيهات",
    "arabic": "مأكولات عربية",
    "indian": "هندي",
    "chinese": "صيني",
    "italian": "إيطالي",
    "bbq": "مشاوي",
}

AR_WEEKDAYS = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]

# -----------------------------
# Mapping helpers
# -----------------------------
def map_price_level_to_range(level: Optional[int]) -> str:
    if level is None or level == 0:
        return "غير محدد"
    if level == 1:
        return "25 – 50 ر.س"
    if level == 2:
        return "50 – 75 ر.س"
    if level == 3:
        return "75 – 120 ر.س"
    if level >= 4:
        return "120+ ر.س"
    return "غير محدد"

def guess_service_options(types: List[str]) -> List[str]:
    opts = []
    tset = set([t.lower() for t in types or []])
    if "meal_delivery" in tset:
        opts.append("توصيل")
    if "meal_takeaway" in tset or "meal_take-away" in tset:
        opts.append("استلام")
    if "restaurant" in tset:
        opts.append("جلوس في المطعم")
    return opts

def normalize_time_string(s: str) -> str:
    if ":" in s:
        parts = s.split(":", 1)
        times = parts[1].strip()
    else:
        times = s.strip()
    times = times.replace("AM", "ص").replace("PM", "م").replace("am", "ص").replace("pm", "م")
    times = times.replace("-", "–")
    return times

def pick_today_hours(weekday_desc: List[str]) -> Tuple[str, List[str]]:
    if not weekday_desc:
        return ("—", [])
    today_idx = datetime.datetime.now().weekday()  # Monday=0
    today_ar = AR_WEEKDAYS[today_idx]
    line = weekday_desc[today_idx] if today_idx < len(weekday_desc) else weekday_desc[0]
    today_times = normalize_time_string(line)
    full_week = []
    for i, raw in enumerate(weekday_desc):
        times = normalize_time_string(raw)
        label = AR_WEEKDAYS[i if i < len(AR_WEEKDAYS) else 0]
        full_week.append(f"{label}: {times}")
    return (f"{today_ar}: {today_times}", full_week)

# -----------------------------
# HTML builders
# -----------------------------
def build_html_item(p: Dict) -> str:
    name = html.escape(p.get("name", "مطعم"))
    address = html.escape(p.get("address", "—"))
    phone = html.escape(p.get("phone", "—"))
    price_range = html.escape(p.get("price_range", "غير محدد"))
    website = p.get("website", "")
    maps_uri = p.get("maps_uri", "")
    today_hours = html.escape(p.get("today_hours", "—"))
    service_options = p.get("service_options", [])
    service_str = "، ".join(service_options) if service_options else "—"
    family = html.escape(p.get("family_friendly", "—"))
    signature = html.escape(p.get("signature_dish", "")) if p.get("signature_dish") else "—"
    crowd = html.escape(p.get("crowd_note", "—"))
    rating = p.get("rating", None)
    rating_count = p.get("rating_count", None)

    rating_html = ""
    if rating is not None and rating_count is not None:
        rating_html = f'<div class="text-sm" style="color:#6b7280;">التقييم: {rating:.1f} / 5 (بناءً على {rating_count} مراجعة)</div>'

    website_html = f'<a href="{website}" target="_blank" rel="nofollow noopener">زيارة الموقع</a>' if website else "—"
    maps_html = f'<a href="{maps_uri}" target="_blank" rel="nofollow noopener">فتح في خرائط Google</a>' if maps_uri else "—"

    full_hours = p.get("full_hours", [])
    hours_details = ""
    if full_hours:
        items = "".join(f"<li>{html.escape(line)}</li>" for line in full_hours)
        hours_details = f"""
<details>
  <summary>أوقات العمل (الأسبوع كامل)</summary>
  <ul>
    {items}
  </ul>
</details>
"""

    return f"""
<div class="restaurant-card" itemscope itemtype="https://schema.org/Restaurant" dir="rtl" style="border:1px solid #e5e7eb;border-radius:12px;padding:16px;margin-bottom:16px;">
  <h3 itemprop="name" style="margin:0 0 8px 0;font-size:20px;">{name}</h3>
  {rating_html}
  <div style="line-height:1.9;">
    <div><strong>العنوان:</strong> <span itemprop="address">{address}</span></div>
    <div><strong>الهاتف:</strong> <a href="tel:{phone}">{phone}</a></div>
    <div><strong>الأوقات (اليوم):</strong> {today_hours}</div>
    {hours_details}
    <div><strong>مناسب للعوائل:</strong> {family}</div>
    <div><strong>السعر للشخص:</strong> {price_range}</div>
    <div><strong>الطبق المميز:</strong> {signature}</div>
    <div><strong>خيارات الخدمة:</strong> {service_str}</div>
    <div><strong>أوقات الزحمة:</strong> {crowd}</div>
    <div><strong>خرائط Google:</strong> {maps_html}</div>
    <div><strong>الموقع الإلكتروني:</strong> {website_html}</div>
  </div>
</div>
"""

def build_post_html(items: List[Dict], title: str) -> str:
    now = datetime.datetime.now().strftime("%Y-%m-%d")
    cards = "\n".join(build_html_item(p) for p in items)
    return f"""
<div itemscope itemtype="https://schema.org/ItemList" dir="rtl">
  <p>آخر تحديث: {now}. المصدر: خرائط Google.</p>
  {cards}
</div>
"""

# -----------------------------
# Google Places (New)
# -----------------------------
PLACES_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
PLACES_DETAILS_URL_TMPL = "https://places.googleapis.com/v1/places/{place_id}"

def places_search_text(api_key: str, query: str, city_key: str, max_results: int = 15) -> List[Dict]:
    """Text Search with explicit FieldMask (required by Places API New)."""
    preset = CITY_PRESETS.get(city_key.lower())
    if not preset:
        raise ValueError(f"Unsupported city '{city_key}'. Supported: {', '.join(CITY_PRESETS.keys())}")

    payload = {
        "textQuery": query,
        "languageCode": "ar",
        "regionCode": preset["regionCode"],
        "maxResultCount": min(max_results, 20),
        "locationBias": {
            "circle": {
                "center": {"latitude": preset["lat"], "longitude": preset["lng"]},
                "radius": preset["radius"],
            }
        },
        "includedType": "restaurant",
    }
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        # FieldMask REQUIRED for searchText responses
        "X-Goog-FieldMask": "places.id,places.displayName,places.rating,places.userRatingCount",
    }
    r = requests.post(PLACES_SEARCH_URL, headers=headers, json=payload, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"[places_search_text] HTTP {r.status_code} - {r.text}")
    data = r.json()
    return data.get("places", [])

def place_details(api_key: str, place_id: str, field_mask: Optional[str] = None) -> Dict:
    """Place Details with FieldMask specifying all needed fields."""
    if not field_mask:
        field_mask = ",".join([
            "id",
            "displayName",
            "formattedAddress",
            "nationalPhoneNumber",
            "websiteUri",
            "googleMapsUri",
            "priceLevel",
            "rating",
            "userRatingCount",
            "currentOpeningHours",
            "regularOpeningHours",
            "types",
        ])
    url = PLACES_DETAILS_URL_TMPL.format(place_id=place_id)
    headers = {
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": field_mask,
    }
    r = requests.get(url, headers=headers, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"[place_details] HTTP {r.status_code} - {r.text}")
    return r.json()

# -----------------------------
# WordPress REST
# -----------------------------
def create_or_update_draft_post(
    base_url: str,
    user: str,
    app_password: str,
    title: str,
    content_html: str,
    post_id: Optional[int] = None
) -> Dict:
    """Creates or updates a WordPress post as DRAFT."""
    auth = (user, app_password)
    endpoint = f"{base_url.rstrip('/')}/wp-json/wp/v2/posts"
    payload = {"title": title, "content": content_html, "status": "draft"}
    if post_id:
        url = f"{endpoint}/{post_id}"
        r = requests.post(url, auth=auth, json=payload, timeout=60)
    else:
        r = requests.post(endpoint, auth=auth, json=payload, timeout=60)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"[WordPress] HTTP {r.status_code} - {r.text}")
    return r.json()

# -----------------------------
# Orchestration helpers
# -----------------------------
def build_query(category_key: str, city_key: str) -> str:
    cat_ar = CATEGORIES.get(category_key, category_key)
    city_ar = CITY_PRESETS.get(city_key, {}).get("ar", city_key)
    return f"أفضل مطاعم {cat_ar} في {city_ar}"

def make_items_from_places(api_key: str, places: List[Dict], min_reviews: int = 200) -> List[Dict]:
    items: List[Dict] = []
    for p in places:
        pid = p.get("id") or p.get("placeId")
        if not pid:
            continue
        det = place_details(api_key, pid)

        name = det.get("displayName", {}).get("text", "")
        address = det.get("formattedAddress", "")
        phone = det.get("nationalPhoneNumber", "")
        website = det.get("websiteUri", "")
        maps_uri = det.get("googleMapsUri", "")
        price_level = det.get("priceLevel", None)
        rating = det.get("rating", None)
        rating_count = det.get("userRatingCount", None)
        types = det.get("types", []) or []

        ch = det.get("currentOpeningHours", {}) or {}
        weekday_desc = ch.get("weekdayDescriptions", []) or []
        today_hours, full_hours = pick_today_hours(weekday_desc)

        services = guess_service_options(types)

        item = {
            "name": name,
            "address": address or "—",
            "phone": phone or "—",
            "price_range": map_price_level_to_range(price_level),
            "website": website,
            "maps_uri": maps_uri,
            "today_hours": today_hours,
            "full_hours": full_hours,
            "service_options": services,
            "family_friendly": "نعم (تقديري)",
            "signature_dish": "",
            "crowd_note": "8:00 م – 11:00 م (تقديري)",
            "rating": rating,
            "rating_count": rating_count,
            "types": types,
        }
        items.append(item)

    # Filter & sort
    items = [it for it in items if (it.get("rating_count") or 0) >= min_reviews]
    items.sort(key=lambda x: ((x.get("rating") or 0), (x.get("rating_count") or 0)), reverse=True)
    return items
