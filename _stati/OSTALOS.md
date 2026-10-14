# Что осталось доделать (передача, 14.10.2026)

Ветка `claude/exciting-ptolemy-g81tlz`. В `main` не влито — живой сайт пока прежний.

Сделано: `kursy/` (главная-пруд с карпом кои, WebGL), `stati/` (12 статей),
`sitemap-sayt.xml`, превью `stati/og/`. Сборка — `python3 _stati/sobrat.py`,
правила — `_stati/README.md`, раздел «Главная сайта и статьи» в `AGENTS.md`.

Открыто:
1. **Лицензия картинки кои не подтверждена** (`assets/ryba/ISTOCHNIK.md`). Найти первоисточник
   или заменить на свободную картинку; новую — через `_stati/ryba_podgotovka.py`
   (поправить точки `ХРЕБЕТ` под новую рыбку и проверить сетку флагом `--proverka`).
2. Корень `Ivan552776.github.io`: строка `Sitemap: https://ivan552776.github.io/ai-bez-lyudey/sitemap-sayt.xml`
   в `robots.txt` и ссылка с главной на `/ai-bez-lyudey/kursy/`.
3. Добавить `sitemap-sayt.xml` в Яндекс Вебмастер и Google Search Console.
4. Сборщик мастерской (`editorial/2026-10-01-stranicy/sobrat.py`) перезаписывает `sitemap.xml` —
   научить его не стирать строки `kursy/` и `stati/` или ссылаться на `sitemap-sayt.xml`.
5. Проверить пруд на настоящих телефонах (iPhone, Android, вебвью Telegram): плавность и нагрев.
6. Превью `stati/og/kursy.jpg` пока с роботом — можно снять кадр пруда.
7. Перед вливанием в `main` — `proverka.sh` и ночная проверка `qa/nochnaya.mjs`.
