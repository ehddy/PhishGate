# G2 and G3 snapshots

This directory holds the self-collected part of PhishGate-Bench:

- **G2**: 100 phishing pages from public phishing feeds (OpenPhish and PhishTank)
- **G3**: 200 benign pages, selected as described in [BENIGN_SAMPLING.md](BENIGN_SAMPLING.md)

The snapshots are not tracked by Git. Download them from Zenodo and extract them with `scripts/dataset_bundle.py unpack` (see the main README).

## Layout

```text
data/manual/samples/
├── phishing/<sample_id>/
│   ├── source.yaml          # provenance, label, brand, capture method
│   └── raw/
│       ├── index.html       # server HTML as fetched
│       ├── rendered.html    # DOM after one headless render
│       ├── screenshot.png   # screenshot used for visual review
│       └── page.mhtml       # full snapshot served behind the gate
└── benign/<sample_id>/      # same layout
```

The annotation files `data/manual_annotation.csv` (G2) and `data/manual_benign_annotation.csv` (G3) list every sample with its brand and source URL. For G3 they also record the benchmark design fields `page_type`, `popularity`, `tranco_rank`, `tranco_list_id`, and `brand_relation`. `benign_review.csv` and `tranco_rank_audit.csv` record the review and ranking decisions behind G3.

## Selection criteria

- **G2**: every sample must impersonate an identifiable brand and show a credential or personal-data form on the captured page. Landing pages without an input field, dead links, and vendor phishing-simulation pages were excluded. Captures that showed personal data from the collection environment were excluded rather than masked.
- **G3**: a balanced 2 x 2 design of page purpose (form or general) and Tranco popularity (popular or long tail), with 50 samples per cell. Every sample was visually reviewed before inclusion.

## Access

Each sample can be reached in two ways:

- **Access slug**: `http://<phishgate-host>/<slug>/`. No hostname setup is needed. `scripts/prepare_experiment.py` writes these URLs to `targets/G2/slug.txt` and `targets/G3/slug.txt`.
- **Original hostname**: `http://<source-host>/`, after `sudo python3 scripts/configure_hosts.py --apply`. The URLs are written to `targets/G2/target.txt` and `targets/G3/target.txt`. Hostname routing works through the `prod` profile. Domains on a browser's HSTS preload list may be upgraded to HTTPS and fail to load locally.

## Serving and safety

The backend renders `raw/page.mhtml` on demand (`backend/app/manual_render.py`). It inlines every subresource, removes all scripts and inline event handlers, and disables forms and links. A small offline handler lets common cookie-consent buttons close their overlay. Phishing and benign samples use the same gate and the same rendering path.

Never restore credential collection, form submission, or outbound network calls from a served sample.
