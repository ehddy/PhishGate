# Benign Sample Selection Methodology

This document records how the `benign`-labeled half of `data/manual/samples/`
was selected, so the sampling design is auditable rather than an unexplained
pile of URLs. It only covers *selection criteria*; see `data/manual/README.md`
for the collection tool, storage layout, and serving mechanism.

## Why a designed sample instead of an indiscriminate crawl

A detector that only ever sees phishing pages behind an interaction gate has
no negative examples to calibrate against. Conversely, a benign set containing
only ordinary home pages makes the label partly predictable from page purpose:
phishing pages tend to imitate authentication or data-entry flows. The final
benign corpus therefore crosses two independent variables -- page purpose and
site popularity -- rather than treating either as an incidental property.

## Final 2 x 2 design (200 accepted samples)

| Primary page purpose | Popular | Long-tail | Row total |
|---|---:|---:|---:|
| Form | 50 | 50 | 100 |
| General | 50 | 50 | 100 |
| Column total | 100 | 100 | 200 |

The equal cells are an experimental control, not an estimate of the natural
Web distribution. Results must report false-positive rate both overall and
for all four cells; otherwise a good result on easy general pages could hide a
poor result on legitimate login pages or unfamiliar brands.

### Page-purpose rule

- `form`: the page's primary visible task is login, sign-up, account recovery,
  payment, booking, or another deliberate user-data-entry flow. Search boxes,
  newsletter fields, cookie controls, and a form hidden behind a further click
  do not make an otherwise ordinary page a `form` sample.
- `general`: the primary visible task is consuming or navigating legitimate
  content (for example a home, product, documentation, news, government, or
  informational page). A header login link or incidental search field is
  allowed, but an authentication/data-entry panel must not dominate the first
  observation.

This split is grounded in phishing-detection work showing that benign home
pages and benign login pages are not interchangeable controls. PILU-90K
explicitly separates legitimate home pages from legitimate login pages, while
PILWD reports that training with legitimate home pages can raise false
positives on legitimate login pages. See the references below.

### Popularity rule

"Famous" is not assigned from researcher intuition or national brand
recognition. The stored label is `popular` or `long_tail`, determined only from
the frozen standard Tranco list:

