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
        TR[Catalogue translation - DeepL]
        FEED[Feed builder]
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

    SHOP --> BLOG --> IGD
    IGD -->|approval request| H{{Human approval}}
    H -->|manual trigger only| PUB[Publish to Instagram]
```

## Reading the diagram

- **Supplier sync** compares supplier data with the store, writes only differences, then reads every changed value back. A mismatch fails the run.
- **Catalogue translation** (DeepL, allowlisted fields only) looks up `locale:field:text` in the cache. A hit is reused; a miss is translated and stored as `auto`. Entries marked `manual` are never replaced.
- **Feed builder** reads the store once and emits one offer per product per market, with full image galleries. Per-market differences (language, currency, URL prefix) live in a config table.
- **Blog** runs a monthly research stage that is merged by pull request (my approval gate), then drafts posts daily. Claude drafts and translates the posts inline; AI-generated images accompany them.
- **Instagram** is a two-stage flow. The draft stage runs on a schedule and creates an unpublished post plus an approval request. The publish stage has no schedule: it runs only when I trigger it.
