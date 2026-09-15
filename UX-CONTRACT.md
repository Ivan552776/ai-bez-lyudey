# UX Contract

## Product context

Практическая библиотека для русскоязычных новичков: изучить одну нейросеть, взять запрос и выполнить задачу. RU, даты в Europe/Moscow. Цель доступности — WCAG 2.2 AA; основные цели касания от 44 px. Библиотека является приложением с состоянием, а не лендингом.

## Business-context sources

| Domain / scope | Authoritative source | Source type | Reviewed date |
|---|---|---|---|
| Permission model | PRODUCT.md; API `/api/lesson` | Product requirements and server access contract | 2026-09-15 |
| Data lifecycle | PRODUCT.md; `S`, `post`, `restorePractice` in index.html | Existing product behavior | 2026-09-15 |
| Billing / payment | PRODUCT.md; existing subscription screen | Maintained product decision; unchanged by section migration | 2026-09-15 |
| Deletion / legal copy | Existing profile/documents screens | Out of this migration; no new deletion or agreements | 2026-09-15 |
| Navigation / content | User brief 2026-09-15; curriculum section migration PLAN.md in private project | Explicit user instruction | 2026-09-15 |

## Visual contract

DESIGN.md records the palette, surfaces and composition. Runtime owner is the final CSS cascade in index.html, generated from curriculum/2026-09-15-premium/premium.css and visual_patch.py in the private project. No build-time token export. Only the light theme is supported by explicit user decision on 2026-09-15. Ignore old dark-mode preferences and Telegram/system theme; remove the switch. Check computed colors and 360/390/430 px after changing the cascade. The earlier library CSS remains for archived views; the new section CSS owns current surfaces.

## Canonical UI Map

| Capability | Canonical owner | Source of truth | Allowed variants | Verification |
|---|---|---|---|---|
| Select/Listbox | Native select | `prompt-course`, `practice-course`, `prep-course` | OS popup intentionally accepted on phone and desktop; visible labels | Keyboard selection, filter and narrow viewport |
| Form | Native dialog + app handlers | `copyText`, `copy-fallback`; search fields | novalidate, inline feedback, no browser validation bubbles | Clipboard success/fallback, Escape, search clear |
| Scrollbar | Global semantic CSS | Final `:root` / `[data-n]` CSS | Document scroll; horizontal code/nav overflow only | Computed colors; viewport overflow; no page transforms |
| Toast | Existing local feedback + appNotice | `copyText`, `appNotice`, achievements | Copy status stays on its button; noninteractive notice | Live text, no click obstruction |
| CRUD | Existing progress and bookmarks | `S`, `markDone`, `restorePractice`, favourites | Local updates only; no new remote destructive action | Persistence across navigation; access fetched from server |

## Navigation and responsive behavior

Home has five destinations: lessons, prompts, practice, VPN, foreign number. The library displays six illustrated books. Registration is separate preparation reached from home, the library or a course. The header owns home/search/profile; secondary routes use five horizontal section buttons. There is no bottom dock, slideshow, laptop scene or page-scale transition.

`show` is the only view owner. It validates the destination, hides inactive views, updates the Telegram BackButton and document title, focuses a visible heading and resets document scroll. `posRestore` restores a lesson synchronously after rendering: no delayed jump under the next click. Lesson/exercise back buttons are explicit. A lesson opened from prompts, search or an exercise returns to that origin, including after a failed load and retry. The native Telegram back delegates to those buttons. Filters and expanded prompts stay in memory during the visit; progress and practice checks use per-user storage. Missing deep links show the home with a notice. No history or credential query parameters are added by this change.

## Content ownership

- Lessons: explanation, steps, colored diagram, collapsed sources, entry to practice.
- Practice: sample data, complete prompt, worked result, follow-up prompt, personal exercise and three questions. Questions refer to the sample and belong here.
- Prompts: independent searchable catalogue; two prompts per lesson. Show 12, with explicit load-more.
- Preparation: service-specific account steps and email help. VPN and phone purchases remain separate.
- VPN: Ded Proxy on dedfast.com, device-specific installation. INCY is a separate client for an existing compatible subscription, not a compulsory activation step.
- Numbers: SMSFAST with personal-use endorsement from the user; explain requirements without guaranteeing every virtual number is accepted.

`lessonParts` is the canonical projection of existing lesson blocks. `blk` remains the canonical renderer, `copyText` the clipboard owner, `testInit` the quiz owner. No paid body is embedded in the public site. `fetchLesson` always performs the existing server check before paid content is shown.

## Flow ledger

| Operation | Pending | Success | Failure / recovery | Focus |
|---|---|---|---|---|
| Open paid lesson / exercise | Local loading text; chrome remains clickable | Render server response | 401/402 access screen; timeout/server failure retry; stale response discarded | Heading; no delayed scroll |
| Copy prompt | Button remains in place | “Скопировано” | Existing selectable-text dialog | Same button or dialog |
| Find prompt | Immediate local filter, IME-safe | Matching cards and count | Empty state and clear | Search input |
| Practice checks | Native checkbox | Per-user device storage | No false claim of server sync | Checkbox |
| Finish quiz | One question at a time | Result attributed to the exercise lesson key | Explanation and retry | Next question/result |
| Back | Immediate | Explicit parent view | Invalid destination retains current view | Parent heading |

## Verification

Run the premium strict static audit and project `deploy/proverka.sh`. The static auditor cannot infer delegated `data-*` click handlers: review such findings against the canonical event dispatcher and browser flows, not by adding duplicate inline handlers. Browser checks cover every lesson/exercise pair on a local fixture, production lock behavior, loading/error/stale responses, prompt search/copy, registration, four VPN devices, light-only 320/360/390/430/1180 and legacy dark-preference migration. Real payment and real regional/network changes are not test actions.
