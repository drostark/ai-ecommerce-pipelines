"""Translation cache that never overwrites a human edit.

Cache key = "locale:field:text". Because the source text is part of the key,
changed source copy simply misses the cache and gets retranslated, while
unchanged copy is never paid for twice. Human edits are seeded into the same
cache with source="manual"; automation only ever *adds* missing keys.

`machine_translate` is a stand-in for the DeepL call. FIELDS is an allowlist:
nothing outside it is ever sent for translation.
"""
import json
import sys
from pathlib import Path

PRODUCTS = Path(__file__).parents[2] / "sample-data" / "products.json"
LOCALES = ["de", "fr", "nl"]          # English is the source language
FIELDS = ["title", "description"]


def cache_key(locale: str, field: str, text: str) -> str:
    return f"{locale}:{field}:{text}"


def machine_translate(text: str, locale: str) -> str:
    """Stub for the translation API call. Deterministic so the demo is reproducible."""
    return f"[{locale}-auto] {text}"


def seed_manual(cache: dict, locale: str, field: str, text: str, value: str) -> None:
    """Record a human edit. Manual always wins, even over an earlier auto entry."""
    cache[cache_key(locale, field, text)] = {"value": value, "source": "manual"}


def translate(cache: dict, locale: str, field: str, text: str) -> str:
    key = cache_key(locale, field, text)
    if key not in cache:                       # only fill gaps, never overwrite
        cache[key] = {"value": machine_translate(text, locale), "source": "auto"}
    return cache[key]["value"]


def run(products: list, cache: dict) -> dict:
    """Translate every field for every locale; return {locale: {sku: {field: text}}}."""
    out = {loc: {} for loc in LOCALES}
    for p in products:
        for loc in LOCALES:
            out[loc][p["sku"]] = {f: translate(cache, loc, f, p[f]) for f in FIELDS}
    return out


if __name__ == "__main__":
    products = json.loads(PRODUCTS.read_text())
    cache: dict = {}

    # A human fixed this German title by hand; seed it before automation runs.
    first = products[0]
    seed_manual(cache, "de", "title", first["title"], "Leinen-Bettbezug (von Hand korrigiert)")

    result = run(products, cache)
    again = run(products, cache)               # second run: must change nothing
    assert result == again, "re-run changed output"
    assert result["de"]["SAMPLE-001"]["title"].startswith("Leinen-Bettbezug"), "manual edit lost"

    manual = sum(1 for e in cache.values() if e["source"] == "manual")
    print(f"{len(cache)} cache entries ({manual} manual, {len(cache) - manual} auto)")
    print("manual edit preserved; re-run is a no-op")
    sys.exit(0)
