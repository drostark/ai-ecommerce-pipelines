"""Daily inventory sync that verifies every write.

An API returning HTTP 200 only means "request accepted", not "stock changed".
So every write is followed by a read-back, and the run exits non-zero if any
SKU does not match. There is no silent "success".

`FakeStore` stands in for the shop's admin API. Run with --simulate-silent-drop
to see a store that accepts a write but ignores it.
"""
import json
import sys
from pathlib import Path

PRODUCTS = Path(__file__).parents[2] / "sample-data" / "products.json"


class FakeStore:
    def __init__(self, stock: dict, drop: set = frozenset()):
        self.stock, self.drop = dict(stock), set(drop)

    def get(self, sku: str) -> int:
        return self.stock[sku]

    def set(self, sku: str, qty: int) -> int:
        if sku not in self.drop:               # simulated silent failure
            self.stock[sku] = qty
        return 200                             # always claims success


def sync(store, supplier: dict) -> dict:
    report = {"unchanged": [], "verified": [], "mismatch": []}
    for sku, wanted in supplier.items():
        if store.get(sku) == wanted:           # diff first: skip needless writes
            report["unchanged"].append(sku)
            continue
        store.set(sku, wanted)
        actual = store.get(sku)                # read back; never trust the 200
        bucket = "verified" if actual == wanted else "mismatch"
        report[bucket].append(sku if bucket == "verified" else (sku, wanted, actual))
    return report


def main(argv: list) -> int:
    products = json.loads(PRODUCTS.read_text())
    supplier = {p["sku"]: p["supplier_stock"] for p in products}
    drop = {"SAMPLE-003"} if "--simulate-silent-drop" in argv else set()
    store = FakeStore({p["sku"]: p["stock"] for p in products}, drop)

    r = sync(store, supplier)
    print(f"unchanged={len(r['unchanged'])} verified={len(r['verified'])} "
          f"mismatch={len(r['mismatch'])}")
    for sku, wanted, actual in r["mismatch"]:
        print(f"  MISMATCH {sku}: wrote {wanted}, store reports {actual}")
    return 1 if r["mismatch"] else 0           # non-zero exit = red CI run, a human sees it


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
