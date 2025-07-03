# Changelog

## [Unreleased]
- Add package structure under `utubenews/`
- Move client-side script to `static/`
- Update imports and README
- Add docstrings and typing
- Provide example tests
- Allow setting `max_pages` for Naver sources via `rss_sources.yaml`
- Improve pipeline and collector docstrings
- Add `examples/run_pipeline.py` usage sample
- Add tests for summarization utilities
- Improve `extract_main_text` to parse `<article>` containers and lower
  default `min_len` to 10
- Normalize generated scripts before saving
- `run()` always extracts article bodies and summaries
- Output JSON now includes all collected fields
- Screenshots are captured by default; use `--no-screenshot` to opt out

