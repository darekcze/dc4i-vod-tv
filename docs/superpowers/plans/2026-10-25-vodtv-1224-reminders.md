# 1.2.24 foreground reminders

Canonical issue #24 and approved design. Extend dc4iEpgRemindersV1, remove its
old duplicate timer, preserve legacy entries/profile TV.store and use TDD.
No native toast/background/wake API, permissions, merge, deployment or LG calls.

- [x] Profile-scoped synchronous storage port, compatible legacy array, bounded
  admission, deduplication/cancel/expiry and confirmed-write-before-delivery.
- [x] Local-TV-time quiet hours (overnight/full-day), UTC event identity, DST tests.
- [x] Foreground/visible/focused gate; reload/profile switching with no stale list.
- [x] Remote settings/list controls, PL/EN labels and persisted preferences.
- [x] Generated integration/full offline regression and bilingual gap notes.

Validation: 36 Node suites, 14 Python cases, generated structure/35 JavaScript
syntax checks and webOS CLI check passed, plus Europe/Warsaw reminder suite.
Actual browser/platform acceptance remains blocked; these are offline checks.

Delivery is best-effort foreground, at most once after confirmed removal. A crash
between removal and toast may miss delivery; closed/quiet expired events are not
replayed later. No real platform background capability is claimed.
#25 assessment must require official/licensed sources and explicit provenance;
no scraped datasets, inferred provider Top10 or invented rankings.
