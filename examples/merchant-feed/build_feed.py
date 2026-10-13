"""One feed builder, many markets.

A single function turns the product catalogue into one feed with one offer per
(product, market). Adding a market is a config row, not a new feed or script.
Supports full image galleries.
"""
import json
import xml.etree.ElementTree as ET
from pathlib import Path

PRODUCTS = Path(__file__).parents[2] / "sample-data" / "products.json"
G = "http://base.google.com/ns/1.0"
ET.register_namespace("g", G)

# market -> language, currency, URL prefix. This table is the only per-market code.
MARKETS = {
    "DE": {"lang": "de", "currency": "EUR", "path": "/de"},
    "AT": {"lang": "de", "currency": "EUR", "path": "/de-at"},
    "FR": {"lang": "fr", "currency": "EUR", "path": "/fr"},
    "BE": {"lang": "nl", "currency": "EUR", "path": "/nl-be"},
    "LU": {"lang": "fr", "currency": "EUR", "path": "/fr-lu"},
    "NL": {"lang": "nl", "currency": "EUR", "path": "/nl"},
}
BASE_URL = "https://shop.example.com"


def g(parent: ET.Element, tag: str, text: str) -> None:
    ET.SubElement(parent, f"{{{G}}}{tag}").text = text


def build_feed(products: list, markets: dict, translations: dict | None = None) -> ET.Element:
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "Example catalogue feed"
    for code, m in markets.items():
        for p in products:
            item = ET.SubElement(channel, "item")
            tr = (translations or {}).get(m["lang"], {}).get(p["sku"], {})
            g(item, "id", f"{p['sku']}-{code}")            # unique per market
            g(item, "item_group_id", p["sku"])
            g(item, "title", tr.get("title", p["title"]))
            g(item, "description", tr.get("description", p["description"]))
            for i, url in enumerate(p["images"]):
                g(item, "image_link" if i == 0 else "additional_image_link", url)
            g(item, "link", f"{BASE_URL}{m['path']}/products/{p['sku'].lower()}")
            g(item, "price", f"{p['price']} {m['currency']}")
            g(item, "availability", "in_stock" if p["stock"] > 0 else "out_of_stock")
            g(item, "feed_label", code)
            g(item, "content_language", m["lang"])
    return rss


def validate(rss: ET.Element, expected: int) -> None:
    """Fail loudly instead of shipping a short or duplicated feed."""
    ids = [e.text for e in rss.iter(f"{{{G}}}id")]
    assert len(ids) == expected, f"expected {expected} offers, got {len(ids)}"
    assert len(set(ids)) == len(ids), "duplicate offer ids"


if __name__ == "__main__":
    products = json.loads(PRODUCTS.read_text())
    feed = build_feed(products, MARKETS)
    validate(feed, len(products) * len(MARKETS))
    out = Path(__file__).parent / "feed.xml"
    ET.indent(feed)
    ET.ElementTree(feed).write(out, encoding="utf-8", xml_declaration=True)
    print(f"{len(products) * len(MARKETS)} offers for {len(MARKETS)} markets -> {out.name}")
