# Google Places → WordPress (Arabic Restaurant Lists)

Streamlit app + core module to fetch top restaurants from **Google Places API (New)** and publish Arabic HTML cards as a **WordPress draft**.

## Features
- Multi-city presets (Riyadh, Jeddah, Dammam, Khobar, Makkah, Madinah, Dubai, Abu Dhabi, Sharjah).
- Multi-category presets (burger, pizza, sushi, seafood, shawarma, mandi, breakfast, cafes, arabic, indian, chinese, italian, bbq, etc.).
- Arabic RTL cards with rating, address, phone, today's hours + weekly details, price-per-person (derived), Google Maps & website links.
- Filter by minimum review count; sort by rating then review count.
- One-click publish as **Draft** to WordPress via REST API.

## Local Run
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Cloud Deployment
1. Push these files to a GitHub repo (e.g., `places-to-wp`).
2. Go to https://share.streamlit.io/ → New app → connect your repo → set **Main file path** to `app.py`.
3. Add **Secrets** under App settings:
```toml
GOOGLE_API_KEY = "AIza..."
WP_BASE_URL    = "https://www.yoursite.com"
WP_USER        = "your_wp_user"
WP_APP_PASS    = "xxxx xxxx xxxx xxxx"
```
4. Deploy. Open the app → pick city/category → **Fetch** → preview → **Publish to WordPress**.

## WordPress Requirements
- Enable **Application Passwords** (Users → Profile → Application Passwords) to get `WP_APP_PASS`.
- Ensure your domain supports REST: `https://your-site.com/wp-json/` accessible.
- The app creates the post with status `draft`.

## Google Requirements
- Enable **Places API (New)** in your Google Cloud project.
- Use `GOOGLE_API_KEY` with the Places endpoints.
- Billing must be active on your Google Cloud project.

## Notes
- Popular Times is **not** available via Google Places API. This app shows a conservative "crowd" estimate you can edit.
- Fields like "family friendly" and "signature dish" are left as estimated/blank.
- Extend cities or categories by editing `CITY_PRESETS` and `CATEGORIES` in `places_core.py`.
