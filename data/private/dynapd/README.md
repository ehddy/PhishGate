# DynaPD kits (G1)

Download the DynaPD kits from the authors' [official repository](https://github.com/lindsey98/DynaPD) and its linked kit archive.

`selection.csv` lists the 100 kits used in PhishGate-Bench. For each row, copy the kit identified by `source_hash` and `subfolder` to `raw_selected/<copied_directory>/`. The `brand`, `entrypoint`, and `catalog_url` columns are used at runtime. Do not edit them.

The selection was made as follows:

- Kits that substantially duplicate a PhishDecloaker kit were excluded.
- Annotations that do not name an impersonated brand were excluded.
- Entry pages that need remote render resources were excluded.
- Pages that fail an HTTP smoke test through the hardened PHP launcher were excluded.
- Kits whose own server-side anti-bot logic redirects away from the phishing page were excluded.

The kits are not tracked by Git and must not be redistributed from this repository. Serve `raw_selected/` only through `tools/runtime/start_dynapd_php.sh`. That launcher disables mail, outbound network access, command execution, uploads, and file modification.
