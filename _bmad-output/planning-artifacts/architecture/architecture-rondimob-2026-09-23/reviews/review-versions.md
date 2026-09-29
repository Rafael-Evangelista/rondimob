# Version review — rondimob architecture spine

Checked: 2026-09-29. Spine stack header says versions were read on 2026-09-23. Provenance is `.memlog.md` in this folder. The spine was not edited.

## Verdict

Pass. Every committed stack pin was web-researched, and a same-day recheck shows those releases are still current. One series is unpinned at the micro, and one patch number still does not appear on the vendor’s own download page.

## Recheck (2026-09-29)

| Name | Spine pin | Still current | Source checked today |
| --- | --- | --- | --- |
| Django | 6.1.1 | Yes | [djangoproject.com/download](https://www.djangoproject.com/download/) still calls 6.1.1 the latest official release. [6.1.1 release notes](https://docs.djangoproject.com/en/6.1/releases/6.1.1/) still dated 2026-09-02. [Install FAQ](https://docs.djangoproject.com/en/6.1/faq/install/) still lists Python 3.12, 3.13, and 3.14 for Django 6.1, and only the latest micro of each series. |
| PostgreSQL | 18.6 | Yes | [postgresql.org news, 2026-08-13](https://www.postgresql.org/about/news/postgresql-186-1711-1615-1519-1424-and-19-beta-3-released-3365/) is still the 18.6 announcement. [versio.io, data as of 2026-09-22](https://www.versio.io/en/product-release-end-of-life-eol-postgresql-postgresql.html) still lists 18.6 as latest. 19 is not GA: [Beta 4, 2026-09-24](https://www.postgresql.org/about/news/postgresql-19-beta-4-released-3386/). |
| Celery | 5.6.3 | Yes | [Stable changelog](https://docs.celeryq.dev/en/stable/changelog.html) is titled Celery 5.6.3 and opens on 5.6.3, release-date 2026-03-26. No 5.6.4 or 5.7 on that page. [What’s new in 5.6](https://docs.celeryq.dev/en/v5.6.3/history/whatsnew-5.6.html) still lists official CPython support through 3.13. |
| Redis | 8.10.2 | Yes, on secondary sources | [endoflife.date/redis](https://endoflife.date/redis), last updated 2026-09-18, latest 8.10.2 (2026-09-17). [versio.io, data as of 2026-09-29](https://www.versio.io/en/product-release-end-of-life-eol-redis-redis.html) agrees. [redis.io version management](https://redis.io/docs/latest/operate/oss_and_stack/install/version-mgmt/) lists Redis 8.10 as GA and does not print the patch. |
| Python | 3.13, micro mais recente | Series yes; micro not pinned | [python.org 3.13.15](https://www.python.org/downloads/release/python-31315/), released 2026-08-05, is the latest 3.13 micro. No newer 3.13 micro showed up between the 2026-09-23 read and today. |

The 2026-09-23 memlog entries match this recheck. Nothing in the stack table is stale.

## Named technology and starter

The committed names are Python, Django, PostgreSQL, Celery, and Redis. They still exist, and they still fit a modular monolith plus a separate worker, one database, and one broker. `django-tenants` is named only as excluded (AD-4); it is not a pin. Row-level security is a PostgreSQL feature under the 18.6 pin, not a separate product. The spine does not lean on a starter or cookiecutter, so there are no live starter defaults to check. Host and UI toolkit stay under Deferred.

## Findings

- **medium** — Python micro is unpinned. The stack row says `3.13, micro mais recente` (ARCHITECTURE-SPINE.md, Stack). The series choice is researched: it is the overlap of Django 6.1 (3.12–3.14) and Celery 5.6’s official list (through 3.13). The memlog records that as an assumption, later adopted as a working definition on 2026-09-29. Django’s install FAQ only officially supports the latest micro of each series, so the floating wording matches Django’s rule, and two builds on different days can still land on different 3.13 patches. Current latest is 3.13.15 (2026-08-05). *Disposition:* discuss. Pin `3.13.15` if the build must be reproducible; leave the float only if “latest 3.13 micro at install time” is the intended rule.

- **low** — Redis 8.10.2 was never printed on redis.io. The memlog already says download.redis.io did not show the number, and the version-management page still only names the 8.10 series. endoflife.date and versio.io still agree on 8.10.2. endoflife.ai lags and still shows 8.10.1. *Disposition:* ignore for this gate. Re-read redis.io or the GitHub release when the host is chosen.

No critical or high findings.
