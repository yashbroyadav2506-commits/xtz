import json
import logging
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


logger = logging.getLogger(__name__)
OPEN_LIBRARY_SEARCH_URL = "https://openlibrary.org/search.json"
OPEN_LIBRARY_COVER_URL = "https://covers.openlibrary.org/b/id/{cover_id}-M.jpg"


def _normalize(value):
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def lookup_cover_url(title, author):
    """Find a likely matching Open Library cover; return None when no match exists."""
    params = urlencode(
        {
            "title": title,
            "author": author,
            "limit": 20,
            "fields": "title,author_name,cover_i",
        }
    )
    request = Request(
        f"{OPEN_LIBRARY_SEARCH_URL}?{params}",
        headers={"User-Agent": "BookSwap/1.0 (student book exchange app)"},
    )
    try:
        with urlopen(request, timeout=3) as response:
            results = json.load(response).get("docs", [])
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
        logger.warning("Open Library cover lookup failed for %r by %r: %s", title, author, error)
        return None

    normalized_title = _normalize(title)
    normalized_author = _normalize(author)
    candidates = []
    for result in results:
        cover_id = result.get("cover_i")
        result_title = _normalize(result.get("title", ""))
        authors = [_normalize(name) for name in result.get("author_name", [])]
        if not cover_id or not result_title or not authors:
            continue
        title_matches = result_title == normalized_title or normalized_title in result_title
        author_matches = any(
            result_author == normalized_author
            or result_author in normalized_author
            or normalized_author in result_author
            for result_author in authors
        )
        if title_matches and author_matches:
            score = (result_title == normalized_title, normalized_author in authors)
            candidates.append((score, cover_id))

    if not candidates:
        return None
    _, cover_id = max(candidates, key=lambda candidate: candidate[0])
    return OPEN_LIBRARY_COVER_URL.format(cover_id=cover_id)
