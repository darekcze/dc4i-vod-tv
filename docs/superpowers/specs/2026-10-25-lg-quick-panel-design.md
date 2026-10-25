# DC4i VODTV, readable LG quick panel (2026-10-25)

## Intent
Make the quick-settings drawer on LG OLED55G42LW comfortable to read from a sofa.
The owner supplied a photograph showing a narrow panel with very small dedication text,
excessive whitespace above it, wrapped metadata and duplicated DC4i Labs labels.

## Approaches
1. Keep 690px drawer and reduce margins. Rejected, small line width.
2. Full-screen About view. Rejected, user wants quick settings on the right.
3. Selected: 900px right drawer, grouped controls, two-column metadata, large dedication card.

## Requirements
- 1920x1080 webOS: 900px drawer, 18px top/bottom and 20px right.
- Body poetry 22px, app title 34px, metadata values 22px.
- Preserve family dedication verbatim and remove repeated DC4i Labs.
- Move app details above the dedication, no bottom-pushing.
- Hide Screen off on unrooted LG; it requires an unavailable helper.
- Latest Version comes from public lg.darc.dev catalog; never invent release date.
- Remote keyboard navigation includes visible links and logo, excludes hidden controls.
- Keep approved neon artwork and Kodi credentials unchanged.

## Verification commands
- node scripts/test_quick_panel.mjs
- python3 scripts/render_quick_panel_preview.py
- python3 scripts/test_panel_layout.py
- node scripts/test_handoff.mjs
- python3 test_vod_tv.py
- LG actual IPK install and installed file verification
