# -*- coding: utf-8 -*-
import pandas as pd
import streamlit as st
from streamlit.components.v1 import html as st_html

from places_core import CITY_PRESETS, places_search_text, make_items_from_places, build_post_html, create_or_update_draft_post

st.set_page_config(page_title="قائمة المطاعم", page_icon="🍽️")

st.title("🍽️ جلب مطاعم من Google Places ونشرها كمسودة ووردبريس")

with st.sidebar:
    google_api_key = st.text_input("Google API Key", value=st.secrets.get("GOOGLE_API_KEY",""), type="password")
    wp_base_url = st.text_input("WP Base URL", value=st.secrets.get("WP_BASE_URL",""))
    wp_user = st.text_input("WP Username", value=st.secrets.get("WP_USER",""))
    wp_app_pass = st.text_input("WP App Password", value=st.secrets.get("WP_APP_PASS",""), type="password")

st.subheader("استعلام البحث")
query_text = st.text_input("اكتب ما تريد البحث عنه", placeholder="مثال: مطاعم بيتزا في الرياض")
city_key = st.selectbox("المدينة (اختياري)", options=["—"]+list(CITY_PRESETS.keys()), index=0)
max_results = st.number_input("أقصى عدد نتائج", min_value=5, max_value=20, value=15, step=1)
min_reviews = st.slider("أقل عدد مراجعات", 0, 2000, 200, 50)

final_query = query_text.strip()

tab1, tab2 = st.tabs(["المعاينة","نشر"])

with tab1:
    if st.button("جلب النتائج"):
        if not google_api_key: st.error("أدخل API Key")
        elif not final_query: st.error("أدخل استعلام")
        else:
            try:
                effective_city = city_key if city_key!="—" else "riyadh"
                places = places_search_text(google_api_key, final_query, effective_city, int(max_results))
                region_code = CITY_PRESETS.get(effective_city,{}).get("regionCode")
                items = make_items_from_places(google_api_key, places, int(min_reviews), region_code=region_code)
                st.session_state["items"] = items
                st.success(f"تم الجلب. عدد النتائج: {len(items)}")
                if items:
                    df = pd.DataFrame([{"الاسم":it["name"],"العنوان":it["address"],"الهاتف":it["phone"],"المراجعات":it["rating_count"]} for it in items])
                    st.dataframe(df,use_container_width=True)
                    html_preview = build_post_html(items, title=final_query)
                    st_html(html_preview, height=800, scrolling=True)
            except Exception as e:
                st.error(f"خطأ: {e}")

with tab2:
    draft_title = st.text_input("عنوان المقال", value=f"{final_query} — محدّث")
    if st.button("انشر كمسودة"):
        items = st.session_state.get("items",[])
        if not items: st.error("لا يوجد نتائج")
        else:
            try:
                html_content = build_post_html(items, draft_title)
                res = create_or_update_draft_post(wp_base_url, wp_user, wp_app_pass, draft_title, html_content)
                st.success(f"تم إنشاء المسودة #{res.get('id')}")
                if res.get("link"): st.markdown(f"[رابط المسودة]({res['link']})")
            except Exception as e:
                st.error(f"فشل النشر: {e}")
