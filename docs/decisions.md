# Key decisions and trade-offs

## 1. Verify every write; treat HTTP 200 as "accepted", not "done"
**Decision:** After each write, read the value back and compare. Any mismatch fails the run with a non-zero exit.
**Why:** The dangerous failure is a sync that reports success while the store is unchanged. Nobody notices, because nothing is red.
**Trade-off:** One extra read per changed item, and more failed runs at first. A failed run is cheaper than a wrong shop.

## 2. Diff before writing
**Decision:** Compare source and destination first and write only what differs.
**Why:** Fewer writes means fewer chances to fail, less API usage, and a clearer report ("3 unchanged, 4 verified").
**Trade-off:** Needs a read per item even when nothing changes.

## 3. Cache translations by `locale:field:text`
**Decision:** Include the source text in the cache key.
**Why:** Unchanged copy is never sent to DeepL twice, and only allowlisted fields are ever sent. Changed copy misses the cache and is retranslated automatically, so stale translations can't survive an edit.
**Trade-off:** If the source changes, an old manual edit is orphaned under the old key and must be re-seeded. I accept that because the alternative, silently keeping a translation that no longer matches the source, is worse.

## 4. Manual edits live in the cache and always win
**Decision:** Human corrections are seeded as `source: manual`. Automation only fills missing keys.
**Why:** If automation can overwrite a correction, I stop making corrections and quality drifts.
**Trade-off:** A bad manual edit stays until a person fixes it.

## 5. One feed builder, a config table per market
**Decision:** One function produces one feed with an offer per product per market, driven by a table of language, currency and URL prefix.
**Why:** Adding or changing a market is a data change, not a new script. All markets share one validation step.
**Trade-off:** A bug in the shared builder affects every market at once. The builder asserts the expected offer count and unique IDs before output.

## 6. Human approval for irreversible steps
**Decision:** Drafting is scheduled. Publishing to Instagram is a separate workflow with no schedule that I trigger by hand.
**Why:** A published post can't be quietly taken back. A draft that sits unpublished costs nothing.
**Trade-off:** Slower, and it needs me. For a brand account, that is the right price.

## 7. Pull requests and read-only diagnosis when working with AI
**Decision:** AI-written changes land through PRs I review. For problems, the AI diagnoses read-only first, then proposes a fix.
**Why:** It keeps me in the loop on the part that matters (what changes in production) while the AI does the typing and investigation.
**Trade-off:** Slower than letting it write directly.

## 8. Prefer free tiers until a paid one is justified
**Decision:** Start on free-tier infrastructure, such as scheduled CI runs, and pay only when a limit is actually hit.
**Why:** A solo operation can't carry fixed costs for pipelines that may not earn their keep.
**Trade-off:** Free tiers have limits and occasional constraints that shape the design.
