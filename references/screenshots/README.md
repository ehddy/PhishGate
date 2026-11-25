# Template Design References

This directory holds the provenance records for the published figures that the gate templates were modeled on. Each `local_item_id` in a template's `frontend/src/gates/<family>/templates/<template>/reference.yaml` resolves to `items/<local_item_id>/source.yaml` here.

## Why there are no images

The figures come from academic papers and industry threat-intelligence reports, and their publishers hold the copyright (`rights: third-party-copyright-research-reference`). This repository does not redistribute them. To view a figure, open `source.url` and go to the figure named in `source.locator`.

## Record format

```yaml
schema_version: 1
item_id: <UTC time>-<source id>-<figure locator>[-<suffix>]
collected_at: <UTC timestamp>
gate_type: click | interaction | challenge | ...
research_role: gate-candidate | ...
pattern: <short pattern name>
source:
  publisher: <publisher>
  title: <title>
  url: <original article or paper>
  locator: <figure number or description>
collection_method: published-report-figure | paper-pdf-figure-extraction
live_phishing_visited: false
rights: third-party-copyright-research-reference
notes: <optional>
image_included: false
```

All records were collected from published sources. No live phishing page was visited to collect them.
