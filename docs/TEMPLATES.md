# Gate Templates

PhishGate has three gate families and 18 templates. A **gate family** defines the completion condition. A **template** defines how that condition is presented. Templates in the same family share one completion handler.

When a profile lists several templates, the backend assigns one template per sample deterministically from the seed (`backend/app/template_assignment.py`). Assignments are balanced within each benchmark group.

## Presentation variants

Each gate is also rendered with a presentation context chosen from the seed (`backend/app/presentation.py`), so a detector cannot recognize a gate by one fixed appearance. The allowed values are defined in `frontend/src/gates/variants.ts`.

| Axis | Values | Effect |
|---|---|---|
| `context_mode` | `neutral`, `brand-label` | Hides or shows the sample's annotated brand in the shell |
| `layout_variant` | `centered`, `compact` | Card composition and density |
| `copy_variant` | `concise`, `standard`, `detailed` | Amount of visible text; never changes the completion condition |
| `theme_variant` | `blue`, `mint`, `slate`, `violet` | Accent color of the shell |

The gallery below shows every template with each value of each axis. The other axes are held at their baseline. The `alert` template uses a native browser dialog, so its screenshots show the page beneath the dialog.

## Design references

Each template is modeled on gates reported in academic studies and industry threat-intelligence reports. The main [README](../README.md#template-references) maps every template to its sources. For each template, the figure used, the retained design patterns, and the local adaptations are recorded in `frontend/src/gates/<family>/templates/<template>/reference.yaml`. No third-party scripts, logos, tracking, form actions, or real CAPTCHA services are used.

## References

**Academic studies**

| Source | Templates |
|---|---|
| P. Zhang et al., "[CrawlPhish: Large-scale Analysis of Client-side Cloaking Techniques in Phishing](https://sefcom.asu.edu/publications/crawlphish-oakland21.pdf)," IEEE S&P, 2021 | `alert`, `notification-confirm` |
| X. Teoh et al., "[PhishDecloaker: Detecting CAPTCHA-cloaked Phishing Websites via Hybrid Vision-based Interactive Models](https://www.usenix.org/conference/usenixsecurity24/presentation/teoh)," USENIX Security, 2024 | `area-select`, `rotate-upright` |
| E. Boulila et al., "[A Closer Look At Modern Evasive Phishing Emails](https://doi.org/10.1109/DSN64029.2025.00066)," IEEE/IFIP DSN, 2025 | `terms-scroll` |

**Industry reports**

| Publisher | Title | Templates |
|---|---|---|
| AhnLab ASEC | [SVG Phishing Malware Distributed with Analysis-Obstruction Features](https://asec.ahnlab.com/ko/87057/) | `cloudflare-checkbox` |
| Cofense | [Immunity Evasion: Defeating Security with Active Measures & Long-Lived Domains](https://cofense.com/blog/immunity-evasion-defeating-security-with-active-measures-long-lived-domains) | `movement-verify` |
| eSentire TRU | [Phish & Chips: Serving Up Tycoon 2FA's Secrets](https://www.esentire.com/blog/phish-chips-serving-up-tycoon-2fas-secrets) | `image-grid`, `text-captcha` |
| HUMAN Security | [Human Challenge: Improved Bot Protection with Better User Experience](https://www.humansecurity.com/learn/blog/human-challenge-improved-bot-protection-with-better-user-experience/) | `press-and-hold` |
| IT Solver | [Gmail Bounce Phishing Email Analysis](https://support.itsolver.net/hc/en-au/articles/14243666809103-Gmail-Bounce-Phishing-Email-Analysis) | `terms-scroll`, `below-fold-reveal` |
| Keep Aware | [Fake Cookie Consent Used as a Phishing Gateway](https://keepaware.com/blog/fake-cookie-consent-used-as-a-phishing-gateway) | `cookie-consent` |
| Keep Aware | [Gated Phishing and How BEC Continues to Evade Security Filters](https://keepaware.com/blog/gated-phishing-and-how-bec-continues-to-evade-security-filters) | `custom-digit` |
| LevelBlue SpiderLabs | [The Infrastructure Relay: Inside Multi-Stage Phishing Redirection Chains](https://www.levelblue.com/blogs/spiderlabs-blog/the-infrastructure-relay-inside-multi-stage-phishing-redirection-chains) | `document-ready` |
| MalwareTips | [The Truth About Cloudflare-captcha.com and Its Spam Pop-ups](https://malwaretips.com/blogs/cloudflare-captcha-com/) | `notification-confirm` |
| Netskope Threat Labs | [New Evasive Campaign Delivers LegionLoader via Fake CAPTCHA & CloudFlare Turnstile](https://threatlabs.netskope.com/blog/2025/04/new-evasive-campaign-delivers-legionloader-via-fake-captcha-cloudflare-turnstile) | `notification-confirm` |
| Palo Alto Networks Unit 42 | [Cybersquatting: Attackers Mimicking Domains of Major Brands Including Facebook, Apple, Amazon and Netflix to Scam Consumers](https://unit42.paloaltonetworks.com/cybersquatting/) | `security-check` |
| Palo Alto Networks Unit 42 | [Discovering CAPTCHA Protected Phishing Campaigns](https://unit42.paloaltonetworks.com/captcha-protected-phishing/) | `image-grid` |
| Palo Alto Networks Unit 42 | [Sofacy Uses DealersChoice to Target European Government Agency](https://unit42.paloaltonetworks.com/unit42-sofacy-uses-dealerschoice-target-european-government-agency/) | `terms-scroll` |
| PhishEye | [Hotel Booking Phishing: Reservation Hijack](https://phisheye.com/blog/hotel-booking-phishing-reservation-hijack) | `custom-digit` |
| phish.report | [Evading security scanners with fake Cloudflare interstitials](https://phish.report/blog/fake-cloudflare-interstitials) | `cloudflare-checkbox` |
| Proofpoint | [Cybercriminals Abuse AI Website Creation App For Phishing](https://www.proofpoint.com/us/blog/threat-insight/cybercriminals-abuse-ai-website-creation-app-phishing) | `math-challenge` |
| Proofpoint | [TA4922: The Suspected Chinese Crime Group is Going Global](https://www.proofpoint.com/us/blog/threat-insight/ta4922-suspected-chinese-crime-group-going-global) | `slide-to-verify` |
| SANS ISC | [Nice Phishing Sample Delivering Trickbot](https://isc.sans.edu/diary/23641) | `terms-scroll` |
| SANS ISC | [Phishing Campaign with Blurred Images](https://isc.sans.edu/diary/21207) | `blurred-preview` |
| Sophos X-Ops | [Scalable Vector Graphics files pose a novel phishing threat](https://www.sophos.com/blog/svg-phishing) | `cloudflare-checkbox` |
| Volexity | [Multiple Russian Threat Actors Targeting Microsoft Device Code Authentication](https://www.volexity.com/blog/2025/02/13/multiple-russian-threat-actors-targeting-microsoft-device-code-authentication/) | `security-check` |
| xorlab | [Abusing Adobe and QR Links for AITM Microsoft 365 Phishing](https://www.xorlab.com/en/blog/abusing-adobe-and-qr-links-for-aitm-microsoft-365-phishing) | `press-and-hold`, `slide-to-verify` |
| Zscaler ThreatLabz | [New Voicemail-Themed Phishing Attacks Use Evasion Techniques and Steal Credentials](https://www.zscaler.com/blogs/security-research/new-voicemail-themed-phishing-attacks-use-evasion-techniques-and-steal-credentials) | `blurred-preview` |

## Click

Completion requires one explicit click or a response to a browser dialog.

### `alert`

Native JavaScript alert interstitial. Completes when the dialog is dismissed.

<p align="center"><img src="images/templates/alert.png" alt="alert gate" width="70%"></p>

<details>
<summary>Presentation variants</summary>


**Context mode**

| `neutral` | `brand-label` |
|---|---|
| <img src="images/variant-matrix/alert/context_mode-neutral.png" alt="alert neutral" width="100%"> | <img src="images/variant-matrix/alert/context_mode-brand-label.png" alt="alert brand-label" width="100%"> |

**Layout**

| `centered` | `compact` |
|---|---|
| <img src="images/variant-matrix/alert/layout_variant-centered.png" alt="alert centered" width="100%"> | <img src="images/variant-matrix/alert/layout_variant-compact.png" alt="alert compact" width="100%"> |

**Copy**

| `concise` | `standard` | `detailed` |
|---|---|---|
| <img src="images/variant-matrix/alert/copy_variant-concise.png" alt="alert concise" width="100%"> | <img src="images/variant-matrix/alert/copy_variant-standard.png" alt="alert standard" width="100%"> | <img src="images/variant-matrix/alert/copy_variant-detailed.png" alt="alert detailed" width="100%"> |

**Theme**

| `blue` | `mint` | `slate` | `violet` |
|---|---|---|---|
| <img src="images/variant-matrix/alert/theme_variant-blue.png" alt="alert blue" width="100%"> | <img src="images/variant-matrix/alert/theme_variant-mint.png" alt="alert mint" width="100%"> | <img src="images/variant-matrix/alert/theme_variant-slate.png" alt="alert slate" width="100%"> | <img src="images/variant-matrix/alert/theme_variant-violet.png" alt="alert violet" width="100%"> |

</details>

### `cookie-consent`

Cookie-consent overlay shown as a centered modal, bottom banner, or side panel. Completes on the consent action.

<p align="center"><img src="images/templates/cookie-consent.png" alt="cookie-consent gate" width="70%"></p>

<details>
<summary>Presentation variants</summary>


**Context mode**

| `neutral` | `brand-label` |
|---|---|
| <img src="images/variant-matrix/cookie-consent/context_mode-neutral.png" alt="cookie-consent neutral" width="100%"> | <img src="images/variant-matrix/cookie-consent/context_mode-brand-label.png" alt="cookie-consent brand-label" width="100%"> |

**Layout**

| `centered` | `compact` |
|---|---|
| <img src="images/variant-matrix/cookie-consent/layout_variant-centered.png" alt="cookie-consent centered" width="100%"> | <img src="images/variant-matrix/cookie-consent/layout_variant-compact.png" alt="cookie-consent compact" width="100%"> |

**Copy**

| `concise` | `standard` | `detailed` |
|---|---|---|
| <img src="images/variant-matrix/cookie-consent/copy_variant-concise.png" alt="cookie-consent concise" width="100%"> | <img src="images/variant-matrix/cookie-consent/copy_variant-standard.png" alt="cookie-consent standard" width="100%"> | <img src="images/variant-matrix/cookie-consent/copy_variant-detailed.png" alt="cookie-consent detailed" width="100%"> |

**Theme**

| `blue` | `mint` | `slate` | `violet` |
|---|---|---|---|
| <img src="images/variant-matrix/cookie-consent/theme_variant-blue.png" alt="cookie-consent blue" width="100%"> | <img src="images/variant-matrix/cookie-consent/theme_variant-mint.png" alt="cookie-consent mint" width="100%"> | <img src="images/variant-matrix/cookie-consent/theme_variant-slate.png" alt="cookie-consent slate" width="100%"> | <img src="images/variant-matrix/cookie-consent/theme_variant-violet.png" alt="cookie-consent violet" width="100%"> |

</details>

### `cloudflare-checkbox`

Local human-verification card modeled on common checkbox gates. Completes when the checkbox is selected. It does not contact Cloudflare.

<p align="center"><img src="images/templates/cloudflare-checkbox.png" alt="cloudflare-checkbox gate" width="70%"></p>

<details>
<summary>Presentation variants</summary>


**Context mode**

| `neutral` | `brand-label` |
|---|---|
| <img src="images/variant-matrix/cloudflare-checkbox/context_mode-neutral.png" alt="cloudflare-checkbox neutral" width="100%"> | <img src="images/variant-matrix/cloudflare-checkbox/context_mode-brand-label.png" alt="cloudflare-checkbox brand-label" width="100%"> |

**Layout**

| `centered` | `compact` |
|---|---|
| <img src="images/variant-matrix/cloudflare-checkbox/layout_variant-centered.png" alt="cloudflare-checkbox centered" width="100%"> | <img src="images/variant-matrix/cloudflare-checkbox/layout_variant-compact.png" alt="cloudflare-checkbox compact" width="100%"> |

**Copy**

| `concise` | `standard` | `detailed` |
|---|---|---|
| <img src="images/variant-matrix/cloudflare-checkbox/copy_variant-concise.png" alt="cloudflare-checkbox concise" width="100%"> | <img src="images/variant-matrix/cloudflare-checkbox/copy_variant-standard.png" alt="cloudflare-checkbox standard" width="100%"> | <img src="images/variant-matrix/cloudflare-checkbox/copy_variant-detailed.png" alt="cloudflare-checkbox detailed" width="100%"> |

**Theme**

| `blue` | `mint` | `slate` | `violet` |
|---|---|---|---|
| <img src="images/variant-matrix/cloudflare-checkbox/theme_variant-blue.png" alt="cloudflare-checkbox blue" width="100%"> | <img src="images/variant-matrix/cloudflare-checkbox/theme_variant-mint.png" alt="cloudflare-checkbox mint" width="100%"> | <img src="images/variant-matrix/cloudflare-checkbox/theme_variant-slate.png" alt="cloudflare-checkbox slate" width="100%"> | <img src="images/variant-matrix/cloudflare-checkbox/theme_variant-violet.png" alt="cloudflare-checkbox violet" width="100%"> |

</details>

### `document-ready`

Document-preparation card. Completes on Continue.

<p align="center"><img src="images/templates/document-ready.png" alt="document-ready gate" width="70%"></p>

<details>
<summary>Presentation variants</summary>


**Context mode**

| `neutral` | `brand-label` |
|---|---|
| <img src="images/variant-matrix/document-ready/context_mode-neutral.png" alt="document-ready neutral" width="100%"> | <img src="images/variant-matrix/document-ready/context_mode-brand-label.png" alt="document-ready brand-label" width="100%"> |

**Layout**

| `centered` | `compact` |
|---|---|
| <img src="images/variant-matrix/document-ready/layout_variant-centered.png" alt="document-ready centered" width="100%"> | <img src="images/variant-matrix/document-ready/layout_variant-compact.png" alt="document-ready compact" width="100%"> |

**Copy**

| `concise` | `standard` | `detailed` |
|---|---|---|
| <img src="images/variant-matrix/document-ready/copy_variant-concise.png" alt="document-ready concise" width="100%"> | <img src="images/variant-matrix/document-ready/copy_variant-standard.png" alt="document-ready standard" width="100%"> | <img src="images/variant-matrix/document-ready/copy_variant-detailed.png" alt="document-ready detailed" width="100%"> |

**Theme**

| `blue` | `mint` | `slate` | `violet` |
|---|---|---|---|
| <img src="images/variant-matrix/document-ready/theme_variant-blue.png" alt="document-ready blue" width="100%"> | <img src="images/variant-matrix/document-ready/theme_variant-mint.png" alt="document-ready mint" width="100%"> | <img src="images/variant-matrix/document-ready/theme_variant-slate.png" alt="document-ready slate" width="100%"> | <img src="images/variant-matrix/document-ready/theme_variant-violet.png" alt="document-ready violet" width="100%"> |

</details>

### `notification-confirm`

In-page notification-permission prompt. Completes on Allow. The native notification API is never called.

<p align="center"><img src="images/templates/notification-confirm.png" alt="notification-confirm gate" width="70%"></p>

<details>
<summary>Presentation variants</summary>


**Context mode**

| `neutral` | `brand-label` |
|---|---|
| <img src="images/variant-matrix/notification-confirm/context_mode-neutral.png" alt="notification-confirm neutral" width="100%"> | <img src="images/variant-matrix/notification-confirm/context_mode-brand-label.png" alt="notification-confirm brand-label" width="100%"> |

**Layout**

| `centered` | `compact` |
|---|---|
| <img src="images/variant-matrix/notification-confirm/layout_variant-centered.png" alt="notification-confirm centered" width="100%"> | <img src="images/variant-matrix/notification-confirm/layout_variant-compact.png" alt="notification-confirm compact" width="100%"> |

**Copy**

| `concise` | `standard` | `detailed` |
|---|---|---|
| <img src="images/variant-matrix/notification-confirm/copy_variant-concise.png" alt="notification-confirm concise" width="100%"> | <img src="images/variant-matrix/notification-confirm/copy_variant-standard.png" alt="notification-confirm standard" width="100%"> | <img src="images/variant-matrix/notification-confirm/copy_variant-detailed.png" alt="notification-confirm detailed" width="100%"> |

**Theme**

| `blue` | `mint` | `slate` | `violet` |
|---|---|---|---|
| <img src="images/variant-matrix/notification-confirm/theme_variant-blue.png" alt="notification-confirm blue" width="100%"> | <img src="images/variant-matrix/notification-confirm/theme_variant-mint.png" alt="notification-confirm mint" width="100%"> | <img src="images/variant-matrix/notification-confirm/theme_variant-slate.png" alt="notification-confirm slate" width="100%"> | <img src="images/variant-matrix/notification-confirm/theme_variant-violet.png" alt="notification-confirm violet" width="100%"> |

</details>

### `security-check`

"Before you continue" security interstitial. Completes on Continue.

<p align="center"><img src="images/templates/security-check.png" alt="security-check gate" width="70%"></p>

<details>
<summary>Presentation variants</summary>


**Context mode**

| `neutral` | `brand-label` |
|---|---|
| <img src="images/variant-matrix/security-check/context_mode-neutral.png" alt="security-check neutral" width="100%"> | <img src="images/variant-matrix/security-check/context_mode-brand-label.png" alt="security-check brand-label" width="100%"> |

**Layout**

| `centered` | `compact` |
|---|---|
| <img src="images/variant-matrix/security-check/layout_variant-centered.png" alt="security-check centered" width="100%"> | <img src="images/variant-matrix/security-check/layout_variant-compact.png" alt="security-check compact" width="100%"> |

**Copy**

| `concise` | `standard` | `detailed` |
|---|---|---|
| <img src="images/variant-matrix/security-check/copy_variant-concise.png" alt="security-check concise" width="100%"> | <img src="images/variant-matrix/security-check/copy_variant-standard.png" alt="security-check standard" width="100%"> | <img src="images/variant-matrix/security-check/copy_variant-detailed.png" alt="security-check detailed" width="100%"> |

**Theme**

| `blue` | `mint` | `slate` | `violet` |
|---|---|---|---|
| <img src="images/variant-matrix/security-check/theme_variant-blue.png" alt="security-check blue" width="100%"> | <img src="images/variant-matrix/security-check/theme_variant-mint.png" alt="security-check mint" width="100%"> | <img src="images/variant-matrix/security-check/theme_variant-slate.png" alt="security-check slate" width="100%"> | <img src="images/variant-matrix/security-check/theme_variant-violet.png" alt="security-check violet" width="100%"> |

</details>

### `blurred-preview`

Blurred document preview behind a view-to-unlock overlay. Completes on the view action.

<p align="center"><img src="images/templates/blurred-preview.png" alt="blurred-preview gate" width="70%"></p>

<details>
<summary>Presentation variants</summary>


**Context mode**

| `neutral` | `brand-label` |
|---|---|
| <img src="images/variant-matrix/blurred-preview/context_mode-neutral.png" alt="blurred-preview neutral" width="100%"> | <img src="images/variant-matrix/blurred-preview/context_mode-brand-label.png" alt="blurred-preview brand-label" width="100%"> |

**Layout**

| `centered` | `compact` |
|---|---|
| <img src="images/variant-matrix/blurred-preview/layout_variant-centered.png" alt="blurred-preview centered" width="100%"> | <img src="images/variant-matrix/blurred-preview/layout_variant-compact.png" alt="blurred-preview compact" width="100%"> |

**Copy**

| `concise` | `standard` | `detailed` |
|---|---|---|
| <img src="images/variant-matrix/blurred-preview/copy_variant-concise.png" alt="blurred-preview concise" width="100%"> | <img src="images/variant-matrix/blurred-preview/copy_variant-standard.png" alt="blurred-preview standard" width="100%"> | <img src="images/variant-matrix/blurred-preview/copy_variant-detailed.png" alt="blurred-preview detailed" width="100%"> |

**Theme**

| `blue` | `mint` | `slate` | `violet` |
|---|---|---|---|
| <img src="images/variant-matrix/blurred-preview/theme_variant-blue.png" alt="blurred-preview blue" width="100%"> | <img src="images/variant-matrix/blurred-preview/theme_variant-mint.png" alt="blurred-preview mint" width="100%"> | <img src="images/variant-matrix/blurred-preview/theme_variant-slate.png" alt="blurred-preview slate" width="100%"> | <img src="images/variant-matrix/blurred-preview/theme_variant-violet.png" alt="blurred-preview violet" width="100%"> |

</details>

## Interaction

Completion requires a pointer gesture or scrolling rather than a single click.

### `movement-verify`

Verification area that completes after real pointer movement enters the target region.

<p align="center"><img src="images/templates/movement-verify.png" alt="movement-verify gate" width="70%"></p>

<details>
<summary>Presentation variants</summary>


**Context mode**

| `neutral` | `brand-label` |
|---|---|
| <img src="images/variant-matrix/movement-verify/context_mode-neutral.png" alt="movement-verify neutral" width="100%"> | <img src="images/variant-matrix/movement-verify/context_mode-brand-label.png" alt="movement-verify brand-label" width="100%"> |

**Layout**

| `centered` | `compact` |
|---|---|
| <img src="images/variant-matrix/movement-verify/layout_variant-centered.png" alt="movement-verify centered" width="100%"> | <img src="images/variant-matrix/movement-verify/layout_variant-compact.png" alt="movement-verify compact" width="100%"> |

**Copy**

| `concise` | `standard` | `detailed` |
|---|---|---|
| <img src="images/variant-matrix/movement-verify/copy_variant-concise.png" alt="movement-verify concise" width="100%"> | <img src="images/variant-matrix/movement-verify/copy_variant-standard.png" alt="movement-verify standard" width="100%"> | <img src="images/variant-matrix/movement-verify/copy_variant-detailed.png" alt="movement-verify detailed" width="100%"> |

**Theme**

| `blue` | `mint` | `slate` | `violet` |
|---|---|---|---|
| <img src="images/variant-matrix/movement-verify/theme_variant-blue.png" alt="movement-verify blue" width="100%"> | <img src="images/variant-matrix/movement-verify/theme_variant-mint.png" alt="movement-verify mint" width="100%"> | <img src="images/variant-matrix/movement-verify/theme_variant-slate.png" alt="movement-verify slate" width="100%"> | <img src="images/variant-matrix/movement-verify/theme_variant-violet.png" alt="movement-verify violet" width="100%"> |

</details>

### `press-and-hold`

Hold control. The benchmark profile requires a continuous 3,000 ms press.

<p align="center"><img src="images/templates/press-and-hold.png" alt="press-and-hold gate" width="70%"></p>

<details>
<summary>Presentation variants</summary>


**Context mode**

| `neutral` | `brand-label` |
|---|---|
| <img src="images/variant-matrix/press-and-hold/context_mode-neutral.png" alt="press-and-hold neutral" width="100%"> | <img src="images/variant-matrix/press-and-hold/context_mode-brand-label.png" alt="press-and-hold brand-label" width="100%"> |

**Layout**

| `centered` | `compact` |
|---|---|
| <img src="images/variant-matrix/press-and-hold/layout_variant-centered.png" alt="press-and-hold centered" width="100%"> | <img src="images/variant-matrix/press-and-hold/layout_variant-compact.png" alt="press-and-hold compact" width="100%"> |

**Copy**

| `concise` | `standard` | `detailed` |
|---|---|---|
| <img src="images/variant-matrix/press-and-hold/copy_variant-concise.png" alt="press-and-hold concise" width="100%"> | <img src="images/variant-matrix/press-and-hold/copy_variant-standard.png" alt="press-and-hold standard" width="100%"> | <img src="images/variant-matrix/press-and-hold/copy_variant-detailed.png" alt="press-and-hold detailed" width="100%"> |

**Theme**

| `blue` | `mint` | `slate` | `violet` |
|---|---|---|---|
| <img src="images/variant-matrix/press-and-hold/theme_variant-blue.png" alt="press-and-hold blue" width="100%"> | <img src="images/variant-matrix/press-and-hold/theme_variant-mint.png" alt="press-and-hold mint" width="100%"> | <img src="images/variant-matrix/press-and-hold/theme_variant-slate.png" alt="press-and-hold slate" width="100%"> | <img src="images/variant-matrix/press-and-hold/theme_variant-violet.png" alt="press-and-hold violet" width="100%"> |

</details>

### `slide-to-verify`

Slider. The benchmark profile completes when the handle reaches 94% of the track.

<p align="center"><img src="images/templates/slide-to-verify.png" alt="slide-to-verify gate" width="70%"></p>

<details>
<summary>Presentation variants</summary>


**Context mode**

| `neutral` | `brand-label` |
|---|---|
| <img src="images/variant-matrix/slide-to-verify/context_mode-neutral.png" alt="slide-to-verify neutral" width="100%"> | <img src="images/variant-matrix/slide-to-verify/context_mode-brand-label.png" alt="slide-to-verify brand-label" width="100%"> |

**Layout**

| `centered` | `compact` |
|---|---|
| <img src="images/variant-matrix/slide-to-verify/layout_variant-centered.png" alt="slide-to-verify centered" width="100%"> | <img src="images/variant-matrix/slide-to-verify/layout_variant-compact.png" alt="slide-to-verify compact" width="100%"> |

**Copy**

| `concise` | `standard` | `detailed` |
|---|---|---|
| <img src="images/variant-matrix/slide-to-verify/copy_variant-concise.png" alt="slide-to-verify concise" width="100%"> | <img src="images/variant-matrix/slide-to-verify/copy_variant-standard.png" alt="slide-to-verify standard" width="100%"> | <img src="images/variant-matrix/slide-to-verify/copy_variant-detailed.png" alt="slide-to-verify detailed" width="100%"> |

**Theme**

| `blue` | `mint` | `slate` | `violet` |
|---|---|---|---|
| <img src="images/variant-matrix/slide-to-verify/theme_variant-blue.png" alt="slide-to-verify blue" width="100%"> | <img src="images/variant-matrix/slide-to-verify/theme_variant-mint.png" alt="slide-to-verify mint" width="100%"> | <img src="images/variant-matrix/slide-to-verify/theme_variant-slate.png" alt="slide-to-verify slate" width="100%"> | <img src="images/variant-matrix/slide-to-verify/theme_variant-violet.png" alt="slide-to-verify violet" width="100%"> |

</details>

### `terms-scroll`

Three-page document viewer. Completes at 90% scroll depth.

<p align="center"><img src="images/templates/terms-scroll.png" alt="terms-scroll gate" width="70%"></p>

<details>
<summary>Presentation variants</summary>


**Context mode**

| `neutral` | `brand-label` |
|---|---|
| <img src="images/variant-matrix/terms-scroll/context_mode-neutral.png" alt="terms-scroll neutral" width="100%"> | <img src="images/variant-matrix/terms-scroll/context_mode-brand-label.png" alt="terms-scroll brand-label" width="100%"> |

**Layout**

| `centered` | `compact` |
|---|---|
| <img src="images/variant-matrix/terms-scroll/layout_variant-centered.png" alt="terms-scroll centered" width="100%"> | <img src="images/variant-matrix/terms-scroll/layout_variant-compact.png" alt="terms-scroll compact" width="100%"> |

**Copy**

| `concise` | `standard` | `detailed` |
|---|---|---|
| <img src="images/variant-matrix/terms-scroll/copy_variant-concise.png" alt="terms-scroll concise" width="100%"> | <img src="images/variant-matrix/terms-scroll/copy_variant-standard.png" alt="terms-scroll standard" width="100%"> | <img src="images/variant-matrix/terms-scroll/copy_variant-detailed.png" alt="terms-scroll detailed" width="100%"> |

**Theme**

| `blue` | `mint` | `slate` | `violet` |
|---|---|---|---|
| <img src="images/variant-matrix/terms-scroll/theme_variant-blue.png" alt="terms-scroll blue" width="100%"> | <img src="images/variant-matrix/terms-scroll/theme_variant-mint.png" alt="terms-scroll mint" width="100%"> | <img src="images/variant-matrix/terms-scroll/theme_variant-slate.png" alt="terms-scroll slate" width="100%"> | <img src="images/variant-matrix/terms-scroll/theme_variant-violet.png" alt="terms-scroll violet" width="100%"> |

</details>

### `below-fold-reveal`

Webmail-style page whose action is below the initial viewport. Completes at 82% scroll depth.

<p align="center"><img src="images/templates/below-fold-reveal.png" alt="below-fold-reveal gate" width="70%"></p>

<details>
<summary>Presentation variants</summary>


**Context mode**

| `neutral` | `brand-label` |
|---|---|
| <img src="images/variant-matrix/below-fold-reveal/context_mode-neutral.png" alt="below-fold-reveal neutral" width="100%"> | <img src="images/variant-matrix/below-fold-reveal/context_mode-brand-label.png" alt="below-fold-reveal brand-label" width="100%"> |

**Layout**

| `centered` | `compact` |
|---|---|
| <img src="images/variant-matrix/below-fold-reveal/layout_variant-centered.png" alt="below-fold-reveal centered" width="100%"> | <img src="images/variant-matrix/below-fold-reveal/layout_variant-compact.png" alt="below-fold-reveal compact" width="100%"> |

**Copy**

| `concise` | `standard` | `detailed` |
|---|---|---|
| <img src="images/variant-matrix/below-fold-reveal/copy_variant-concise.png" alt="below-fold-reveal concise" width="100%"> | <img src="images/variant-matrix/below-fold-reveal/copy_variant-standard.png" alt="below-fold-reveal standard" width="100%"> | <img src="images/variant-matrix/below-fold-reveal/copy_variant-detailed.png" alt="below-fold-reveal detailed" width="100%"> |

**Theme**

| `blue` | `mint` | `slate` | `violet` |
|---|---|---|---|
| <img src="images/variant-matrix/below-fold-reveal/theme_variant-blue.png" alt="below-fold-reveal blue" width="100%"> | <img src="images/variant-matrix/below-fold-reveal/theme_variant-mint.png" alt="below-fold-reveal mint" width="100%"> | <img src="images/variant-matrix/below-fold-reveal/theme_variant-slate.png" alt="below-fold-reveal slate" width="100%"> | <img src="images/variant-matrix/below-fold-reveal/theme_variant-violet.png" alt="below-fold-reveal violet" width="100%"> |

</details>

## Challenge

Completion requires an answer validated by the server. The expected answer is never sent to the client.

### `custom-digit`

Enter the five digits rendered in a locally generated image.

<p align="center"><img src="images/templates/custom-digit.png" alt="custom-digit gate" width="70%"></p>

<details>
<summary>Presentation variants</summary>


**Context mode**

| `neutral` | `brand-label` |
|---|---|
| <img src="images/variant-matrix/custom-digit/context_mode-neutral.png" alt="custom-digit neutral" width="100%"> | <img src="images/variant-matrix/custom-digit/context_mode-brand-label.png" alt="custom-digit brand-label" width="100%"> |

**Layout**

| `centered` | `compact` |
|---|---|
| <img src="images/variant-matrix/custom-digit/layout_variant-centered.png" alt="custom-digit centered" width="100%"> | <img src="images/variant-matrix/custom-digit/layout_variant-compact.png" alt="custom-digit compact" width="100%"> |

**Copy**

| `concise` | `standard` | `detailed` |
|---|---|---|
| <img src="images/variant-matrix/custom-digit/copy_variant-concise.png" alt="custom-digit concise" width="100%"> | <img src="images/variant-matrix/custom-digit/copy_variant-standard.png" alt="custom-digit standard" width="100%"> | <img src="images/variant-matrix/custom-digit/copy_variant-detailed.png" alt="custom-digit detailed" width="100%"> |

**Theme**

| `blue` | `mint` | `slate` | `violet` |
|---|---|---|---|
| <img src="images/variant-matrix/custom-digit/theme_variant-blue.png" alt="custom-digit blue" width="100%"> | <img src="images/variant-matrix/custom-digit/theme_variant-mint.png" alt="custom-digit mint" width="100%"> | <img src="images/variant-matrix/custom-digit/theme_variant-slate.png" alt="custom-digit slate" width="100%"> | <img src="images/variant-matrix/custom-digit/theme_variant-violet.png" alt="custom-digit violet" width="100%"> |

</details>

### `math-challenge`

Solve a generated arithmetic problem.

<p align="center"><img src="images/templates/math-challenge.png" alt="math-challenge gate" width="70%"></p>

<details>
<summary>Presentation variants</summary>


**Context mode**

| `neutral` | `brand-label` |
|---|---|
| <img src="images/variant-matrix/math-challenge/context_mode-neutral.png" alt="math-challenge neutral" width="100%"> | <img src="images/variant-matrix/math-challenge/context_mode-brand-label.png" alt="math-challenge brand-label" width="100%"> |

**Layout**

| `centered` | `compact` |
|---|---|
| <img src="images/variant-matrix/math-challenge/layout_variant-centered.png" alt="math-challenge centered" width="100%"> | <img src="images/variant-matrix/math-challenge/layout_variant-compact.png" alt="math-challenge compact" width="100%"> |

**Copy**

| `concise` | `standard` | `detailed` |
|---|---|---|
| <img src="images/variant-matrix/math-challenge/copy_variant-concise.png" alt="math-challenge concise" width="100%"> | <img src="images/variant-matrix/math-challenge/copy_variant-standard.png" alt="math-challenge standard" width="100%"> | <img src="images/variant-matrix/math-challenge/copy_variant-detailed.png" alt="math-challenge detailed" width="100%"> |

**Theme**

| `blue` | `mint` | `slate` | `violet` |
|---|---|---|---|
| <img src="images/variant-matrix/math-challenge/theme_variant-blue.png" alt="math-challenge blue" width="100%"> | <img src="images/variant-matrix/math-challenge/theme_variant-mint.png" alt="math-challenge mint" width="100%"> | <img src="images/variant-matrix/math-challenge/theme_variant-slate.png" alt="math-challenge slate" width="100%"> | <img src="images/variant-matrix/math-challenge/theme_variant-violet.png" alt="math-challenge violet" width="100%"> |

</details>

### `image-grid`

Select every cell that matches the requested category in a 3x3 grid.

<p align="center"><img src="images/templates/image-grid.png" alt="image-grid gate" width="70%"></p>

<details>
<summary>Presentation variants</summary>


**Context mode**

| `neutral` | `brand-label` |
|---|---|
| <img src="images/variant-matrix/image-grid/context_mode-neutral.png" alt="image-grid neutral" width="100%"> | <img src="images/variant-matrix/image-grid/context_mode-brand-label.png" alt="image-grid brand-label" width="100%"> |

**Layout**

| `centered` | `compact` |
|---|---|
| <img src="images/variant-matrix/image-grid/layout_variant-centered.png" alt="image-grid centered" width="100%"> | <img src="images/variant-matrix/image-grid/layout_variant-compact.png" alt="image-grid compact" width="100%"> |

**Copy**

| `concise` | `standard` | `detailed` |
|---|---|---|
| <img src="images/variant-matrix/image-grid/copy_variant-concise.png" alt="image-grid concise" width="100%"> | <img src="images/variant-matrix/image-grid/copy_variant-standard.png" alt="image-grid standard" width="100%"> | <img src="images/variant-matrix/image-grid/copy_variant-detailed.png" alt="image-grid detailed" width="100%"> |

**Theme**

| `blue` | `mint` | `slate` | `violet` |
|---|---|---|---|
| <img src="images/variant-matrix/image-grid/theme_variant-blue.png" alt="image-grid blue" width="100%"> | <img src="images/variant-matrix/image-grid/theme_variant-mint.png" alt="image-grid mint" width="100%"> | <img src="images/variant-matrix/image-grid/theme_variant-slate.png" alt="image-grid slate" width="100%"> | <img src="images/variant-matrix/image-grid/theme_variant-violet.png" alt="image-grid violet" width="100%"> |

</details>

### `text-captcha`

Type the characters rendered in a locally generated image (case-insensitive).

<p align="center"><img src="images/templates/text-captcha.png" alt="text-captcha gate" width="70%"></p>

<details>
<summary>Presentation variants</summary>


**Context mode**

| `neutral` | `brand-label` |
|---|---|
| <img src="images/variant-matrix/text-captcha/context_mode-neutral.png" alt="text-captcha neutral" width="100%"> | <img src="images/variant-matrix/text-captcha/context_mode-brand-label.png" alt="text-captcha brand-label" width="100%"> |

**Layout**

| `centered` | `compact` |
|---|---|
| <img src="images/variant-matrix/text-captcha/layout_variant-centered.png" alt="text-captcha centered" width="100%"> | <img src="images/variant-matrix/text-captcha/layout_variant-compact.png" alt="text-captcha compact" width="100%"> |

**Copy**

| `concise` | `standard` | `detailed` |
|---|---|---|
| <img src="images/variant-matrix/text-captcha/copy_variant-concise.png" alt="text-captcha concise" width="100%"> | <img src="images/variant-matrix/text-captcha/copy_variant-standard.png" alt="text-captcha standard" width="100%"> | <img src="images/variant-matrix/text-captcha/copy_variant-detailed.png" alt="text-captcha detailed" width="100%"> |

**Theme**

| `blue` | `mint` | `slate` | `violet` |
|---|---|---|---|
| <img src="images/variant-matrix/text-captcha/theme_variant-blue.png" alt="text-captcha blue" width="100%"> | <img src="images/variant-matrix/text-captcha/theme_variant-mint.png" alt="text-captcha mint" width="100%"> | <img src="images/variant-matrix/text-captcha/theme_variant-slate.png" alt="text-captcha slate" width="100%"> | <img src="images/variant-matrix/text-captcha/theme_variant-violet.png" alt="text-captcha violet" width="100%"> |

</details>

### `area-select`

Click the region of a generated scene that contains the requested item.

<p align="center"><img src="images/templates/area-select.png" alt="area-select gate" width="70%"></p>

<details>
<summary>Presentation variants</summary>


**Context mode**

| `neutral` | `brand-label` |
|---|---|
| <img src="images/variant-matrix/area-select/context_mode-neutral.png" alt="area-select neutral" width="100%"> | <img src="images/variant-matrix/area-select/context_mode-brand-label.png" alt="area-select brand-label" width="100%"> |

**Layout**

| `centered` | `compact` |
|---|---|
| <img src="images/variant-matrix/area-select/layout_variant-centered.png" alt="area-select centered" width="100%"> | <img src="images/variant-matrix/area-select/layout_variant-compact.png" alt="area-select compact" width="100%"> |

**Copy**

| `concise` | `standard` | `detailed` |
|---|---|---|
| <img src="images/variant-matrix/area-select/copy_variant-concise.png" alt="area-select concise" width="100%"> | <img src="images/variant-matrix/area-select/copy_variant-standard.png" alt="area-select standard" width="100%"> | <img src="images/variant-matrix/area-select/copy_variant-detailed.png" alt="area-select detailed" width="100%"> |

**Theme**

| `blue` | `mint` | `slate` | `violet` |
|---|---|---|---|
| <img src="images/variant-matrix/area-select/theme_variant-blue.png" alt="area-select blue" width="100%"> | <img src="images/variant-matrix/area-select/theme_variant-mint.png" alt="area-select mint" width="100%"> | <img src="images/variant-matrix/area-select/theme_variant-slate.png" alt="area-select slate" width="100%"> | <img src="images/variant-matrix/area-select/theme_variant-violet.png" alt="area-select violet" width="100%"> |

</details>

### `rotate-upright`

Rotate a public-domain/CC0 photograph upright in 45-degree steps.

<p align="center"><img src="images/templates/rotate-upright.png" alt="rotate-upright gate" width="70%"></p>

<details>
<summary>Presentation variants</summary>


**Context mode**

| `neutral` | `brand-label` |
|---|---|
| <img src="images/variant-matrix/rotate-upright/context_mode-neutral.png" alt="rotate-upright neutral" width="100%"> | <img src="images/variant-matrix/rotate-upright/context_mode-brand-label.png" alt="rotate-upright brand-label" width="100%"> |

**Layout**

| `centered` | `compact` |
|---|---|
| <img src="images/variant-matrix/rotate-upright/layout_variant-centered.png" alt="rotate-upright centered" width="100%"> | <img src="images/variant-matrix/rotate-upright/layout_variant-compact.png" alt="rotate-upright compact" width="100%"> |

**Copy**

| `concise` | `standard` | `detailed` |
|---|---|---|
| <img src="images/variant-matrix/rotate-upright/copy_variant-concise.png" alt="rotate-upright concise" width="100%"> | <img src="images/variant-matrix/rotate-upright/copy_variant-standard.png" alt="rotate-upright standard" width="100%"> | <img src="images/variant-matrix/rotate-upright/copy_variant-detailed.png" alt="rotate-upright detailed" width="100%"> |

**Theme**

| `blue` | `mint` | `slate` | `violet` |
|---|---|---|---|
| <img src="images/variant-matrix/rotate-upright/theme_variant-blue.png" alt="rotate-upright blue" width="100%"> | <img src="images/variant-matrix/rotate-upright/theme_variant-mint.png" alt="rotate-upright mint" width="100%"> | <img src="images/variant-matrix/rotate-upright/theme_variant-slate.png" alt="rotate-upright slate" width="100%"> | <img src="images/variant-matrix/rotate-upright/theme_variant-violet.png" alt="rotate-upright violet" width="100%"> |

</details>

## Safety

Templates exist only for controlled detection research. They never collect or transmit credentials, and all assets are local.
