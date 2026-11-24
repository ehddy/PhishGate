# Scripts

Run all commands from the repository root.

## Benchmark preparation

```bash
python3 scripts/prepare_experiment.py
```

This builds the seed-fixed benchmark targets and plans under `targets/` from the frozen cohort in `config/cohort.csv`, and verifies them. It requires `.env` with `PHISHGATE_SEED` and all G1, G2, and G3 data in place. The main evaluation uses `targets/EVAL/manifest.csv`.

Do not overwrite a manifest after it has been used in an experiment.

## Local hostnames

Benchmark samples are served under local hostnames. G2 and G3 keep their original hostnames, and G1 uses seed-derived hostnames.

```bash
python3 scripts/configure_hosts.py              # preview the managed /etc/hosts block
sudo python3 scripts/configure_hosts.py --apply
sudo python3 scripts/configure_hosts.py --remove
```

## Dataset bundles

`dataset_bundle.py` packs, verifies, and extracts the benchmark data as reproducible archives with SHA-256 checksums. The default bundle directory is `tmp/dataset-bundles/`.

```bash
python3 scripts/dataset_bundle.py verify --groups manual-phishing manual-benign
python3 scripts/dataset_bundle.py unpack --groups manual-phishing manual-benign
```

`unpack` writes only to the expected paths and never silently replaces different files. The groups are `phishdecloaker`, `dynapd`, `manual-phishing` (G2), and `manual-benign` (G3).

## DynaPD selection

`dataset/import_dynapd_selection.py` documents how the 100 DynaPD kits in `data/private/dynapd/selection.csv` were selected. Running it requires the DynaPD authors' annotation files. To reproduce the benchmark, use the finished `selection.csv` instead.
