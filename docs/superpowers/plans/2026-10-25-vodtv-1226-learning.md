# #26 implementation boundary

Existing canonical issue26/design; observed native progression model, lifecycle
adapter, matched genre propagation and bounded profile ranking signals. Preserve
opened-history semantics and user accounts. Strict track policy stays unknown
without actual runtime track lists; dubbing cannot be inferred from language.
Synthetic event/storage tests and generated play/stop adapter required. Runtime
and full strict-filter acceptance remain open, not waived by offline tests.

# #27 next audit

Audit all newly added settings/cache/history readers for swallowed parse/read
errors versus legitimate first use (the upstream store returns null for both).
Verify profile isolation, corrupt/oversize data, schema/legacy preservation,
failed-write feedback, clear/export semantics, credential exclusion, active-session
cleanup, timer/listener bounds, payload limits and rollback across the stack.
No storage migration may erase accounts, playlists, profiles or viewing history.
Audit native media lifecycle and accumulated observations across crash/restart;
export only explicitly allowed non-secret metadata. Keep real browser1920x1080,
remote/device, provider/source rights, production package/deployment/rollback
verification as explicit release gates. No automatic migration/release here.
