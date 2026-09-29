# Examples

This directory contains the onboarding/demo artefacts for the repository:

- `sample_ratings.json` — a small real assessment input using valid risk IDs from `data/risks.yaml`
- `demo_transcript.txt` — a real terminal transcript captured from this repository's CLI

## Reproduce the demo

From the repository root, run:

```bash
(.venv/bin/capra-pia list-risks | head -n 8) && echo && .venv/bin/capra-pia assess examples/sample_ratings.json
```

## Refresh the transcript

The checked-in transcript was produced with real command output:

```bash
{
  printf '# Real terminal transcript generated from this repository using the existing .venv\n\n'
  printf '$ .venv/bin/capra-pia list-risks | head -n 8\n'
  .venv/bin/capra-pia list-risks | head -n 8
  printf '\n$ .venv/bin/capra-pia assess examples/sample_ratings.json\n'
  .venv/bin/capra-pia assess examples/sample_ratings.json
} > examples/demo_transcript.txt
```

Animated recording tooling was not added here; if you want a GIF/SVG terminal demo later, regenerate locally with `asciinema` + `svg-term` or `vhs`.
