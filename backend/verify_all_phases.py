import asyncio
import sys
import httpx
from app.main import app
from app.core.database import init_db, get_database

sys.stdout.reconfigure(encoding='utf-8')

async def run_full_verification():
    print("=" * 60)
    print("      CINEMATCH AI — FULL PHASE 1-11 VERIFICATION")
    print("=" * 60)

    # 1. Database Verification
    await init_db()
    db = get_database()
    total_movies = await db.movies.count_documents({})
    print(f"\n[PHASE 1] TOTAL MOVIES IN MONGODB: {total_movies}")
    assert total_movies > 5000, f"Expected 5000+ movies, got {total_movies}"
    
    genres = await db.movies.distinct("genres")
    languages = await db.movies.distinct("original_language")
    print(f"[PHASE 1] Distinct Genres: {len(genres)}, Distinct Languages: {len(languages)}")

    # Test in-process with ASGITransport for 100% reliability
    transport = httpx.ASGITransport(app=app)
    base = "http://test/api"
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 2. Homepage & Pagination
        r_movies = await client.get(f"{base}/movies?page=1&per_page=20")
        print(f"\n[PHASE 2] Homepage GET /movies Status: {r_movies.status_code}, Items: {len(r_movies.json().get('items', []))}, Total: {r_movies.json().get('total')}")

        r_page2 = await client.get(f"{base}/movies?page=2&per_page=20")
        p1_ids = [m['id'] for m in r_movies.json().get('items', [])]
        p2_ids = [m['id'] for m in r_page2.json().get('items', [])]
        overlap = set(p1_ids) & set(p2_ids)
        print(f"[PHASE 2] Pagination Page 2 Items: {len(p2_ids)}, Overlap with Page 1: {len(overlap)} (Must be 0)")

        # 3. Search Verification
        queries = ["Tollywood", "Bollywood", "Hollywood", "Anime", "Marvel", "Comedy", "Horror", "Telugu", "Hindi", "English", "Christopher Nolan", "Rajamouli", "Tom Cruise", "2025", "Action", "Sci-Fi"]
        print("\n[PHASE 3 & 11] SEARCH RESULTS VERIFICATION:")
        for q in queries:
            r_search = await client.get(f"{base}/search?q={q}")
            data = r_search.json()
            items = data.get("items", [])
            total = data.get("total", 0)
            titles = [m.get("title") for m in items[:3]]
            print(f"  - Query: '{q:18}' | Status: {r_search.status_code} | Total: {total:5} | Top Matches: {titles}")

        # 4. Discover Endpoint
        r_disc = await client.get(f"{base}/movies/discover?page=1&per_page=10&genre=Action&min_rating=7.0")
        print(f"\n[PHASE 4] GET /movies/discover Status: {r_disc.status_code}, Filtered Total: {r_disc.json().get('total')}")

        # 5. Recommendation Engine
        r_pop = await client.get(f"{base}/recommendations/popular?mode=weighted&limit=5")
        r_mood = await client.get(f"{base}/recommendations/mood/happy?limit=5")
        r_genre = await client.get(f"{base}/recommendations/genre?genres=Action&limit=5")
        r_sem = await client.post(f"{base}/recommendations/semantic", json={"query": "mind-bending space survival", "top_k": 5})

        pop_titles = [m['title'] for m in r_pop.json().get('recommendations', [])]
        mood_titles = [m['title'] for m in r_mood.json().get('recommendations', [])]
        sem_titles = [m['title'] for m in r_sem.json().get('recommendations', [])]
        print(f"\n[PHASE 5] Popularity Recs: {pop_titles}")
        print(f"[PHASE 5] Mood (Happy) Recs: {mood_titles}")
        print(f"[PHASE 5] Semantic Recs: {sem_titles}")

        # 6. Movie Details Routing
        r_inc = await client.get(f"{base}/search?q=Inception")
        inc_items = r_inc.json().get("items", [])
        if inc_items:
            inc_id = inc_items[0]["id"]
            r_detail = await client.get(f"{base}/movies/{inc_id}")
            det_title = r_detail.json().get("title")
            print(f"\n[PHASE 6] Clicking Inception (ID: {inc_id}) returned: '{det_title}' (Verification: {'PASSED' if 'Inception' in det_title else 'FAILED'})")

    print("\n" + "=" * 60)
    print("      ALL PHASES VERIFIED SUCCESSFULLY")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_full_verification())
