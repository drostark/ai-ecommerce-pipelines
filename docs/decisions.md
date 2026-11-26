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
**Why:** Unchanged copy is never sent to the translation provider twice, and only allowlisted fields are ever sent. The key does not name the provider, so a provider switch reuses what is already translated. Changed copy misses the cache and is retranslated automatically, so stale translations can't survive an edit.
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

## 9. Flag unclear cases instead of guessing
**Decision:** When onboarding products, copy may only use text the manufacturer supplied. Anything ambiguous (a missing translation, an unknown colour name, a doubtful claim) is reported for my decision and never written.
**Why:** A plausible guess in a product description becomes a public claim about the product. An empty field is easy to fix later; a wrong one has to be found first.
**Trade-off:** Some products wait for a decision before they go live.

## 10. The translation engine sits behind an interface, and a free tier must fail safe
**Decision:** Translation goes through one stable interface, with the engine and model chosen by configuration. The Gemini adapter batches strings into structured-JSON requests, throttles to the per-minute limit, backs off on 429, and stops cleanly (distinct exit code) at the daily quota. The cache is written after every field, so a rerun after the reset resumes. Only marketing prose goes to the LLM; spec and legal blocks are rebuilt deterministically and must match exactly. Out-of-range lengths get one retry, then a manual-review flag; a glossary and blocking checks (formality, untranslated terms) hold failing rows.
**Why:** A free tier is only free if hitting its limit is a normal, recoverable event, and a swappable engine keeps the workflow independent of any one vendor. Keeping legal and spec text out of the LLM removes the riskiest class of translation error.
**Trade-off:** A general-purpose model needs more guard rails than a dedicated translator, and the checks add code to maintain. Free-tier content may be used by the provider, so only public product copy goes through it.

## 11. A new sales channel is a small in-house publisher, not a hub
**Decision:** eBay is served by its own publisher against eBay's Inventory API, with a channel-neutral listing model so another channel can sit next to it. Scheduled jobs sync orders, stock and price and publish new listings. It is dry-run by default, and doubtful items are held for review instead of published.
**Why:** The store stays the source of truth and the rules (verify after writing, hold unclear cases) stay in my own code. No third-party multichannel subscription.
**Trade-off:** I maintain the marketplace integration myself.