- snapshot: Tranco list [`Y8YYG`](https://tranco-list.eu/list/Y8YYG), generated
  2026-09-22;
- downloaded top-1M CSV SHA-256:
  `1953f1ce7afa915fa11b8d5356be072bc8ff95e87c8ef67eec1756569b8d12a5`;
- rank lookup key: the page hostname reduced to the pay-level domain used by
  Tranco (for example `accounts.google.com` -> `google.com`);
- `popular`: rank 1--5,000 inclusive;
- `long_tail`: rank 5,001--1,000,000 inclusive; and
- absent from the snapshot: ineligible for the confirmatory 200 and retained,
  if useful, only as a separately reported exploratory sample.

The 5,000 boundary is fixed before outcome measurement. It creates a sharp,
auditable contrast while leaving a large long-tail sampling frame. Tranco is
used because it aggregates several rankings over 30 days and provides a
permanent list identifier; it is still a traffic proxy, not a direct measure
of whether a person in one country recognizes a brand.

### Orthogonal tags and diversity controls

`brand_relation` is recorded independently as `kit_matched` when the official
site corresponds to a brand in `data/kit_brand_annotation.csv`, otherwise
`unmatched`. It does not override Tranco popularity and is not a fifth cell.
This preserves paired real-brand/phishing-kit analyses without silently
turning "brand matched" into a synonym for "popular".

Candidate proposal is additionally checked for sector, market, and visible
language diversity. The target is 60--80% English UI and 20--40% intentional
non-English UI spread across at least five locale/market groups; no single
non-English locale should exceed 10% of the full corpus. A non-English page is
included only as an intentional member of that distribution, never merely
because of the collection environment's locale. These are corpus-level diversity checks, not rules
that can change a page's 2 x 2 cell.

## Historical candidate pool

The first candidate pool used free-text axes `brand_matched`, `famous`,
`long_tail`, and `non_credential`. Those values describe how URLs were
proposed, not the final benchmark strata. `data/manual/tranco_rank_audit.csv`
preserves the original 2026-09-12 ranking pass, and
`data/manual/benign_review.csv` preserves the later visual accept/exclude
decision. Final samples instead carry the structured 2 x 2 fields described
above in `source.yaml` and the generated benign annotation CSV.

## Mandatory visual acceptance review

Candidate selection and capture success do not make a sample benchmark-ready.
Before inclusion, inspect `raw/screenshot.png` and retain the sample only when:

- the initial capture clearly satisfies its declared `page_type` definition;
- no cookie/consent dialog, locale chooser, newsletter prompt, advertisement,
  or other incidental popup obscures the page;
- the page is not an access-denied, unavailable, loading-only, blank, or visibly
  broken render;
- the page is not itself an anti-bot interaction challenge that would confound
  the PhishGate condition; and
- its visible language is intentional for geographic diversity rather than an
  accidental result of the collection environment's locale.

The 2026-09-23 review reduced the original 493 candidates to 65 retained form
samples; `benign_review.csv` remains the decision ledger for that initial pass.
The follow-up collection was completed on 2026-09-25 without restoring rejected
candidates: every added sample was re-captured and visually reviewed. The final
set contains exactly 200 accepted samples, with 50 in each `form/general` x
`popular/long_tail` cell.

## Per-sample provenance

Every accepted benign sample's `source.yaml` records structured benchmark
metadata, for example:

```yaml
benchmark:
  page_type: form
  popularity: popular
  tranco_rank: 1
  tranco_list_id: Y8YYG
  brand_relation: kit_matched
  review_status: accepted
  reviewed_at: "2026-09-23"
```

Free-text `notes` may explain a choice but never defines a stratum. The four-cell
breakdown can be recomputed from the generated annotation columns:

```text
page_type,popularity,tranco_rank,tranco_list_id,brand_relation
```

## Collection mechanics (what "collected" means here)

Every sample is a single real page load:
one `GET` of the page's own HTML plus one headless-Chromium render (with a
brief scripted mouse/scroll interaction to satisfy pages that gate content
behind basic activity checks), producing `raw/index.html`, `raw/rendered.html`,
`raw/screenshot.png`, and `raw/page.mhtml`. No credentials are ever entered,
no form is ever submitted, and nothing beyond the single page itself is
fetched. Benchmark captures send `Accept-Language: en-US,en;q=0.9` and
use Chromium locale `en-US` with timezone `America/New_York`. IP-geolocated content is not spoofed, so a page
that still renders an unintended region/language is rejected or deliberately
re-collected from an approved environment. Samples where the initial fetch was rejected (bot/automation
detection on the fetch itself) or where the render step could not complete
were excluded rather than retried indefinitely with a different technique --
that exclusion pattern (concentrated in banking and social-platform brands
with aggressive anti-automation defenses) is a real, expected property of
this collection method, not a shortcoming to work around.

## Known limitations

- **Global rank vs. market-specific recognition.** The popular/long-tail cutoff
  (Tranco global rank <= 5,000) measures worldwide traffic, not "would a
  typical user/detector recognize this brand." A few single-country
  financial brands can land in the long-tail stratum under this rule despite being well-known within their own
  market. No correction is applied for this -- the rule is kept simple and
  reproducible rather than patched with a second, subjective "well-known
  nationally" exception list.
- **Snapshot is a single point in time.** The daily list changes composition
  slightly; a domain near rank 5,000 could cross the boundary on another day.
  The final corpus therefore freezes permanent list ID `Y8YYG` instead of
  re-querying a current rank during later collection sessions.
- **Snapshot drift.** Every sample is a point-in-time capture; a brand's real
  login page can change its design after collection. `collected_at` in each
  `source.yaml` is the reference timestamp for what was actually observed.
- **Not a probability sample.** Popularity *membership* is a hard rule on
  Tranco rank (see above), but candidate *proposal* within each axis still
  comes from researcher judgment (sector/geographic diversity, URL
  reachability) rather than uniform random draws from Tranco's ranked list.
  The axis boundaries are deliberate, rank-verified strata, not a
  statistically representative sample of the web.

## Method references

- Victor Le Pochat et al., "Tranco: A Research-Oriented Top Sites Ranking
  Hardened Against Manipulation," NDSS 2019,
  <https://doi.org/10.14722/ndss.2019.23386>.
- Y. Alsariera et al., "Phishing URL Detection: A Real-Case Scenario Through
  Login URLs," *IEEE Access* 2022 (PILU-90K),
  <https://doi.org/10.1109/ACCESS.2022.3168681>.
- "PILWD: A phishing data set based on legitimate login web pages," *Expert
  Systems with Applications* 2022,
  <https://www.sciencedirect.com/science/article/pii/S0957417422012301>.
