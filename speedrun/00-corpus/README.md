---
status: draft
---

# Speedrun 00 — Corpus

## Goal

Produce a cleaned, deduplicated English text shard to pretrain on — the raw
material every later speedrun stage depends on.

## Deliverable

A ~1-2GB cleaned English shard sourced from Common Crawl/FineWeb via
datatrove, with published deduplication and quality-filter statistics
(fraction of raw data kept, filter-by-filter drop rates).

## Anchor project

datatrove (see `tracks/02-data/LANDSCAPE.md` for the toy/production mapping).
Seed lesson: `tracks/02-data/README.md`, `01-corpus-acquisition` and
`02-cleaning-and-quality-filtering`.

## Verification criterion

This stage has no verified run yet — no cleaned shard exists. When it does,
its `runs/` entry must show: the exact datatrove pipeline command and
config, wall-clock time, input/output shard sizes, and the dedup/quality
filter statistics table (not just a final byte count).
