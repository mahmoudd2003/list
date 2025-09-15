# -*- coding: utf-8 -*-
"""
Streamlit app to fetch top restaurants by city/category from Google Places (New)
and publish an Arabic draft post to WordPress.
"""
import json
import pandas as pd
import streamlit as st

from places_core import (
    CITY_PRESETS,
    CATEGORIES,
    build_query,
    places_search_text,
    make_items_from_places,
    build_post_html,
    create_or_update_draft_post,
)

st.set_page_config(page_title="قائمة المطاعم (Google Places → WordPress)", page_icon="🍽️")

st.title("🍽️ قوائم مطاعم تلقائية — Google Places → WordPress (Draft)")
st.write("اختر المدينة والفئة، اعرض المعاينة، ثم انشر المقال كمسودة في ووردبريس.")

# Secrets / credentials
with st.sidebar:
    st.header("الإعدادات و المفاتيح")
    google_api_key = st.text_input("Google API Key", value=st.secrets.get("GOOGLE_API_KEY", ""), type="password")
    wp_base_url = st.text_input("WP Base URL", value=st.secrets.get("WP_BASE_URL", "https://www.example.com"))
    wp_user = st.text_input("WP Username", value=st.secrets.get("WP_USER", ""))
    wp_app_pass = st.text_input("WP Application Password", value=st.secrets.get("WP_APP_PASS", ""), type="password")
    st.caption("ننصح بوضع المفاتيح في Secrets على Streamlit Cloud بدلاً من كتابتها هنا.")

col1, col2, col3 = st.columns(3)
with col1:
    city_key = st.selectbox("المدينة", options=list(CITY_PRESETS.keys()), index=list(CITY_PRESETS.keys()).index("riyadh"))
with col2:
    category_key = st.selectbox("الفئة", options=list(CATEGORIES.keys()), index=list(CATEGORIES.keys()).index("burger"))
with col3:
    max_results = st.number_input("أقصى عدد نتائج (<=20)", min_value=5, max_value=20, value=15, step=1)

min_reviews = st.slider("أقل عدد مراجعات للاعتماد", min_value=0, max_value=2000, value=200, step=50)

custom_query = st.text_input("استعلام مخصص (اختياري)", value="")
if not custom_query.strip():
    default_query = build_query(category_key, city_key)
else:
    default_query = custom_query.strip()

st.write(f"🔎 **الاستعلام:** {default_query}")

tab1, tab2 = st.tabs(["المعاينة", "نشر إلى ووردبريس"])

with tab1:
    if st.button("جلب النتائج من خرائط Google"):
        if not google_api_key:
            st.error("الرجاء إدخال Google API Key أولًا.")
        else:
            try:
                places = places_search_text(google_api_key, default_query, city_key, max_results=max_results)
                items = make_items_from_places(google_api_key, places, min_reviews=min_reviews)
                st.session_state["items"] = items
                st.success(f"تم الجلب بنجاح. عدد العناصر بعد الفلترة: {len(items)}")
                if items:
                    # Show table
                    df = pd.DataFrame([{
                        "الاسم": it["name"],
                        "التقييم": it.get("rating"),
                        "عدد المراجعات": it.get("rating_count"),
                        "السعر للفرد": it.get("price_range"),
                        "الهاتف": it.get("phone"),
                        "العنوان": it.get("address"),
                        "خرائط Google": it.get("maps_uri"),
                        "الموقع": it.get("website"),
                    } for it in items])
                    st.dataframe(df, use_container_width=True)
                    # HTML preview
                    html_preview = build_post_html(items, title=default_query)
                    st.markdown("**معاينة HTML:**", help="هذه هي البطاقات التي سيتم حقنها في المقال.")
                    st.html(html_preview)
                else:
                    st.warning("لم يتم العثور على عناصر بعد شروط الفلترة. جرب خفض حد المراجعات أو زيادة عدد النتائج.")
            except Exception as e:
                st.error(f"حدث خطأ أثناء الجلب: {e}")

with tab2:
    draft_title = st.text_input("عنوان المقال", value=f"{default_query} — محدّث آليًا")
    publish_btn = st.button("انشر كمسودة في ووردبريس")
    if publish_btn:
        items = st.session_state.get("items", [])
        if not items:
            st.error("لا توجد نتائج في الذاكرة. الرجاء جلب النتائج من التبويب الأول أولاً.")
        elif not all([wp_base_url, wp_user, wp_app_pass]):
            st.error("الرجاء إدخال إعدادات ووردبريس كاملة.")
        else:
            try:
                html_content = build_post_html(items, title=draft_title)
                res = create_or_update_draft_post(
                    base_url=wp_base_url,
                    user=wp_user,
                    app_password=wp_app_pass,
                    title=draft_title,
                    content_html=html_content,
                    post_id=None,
                )
                st.success(f"تم إنشاء المسودة! المعرف: {res.get('id')} — الحالة: {res.get('status')}")
                if res.get("link"):
                    st.markdown(f"[فتح المسودة في الموقع]({res['link']})")
            except Exception as e:
                st.error(f"فشل النشر إلى ووردبريس: {e}")
