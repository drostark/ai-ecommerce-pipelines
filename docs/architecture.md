# Architecture

Small pipelines around one store, each with a single job. They share three rules: **diff before writing, verify after writing, and put a person in front of anything irreversible.**

```mermaid
flowchart TB
    subgraph Inputs
        SUP[Supplier data]
        CAT[Product catalogue]
        EDIT[Manual edits]
    end

    subgraph Automation["Scheduled automation"]
        SYNC[Supplier sync]
        TR[Catalogue translation - Gemini + Claude]
        FEED[Feed builder]
        EBAY[eBay publisher - outlet items]
        BLOG[Blog pipeline]
        IGD[Instagram draft]
    end

    subgraph Stores
        SHOP[(Store)]
        CACHE[(Translation cache)]
    end

    SUP --> SYNC
    SYNC -->|write| SHOP
    SHOP -->|read back| SYNC
    SYNC -->|mismatch| ALERT[Failed run = visible alert]

    EDIT -->|seeded as source=manual| CACHE
    CAT --> TR
    TR <-->|lookup / fill gaps only| CACHE
    TR --> SHOP

    SHOP --> FEED
    FEED -->|"one feed, offer per product x market"| MC[Merchant Center]

    SHOP --> EBAY
    EBAY -->|"publish, then read back"| EB[eBay marketplace]
    EB -->|"orders lower stock; sold on store withdraws offer"| EBAY
    EBAY -->|"held item: low-confidence category or price floor"| H2{{Human review}}

    SHOP --> BLOG --> IGD
    IGD -->|approval request| H{{Human approval}}
    H -->|manual trigger only| PUB[Publish to Instagram]
```

## Reading the diagram

- **Supplier sync** compares supplier data with the store, writes only differences, then reads every changed value back. A mismatch fails the run.
- **Catalogue translation** (allowlisted fields only) looks up `locale:field:text` in the cache. A hit is reused; a miss is translated and stored as `auto`. Entries marked `manual` are never replaced. Product titles and SEO meta fields go to Claude; everything else goes to the Gemini API through a provider interface: batched structured-JSON requests, per-minute throttling with backoff, a clean resume-safe stop on the daily quota, and length-range validation that flags a field for manual review after one retry. The cache key does not name the provider, so a provider change reuses existing translations. The earlier providers were DeepL and Azure AI Translator.
- **Feed builder** reads the store once and emits one offer per product per market, with full image galleries. Per-market differences (language, currency, URL prefix) live in a config table.
- **eBay publisher** is an in-house, per-channel publisher that talks to eBay's Sell Inventory API. It is dry-run by default. The store stays the source of truth: an eBay order lowers store stock, a sale in the store withdraws the eBay offer, and prices follow the store, so the single unit of an outlet item is never sold twice. Items it is unsure about (low-confidence category, price below a floor) are held for review. **Status:** built and running for outlet (returned / open-box) items only; it is not wired into the Merchant Center feed builder and does not cover the main catalogue yet.
- **Blog** runs a monthly research stage that is merged by pull request (my approval gate), then drafts posts daily. Claude drafts and translates the posts inline; AI-generated images accompany them.
- **Instagram** is a two-stage flow. The draft stage runs on a schedule and creates an unpublished post plus an approval request. The publish stage has no schedule: it runs only when I trigger it.
