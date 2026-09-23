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

Действующее решение владельца от 23.09.2026: учебный путь с 3D-роботом по Learning App Interface. Источники облика — editorial/2026-09-20-svet/{svet.css,svet.js,views}, сборка inject.py в один index.html. Зелёная марка, чёрное главное действие, плоские пастельные карточки выбранного курса. Светлая и тёмная темы следуют Telegram; явная сохранённая настройка имеет приоритет. Проверять 360/390/430 px, контраст AA и физическую область нажатия от 44 px.

## Canonical UI Map

| Capability | Canonical owner | Source of truth | Allowed variants | Verification |
|---|---|---|---|---|
| Select/Listbox | Native select | `prompt-course`, `practice-course`, `prep-course` | OS popup intentionally accepted on phone and desktop; visible labels | Keyboard selection, filter and narrow viewport |
| Form | Native dialog + app handlers | `copyText`, `copy-fallback`; search fields | novalidate, inline feedback, no browser validation bubbles | Clipboard success/fallback, Escape, search clear |
| Scrollbar | Global semantic CSS | Final `:root` / `[data-n]` CSS | Document scroll; horizontal code/nav overflow only | Computed colors; viewport overflow; no page transforms |
| Toast | Existing local feedback + appNotice | `copyText`, `appNotice`, achievements | Copy status stays on its button; noninteractive notice | Live text, no click obstruction |
| CRUD | Existing progress and bookmarks | `S`, `markDone`, `restorePractice`, favourites | Local updates only; no new remote destructive action | Persistence across navigation; access fetched from server |

## Navigation and responsive behavior

Главная: приветствие, одна карточка следующего доступного урока, неделя без давления серией дней, свёрнутые материалы. Нижнее меню: Сегодня · Курсы · Я. На вкладке курсов одна пастельная карточка выбранной нейросети; другие курсы в раскрываемом нейтральном списке. Оглавление состоит из трёх последовательных частей. practice/prep/news/ach/log сохранены для старых ссылок; основной путь не требует заходить в них. Новости и канал находятся внутри «О приложении» профиля.

`show` is the only view owner. It validates the destination, hides inactive views, updates the Telegram BackButton and document title, focuses a visible heading and resets document scroll. `posRestore` restores a lesson synchronously after rendering: no delayed jump under the next click. Lesson/exercise back buttons are explicit. A lesson opened from prompts, search or an exercise returns to that origin, including after a failed load and retry. The native Telegram back delegates to those buttons. Filters and expanded prompts stay in memory during the visit; progress and practice checks use per-user storage. Missing deep links show the home with a notice. No history or credential query parameters are added by this change.

## Content ownership

- Урок: короткий разбор → полный запрос → разобранный результат → одна большая кнопка дальше. Остальные блоки сохраняются под «Подробнее».
- Настройки, проекты и источники: обязательные предусловия остаются видимыми; у четырёх уроков первый шаблон сохраняется в настройках, затем отдельный запрос проверяет результат. Индексы исходных блоков и короткие инструкции — lesson-essentials.json, без закрытых тел уроков.
- Практика по прежним ссылкам использует ту же последовательность, с роботом за ноутбуком. Авторизация выполняется заново при каждом открытии; облик получает разрешённое тело через practiceCurrent.blocks, без второго запроса.
- «Получилось?» не экзамен. Ответ «нет» показывает одну подсказку робота, «да» — отклик. Это не влияет на зачёт по дочитыванию.
- Запросы: сначала шесть задач, затем выдача по выбранной задаче или поиску. 96 названий вычисляются из метаданных, закрытые тексты приходят после проверки доступа. Контекст конкретного урока сохраняется через promptsFor.
- Регистрация и первый вход доступны из «Подробнее». Инструкции обхода блокировок и иностранных номеров не возвращаются.

`blk` остаётся владельцем разметки блоков, `copyText` — копирования. `readLesson` в svet.js собирает короткую последовательность из существующего содержимого. Учебные тесты и достижения за правильные ответы удалены. Закрытые тела не встраиваются в публичный файл.

## Flow ledger

| Operation | Pending | Success | Failure / recovery | Focus |
|---|---|---|---|---|
| Open paid lesson / exercise | Local loading text; chrome remains clickable | Render server response | 401/402 access screen; timeout/server failure retry; stale response discarded | Heading; no delayed scroll |
| Copy prompt | Button remains in place | “Скопировано” | Existing selectable-text dialog | Same button or dialog |
| Find prompt | Immediate local filter, IME-safe | Matching cards and count | Empty state and clear | Search input |
| Practice checks | Native checkbox | Per-user device storage | No false claim of server sync | Checkbox |
| Finish reading | Reading progress | Lesson marked complete at the end | Progress remains on this device | No forced navigation |
| Back | Immediate | Explicit parent view | Invalid destination retains current view | Parent heading |

## Verification

Обязательны deploy/proverka.sh и браузерные audit/cveta/vy/palec-zamer/nav/func/swipe через невидимый Chrome cdp.mjs. Матрица 360/390/430, обе темы и reduced-motion проверяет контраст, переполнение, загрузку и отсутствие повторов поз, safe area, реальные области нажатия. Отдельно проверяются все 48 уроков/практик, серверный отказ, устаревшие ответы и копирование.

Движение остаётся в xMove. Центрирование нижнего меню не использует translate: это свойство принадлежит параллаксу перехода. После завершения меню возвращается в центр. Видимость содержимого не зависит от проигрывания анимации. Живой сайт проверяется после пуша; платный API — отдельной авторизованной проверкой с указанным в отчёте тестовым доступом.
