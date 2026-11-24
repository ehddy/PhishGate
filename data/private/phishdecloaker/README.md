# PhishDecloaker kits (G1)

Download the kits published with *PhishDecloaker: Detecting CAPTCHA-cloaked Phishing Websites via Hybrid Vision-based Interactive Models* (USENIX Security 2024):

- Dataset: <https://doi.org/10.5281/zenodo.11228974>
- Archive: `phishing-kits-dataset.zip` (published MD5 `8395ddea3bf84469fedf785941660e3a`)

Extract the archive so that `extracted/src/kit1` through `extracted/src/kit100` exist in this directory. The brand label of each kit is already provided in `data/kit_brand_annotation.csv`.

The kits are not tracked by Git and must not be redistributed from this repository. Treat every kit as untrusted. Docker and Conda serve this directory only through the hardened PHP launcher in `tools/runtime/`, on an internal network or loopback.
