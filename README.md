# PhishGate

**PhishGate** places interaction gates (Click, Interaction, Challenge) in front of web pages without modifying the pages. The page behind a gate is revealed only after the gate is completed. **PhishGate-Bench** applies these gates to phishing and benign pages, so each page can be compared between an Original (no-gate) condition and Gated conditions. Gate completion is logged on the server, separately from the detector's verdict, so you can check whether a correct verdict was based on the hidden content.

This repository contains the framework and benchmark from the master's thesis
*PhishGate: Benchmarking Phishing Website Detectors under Interaction-Gated Cloaking* (Sungkyunkwan University, 2026).
The detection agent from the same thesis is available at [PhishWalk](https://github.com/ehddy/PhishWalk).

<p align="center">
  <img src="docs/images/phishgate-overview.png" alt="Overview of PhishGate" width="90%">
</p>

PhishGate runs as a local reverse proxy, inspired by Cloaken from [PhishDecloaker](https://www.usenix.org/conference/usenixsecurity24/presentation/teoh). Cloaken applies only CAPTCHAs, while PhishGate supports three gate families.

## Gate templates

PhishGate has 3 gate families and 18 templates, all modeled on gates reported in research and threat-intelligence reports. Each template reproduces only the required interaction and the main screen layout. Original screens and impersonated brands are not copied. Layout, text, and color theme can vary without changing the completion condition, and a fixed seed reproduces the same screens. The experiments use the `neutral` context, which shows no brand information on the gate. See [docs/TEMPLATES.md](docs/TEMPLATES.md) for every variant.

| Family | Completion condition | Templates |
|---|---|---|
| Click | One click or a browser-dialog response | 7 |
| Interaction | A pointer gesture or scrolling | 5 |
| Challenge | An answer validated by the server | 6 |

<details open>
<summary><b>Click</b></summary>

| `alert` | `cookie-consent` | `cloudflare-checkbox` |
|---|---|---|
| <img src="docs/images/templates/alert.png" alt="alert" width="100%"> | <img src="docs/images/templates/cookie-consent.png" alt="cookie-consent" width="100%"> | <img src="docs/images/templates/cloudflare-checkbox.png" alt="cloudflare-checkbox" width="100%"> |
| `document-ready` | `notification-confirm` | `security-check` |
| <img src="docs/images/templates/document-ready.png" alt="document-ready" width="100%"> | <img src="docs/images/templates/notification-confirm.png" alt="notification-confirm" width="100%"> | <img src="docs/images/templates/security-check.png" alt="security-check" width="100%"> |
| `blurred-preview` | | |
| <img src="docs/images/templates/blurred-preview.png" alt="blurred-preview" width="100%"> | | |

</details>

<details open>
<summary><b>Interaction</b></summary>

| `movement-verify` | `press-and-hold` | `slide-to-verify` |
|---|---|---|
| <img src="docs/images/templates/movement-verify.png" alt="movement-verify" width="100%"> | <img src="docs/images/templates/press-and-hold.png" alt="press-and-hold" width="100%"> | <img src="docs/images/templates/slide-to-verify.png" alt="slide-to-verify" width="100%"> |
| `terms-scroll` | `below-fold-reveal` | |
| <img src="docs/images/templates/terms-scroll.png" alt="terms-scroll" width="100%"> | <img src="docs/images/templates/below-fold-reveal.png" alt="below-fold-reveal" width="100%"> | |

</details>

<details open>
<summary><b>Challenge</b></summary>

| `custom-digit` | `math-challenge` | `image-grid` |
|---|---|---|
| <img src="docs/images/templates/custom-digit.png" alt="custom-digit" width="100%"> | <img src="docs/images/templates/math-challenge.png" alt="math-challenge" width="100%"> | <img src="docs/images/templates/image-grid.png" alt="image-grid" width="100%"> |
| `text-captcha` | `area-select` | `rotate-upright` |
| <img src="docs/images/templates/text-captcha.png" alt="text-captcha" width="100%"> | <img src="docs/images/templates/area-select.png" alt="area-select" width="100%"> | <img src="docs/images/templates/rotate-upright.png" alt="rotate-upright" width="100%"> |

</details>

### Templates at a glance

No template uses external scripts, tracking, credential collection, or real CAPTCHA services. The full reference list is in [docs/TEMPLATES.md](docs/TEMPLATES.md#references).

| Family | Template | Completion condition | Reference basis |
|---|---|---|---|
| Click | `alert` | Dismiss native JavaScript dialog | [CrawlPhish](https://sefcom.asu.edu/publications/crawlphish-oakland21.pdf) |
| | `cookie-consent` | Click consent action | [Keep Aware](https://keepaware.com/blog/fake-cookie-consent-used-as-a-phishing-gateway) |
| | `cloudflare-checkbox` | Activate verification checkbox | [phish.report](https://phish.report/blog/fake-cloudflare-interstitials); [Sophos X-Ops](https://www.sophos.com/blog/svg-phishing); [AhnLab ASEC](https://asec.ahnlab.com/ko/87057/) |
| | `document-ready` | Click Continue | [LevelBlue SpiderLabs](https://www.levelblue.com/blogs/spiderlabs-blog/the-infrastructure-relay-inside-multi-stage-phishing-redirection-chains) |
| | `notification-confirm` | Click Allow | [CrawlPhish](https://sefcom.asu.edu/publications/crawlphish-oakland21.pdf); [MalwareTips](https://malwaretips.com/blogs/cloudflare-captcha-com/); [Netskope Threat Labs](https://threatlabs.netskope.com/blog/2025/04/new-evasive-campaign-delivers-legionloader-via-fake-captcha-cloudflare-turnstile) |
| | `security-check` | Click Continue | [Palo Alto Networks Unit 42](https://unit42.paloaltonetworks.com/cybersquatting/); [Volexity](https://www.volexity.com/blog/2025/02/13/multiple-russian-threat-actors-targeting-microsoft-device-code-authentication/) |
| | `blurred-preview` | Click View/Continue | [Zscaler ThreatLabz](https://www.zscaler.com/blogs/security-research/new-voicemail-themed-phishing-attacks-use-evasion-techniques-and-steal-credentials); [SANS ISC](https://isc.sans.edu/diary/21207) |
| Interaction | `movement-verify` | Move pointer into target area | [Cofense](https://cofense.com/blog/immunity-evasion-defeating-security-with-active-measures-long-lived-domains) |
| | `press-and-hold` | Hold primary pointer for 3 s | [xorlab](https://www.xorlab.com/en/blog/abusing-adobe-and-qr-links-for-aitm-microsoft-365-phishing); [HUMAN Security](https://www.humansecurity.com/learn/blog/human-challenge-improved-bot-protection-with-better-user-experience/) |
| | `slide-to-verify` | Drag slider to ≥94% and release | [Proofpoint](https://www.proofpoint.com/us/blog/threat-insight/ta4922-suspected-chinese-crime-group-going-global); [xorlab](https://www.xorlab.com/en/blog/abusing-adobe-and-qr-links-for-aitm-microsoft-365-phishing) |
| | `terms-scroll` | Scroll to ≥90% | [Palo Alto Networks Unit 42](https://unit42.paloaltonetworks.com/unit42-sofacy-uses-dealerschoice-target-european-government-agency/); [IT Solver](https://support.itsolver.net/hc/en-au/articles/14243666809103-Gmail-Bounce-Phishing-Email-Analysis); [SANS ISC](https://isc.sans.edu/diary/23641); [Boulila et al.](https://doi.org/10.1109/DSN64029.2025.00066) |
| | `below-fold-reveal` | Scroll to ≥82% | [IT Solver](https://support.itsolver.net/hc/en-au/articles/14243666809103-Gmail-Bounce-Phishing-Email-Analysis) |
| Challenge | `custom-digit` | Enter displayed 5-digit code | [PhishEye](https://phisheye.com/blog/hotel-booking-phishing-reservation-hijack); [Keep Aware](https://keepaware.com/blog/gated-phishing-and-how-bec-continues-to-evade-security-filters) |
| | `math-challenge` | Enter correct arithmetic answer | [Proofpoint](https://www.proofpoint.com/us/blog/threat-insight/cybercriminals-abuse-ai-website-creation-app-phishing) |
| | `image-grid` | Select all matching cells in 3×3 grid | [Palo Alto Networks Unit 42](https://unit42.paloaltonetworks.com/captcha-protected-phishing/); [eSentire TRU](https://www.esentire.com/blog/phish-chips-serving-up-tycoon-2fas-secrets) |
| | `text-captcha` | Enter displayed alphanumeric string | [eSentire TRU](https://www.esentire.com/blog/phish-chips-serving-up-tycoon-2fas-secrets) |
| | `area-select` | Select region containing target object | [PhishDecloaker](https://www.usenix.org/conference/usenixsecurity24/presentation/teoh) |
| | `rotate-upright` | Rotate image to upright orientation | [PhishDecloaker](https://www.usenix.org/conference/usenixsecurity24/presentation/teoh) |

### Gates observed in the wild

These gates were found on live phishing sites in our field study. Each one is labeled with the most similar template and shows the gate (left) and the page that PhishWalk reached after passing it (right).

<p align="center"><img src="docs/images/field-study-1.png" alt="cookie-consent and cloudflare-checkbox gates" width="90%"></p>
<p align="center"><img src="docs/images/field-study-2.png" alt="document-ready and notification-confirm gates" width="90%"></p>
<p align="center"><img src="docs/images/field-study-3.png" alt="security-check and blurred-preview gates" width="90%"></p>
<p align="center"><img src="docs/images/field-study-4.png" alt="slide-to-verify and math-challenge gates" width="90%"></p>

## Quick start

**Demo** (no dataset needed):

```bash
cp .env.example .env
docker compose --profile demo up --build
```

Open `http://127.0.0.1/` and complete the gate. To choose a gate, set `PHISHGATE_PROFILE` to `click`, `interaction`, `challenge`, or a single template such as `click-alert` (see [`config/profiles.yaml`](config/profiles.yaml)):

```bash
PHISHGATE_PROFILE=interaction-slide-to-verify docker compose --profile demo up --build
```

**Your own page:** to gate your own static site, replace the files in `demo/upstream/`. To use Conda instead, set these values in `.env`:

```ini
PHISHGATE_GENERIC_UPSTREAM=on
PHISHGATE_UPSTREAM=http://127.0.0.1:8081   # your local server
PHISHGATE_EXPERIMENT_MANIFEST=
PHISHGATE_DOMAIN_STYLE=off
PHISHGATE_PORT=8080
```

Then run:

```bash
PHISHGATE_SETUP_NODE=1 bash setup_environment.sh
conda run -n PhishGate-node npm --prefix frontend run build
conda activate PhishGate && python3 tools/conda/run.py
```

Generic mode serves one upstream per run. Completing the gate once unlocks the whole site for that session.

## PhishGate-Bench

<p align="center">
  <img src="docs/images/phishgate-bench-construction.png" alt="Construction of PhishGate-Bench" width="90%">
</p>

| Group | Label | Source | Samples |
|---|---|---|---:|
| G1 | Phishing | PHP kits from PhishDecloaker (75) and DynaPD (75) | 150 |
| G2 | Phishing | Inert snapshots of live phishing pages | 100 |
| G3 | Benign | Inert snapshots of login, form, and general pages | 200 |

Each sample is served under four conditions: Original, Click, Interaction, and Challenge. In each gated condition, a fixed seed assigns one template from that family and balances templates within each group, so results can be compared pair by pair on the same page. A gate counts as passed only when PhishGate verifies the completion condition and serves the original page. A further 50 G1 kits in `config/cohort.csv` are used only for preliminary backbone selection.

**Data:**

- **G2 and G3:** download them from Zenodo (`<ZENODO-DOI>`) into `tmp/dataset-bundles/`, then run:

  ```bash
  python3 scripts/dataset_bundle.py unpack --groups manual-phishing manual-benign
  ```

- **G1:** this repository does not redistribute G1. Get it from the original authors:
  - [PhishDecloaker](https://doi.org/10.5281/zenodo.11228974): extract the kits to `data/private/phishdecloaker/extracted/src/kit1` through `kit100`.
  - [DynaPD](https://github.com/lindsey98/DynaPD): place the 100 kits listed in [`data/private/dynapd/selection.csv`](data/private/dynapd/selection.csv) under `data/private/dynapd/raw_selected/`.

**Run:**

```bash
cp .env.example .env                               # reference seed used in the thesis
python3 scripts/prepare_experiment.py              # build the seed-fixed targets
sudo python3 scripts/configure_hosts.py --apply    # map local hostnames
docker compose up --build                          # PHISHGATE_PROFILE: baseline, click, interaction, challenge
```

Each completed gate is logged to `logs/*.jsonl`. The log records completion metadata only, never submitted values. See [scripts/README.md](scripts/README.md) for details.

## Responsible use

Run PhishGate only on loopback or an isolated network you control, and use only synthetic values. PhishGate never accepts arbitrary per-request proxy targets. PHP mail, outbound network access, command execution, and uploads are disabled. Challenge gates are not meant to reproduce or bypass commercial CAPTCHA services. They exist to measure, reproducibly, how content-access requirements affect detectors.

## Citation

```bibtex
@mastersthesis{kim2026phishgate,
  title  = {PhishGate: Benchmarking Phishing Website Detectors under Interaction-Gated Cloaking},
  author = {Kim, Dongyo},
  school = {Sungkyunkwan University},
  year   = {2026}
}
```

## License

Code: [MIT](LICENSE). The G2/G3 data follows the terms of its Zenodo record. G1 kits remain under their original authors' terms.
