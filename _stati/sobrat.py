#!/usr/bin/env python3
"""Сборка раздела «Статьи» открытого сайта (09.10.2026).

Исходники статей — _stati/tekst/*.html: шапка из полей в комментарии и тело
обычным HTML плюс несколько своих меток (<zapros>, <sravn>, <urok> и т. д.,
список — в README.md рядом). Сборщик оборачивает их в страницу: шапка сайта,
разметка для поиска (Article, BreadcrumbList, FAQPage), оглавление, ссылки
в канал и в приложение с меткой источника.

Пишет: stati/index.html, stati/<slug>/index.html, stati/sitemap.xml
и _stati/oblozhki.json — список для картинок-превью (oblozhki.mjs).

Папка начинается с «_», поэтому GitHub Pages её не публикует.
Запуск из корня репозитория:  python3 _stati/sobrat.py  (с --chernovik — пишет и при ошибках)
"""
import html
import json
import math
import re
import sys
from pathlib import Path

КОРЕНЬ = Path(__file__).resolve().parent.parent
ИСХОДНИКИ = КОРЕНЬ / '_stati' / 'tekst'
ВЫХОД = КОРЕНЬ / 'stati'
САЙТ = 'https://ivan552776.github.io/ai-bez-lyudey'
КАНАЛ = 'https://t.me/ai_bez_lyudey'
БОТ = 'https://t.me/ai_bez_lyudey_bot/kurs'

# Порядок рубрик — порядок кнопок на главной раздела
РУБРИКИ = [
    ('nachalo', 'С чего начать'),
    ('vybor', 'Выбрать нейросеть'),
    ('teksty', 'Тексты'),
    ('rabota', 'Работа'),
    ('ucheba', 'Учёба и дети'),
    ('bezopasnost', 'Безопасность'),
]
ИМЯ_РУБРИКИ = dict(РУБРИКИ)

# Буквы курсов — те же, что в гиде neyroseti/
БУКВЫ = {'chatgpt': 'C', 'claude': 'Cl', 'perplexity': 'Px', 'gemini': 'Ge', 'notebook': 'Nb',
         'deepseek': 'DS', 'gigachat': 'G', 'alice': 'А', 'qwen': 'Q', 'proekty': 'П'}

МЕСЯЦЫ = 'января февраля марта апреля мая июня июля августа сентября октября ноября декабря'.split()

беды = []


def дата_словами(iso):
    г, м, д = iso.split('-')
    return f'{int(д)} {МЕСЯЦЫ[int(м) - 1]} {г}'


def esc(s):
    return html.escape(s, quote=True)


def без_тегов(s):
    return html.unescape(re.sub(r'<[^>]+>', ' ', s))


def склонение(n, одна, две, пять):
    n = abs(n) % 100
    if 10 < n < 20:
        return пять
    n %= 10
    return одна if n == 1 else две if 2 <= n <= 4 else пять


def уроков(n):
    return склонение(n, 'урок', 'урока', 'уроков')


ЛАТИНИЦА = dict(zip('абвгдеёжзийклмнопрстуфхцчшщъыьэюя',
                    ['a', 'b', 'v', 'g', 'd', 'e', 'e', 'zh', 'z', 'i', 'y', 'k', 'l', 'm', 'n', 'o', 'p', 'r',
                     's', 't', 'u', 'f', 'h', 'c', 'ch', 'sh', 'sch', '', 'y', '', 'e', 'yu', 'ya']))


def якорь(текст):
    t = ''.join(ЛАТИНИЦА.get(c, c) for c in без_тегов(текст).lower())
    t = re.sub(r'[^a-z0-9]+', '-', t).strip('-')
    return t[:48].rstrip('-') or 'razdel'


# ---------- данные приложения: числа в текстах считаются отсюда ----------

def данные_приложения():
    s = (КОРЕНЬ / 'index.html').read_text(encoding='utf-8')
    i = s.index('const SECS = ') + len('const SECS = ')
    secs = json.loads(s[i:s.index('\n', i)].rstrip().rstrip(';'))
    курсы = [c for c in secs if c.get('slug') and c['slug'] != 'proekty']
    уроков = {len(c['ls']) for c in курсы}
    бесплатных = {sum(1 for l in c['ls'] if l.get('free')) for c in курсы}
    if len(уроков) != 1 or len(бесплатных) != 1:
        беды.append(f'в курсах разное число уроков: {уроков} / бесплатных: {бесплатных}')
    # цена — та же строка, что на экране оплаты в приложении
    цена = re.search(r'Полный доступ — ([\d\s]+) ⭐ в месяц или ([\d\s]+) ⭐ за год', s)
    if not цена:
        беды.append('в index.html не нашлась цена «Полный доступ — … ⭐ в месяц или … ⭐ за год»')
    if 'без автосписаний' not in s:
        беды.append('в index.html нет слов «без автосписаний» — проверь условия оплаты')
    m = re.search(r'<script type="application/json" id="dannye-hvost">(.*?)</script>', s, re.S)
    хвост = json.loads(m.group(1)) if m else {}
    if not хвост.get('S_SLOVAR') or not хвост.get('S_SAFE'):
        беды.append('в index.html нет словаря или памяток (dannye-hvost)')
    # нейросети, что открываются из России: карточки приложения (S_AI_RU) и подробности (S_AI_MORE)
    нейросети = []
    блок = re.search(r'S_AI_RU=\[(.*?)\n\];', s, re.S)
    for e in re.findall(r'\{(id:.*?checked:\'[\d-]+\')\}', блок.group(1) if блок else ''):
        поле = lambda k: (re.search(k + r":'([^']*)'", e) or [None, ''])[1]
        нейросети.append({'id': поле('id'), 't': поле('t'), 'maker': поле('maker'), 'what': поле('what'),
                          'url': поле('url'), 'checked': поле('checked'),
                          'facts': re.findall(r"'([^']*)'", re.search(r'facts:\[(.*?)\]', e).group(1)),
                          'буква': re.search(r"c:\['([^']*)'", e).group(1),
                          **хвост.get('S_AI_MORE', {}).get(поле('id'), {})})
    if len(нейросети) < 5 or any(not x.get('вход') for x in нейросети):
        беды.append(f'не разобрался список нейросетей S_AI_RU: {len(нейросети)}')
    return {
        'нейросети': нейросети,
        'задачи': хвост.get('S_AI_TASKS', []),
        'словарь': sorted(хвост.get('S_SLOVAR', []), key=lambda x: (not re.match('[а-яё]', x[0].lower()), x[0].lower())),
        'памятки': {x['id']: x for x in хвост.get('S_SAFE', [])},
        'месяц': цена.group(1).strip() if цена else '',
        'год': цена.group(2).strip() if цена else '',
        'secs': курсы,
        'курсов': len(курсы),
        'уроков': max(уроков),
        'бесплатных': max(бесплатных),
        'всего_бесплатных': sum(sum(1 for l in c['ls'] if l.get('free')) for c in курсы),
        'названия': [c['t'] for c in курсы],
    }


def урок_с_сайта(uid):
    """Название, обещание и ссылка в приложение — со страницы урока, которую собирает мастерская."""
    p = КОРЕНЬ / 'uroki' / uid / 'index.html'
    if not p.exists():
        беды.append(f'нет урока uroki/{uid}/')
        return None
    s = p.read_text(encoding='utf-8')
    h1 = re.search(r'<h1>(.*?)</h1>', s, re.S)
    lead = re.search(r'<p class="lead">(.*?)</p>', s, re.S)
    meta = re.search(r'<p class="meta">(.*?)</p>', s, re.S)
    link = re.search(r'startapp=(lesson_\d+_\d+)__', s)
    курс = re.search(r'курс «([^»]+)»', meta.group(1)) if meta else None
    минут = re.search(r'(\d+) минут', meta.group(1)) if meta else None
    номер = re.search(r'Урок (\d+) из (\d+)', meta.group(1)) if meta else None
    return {
        'id': uid,
        'h1': без_тегов(h1.group(1)).strip() if h1 else uid,
        'lead': без_тегов(lead.group(1)).strip() if lead else '',
        'курс': курс.group(1) if курс else '',
        'минут': минут.group(1) if минут else '',
        'номер': номер.group(1) if номер else '',
        'старт': link.group(1) if link else '',
    }


# ---------- исходник статьи ----------

def читать(p):
    s = p.read_text(encoding='utf-8')
    m = re.match(r'\s*<!--(.*?)-->', s, re.S)
    if not m:
        беды.append(f'{p.name}: нет шапки')
        return None
    поля = {}
    for line in m.group(1).strip().splitlines():
        if ':' in line:
            k, v = line.split(':', 1)
            поля[k.strip()] = v.strip()
    поля['тело'] = s[m.end():].strip()
    for k in ('slug', 'kod', 'rubrika', 'title', 'description', 'h1', 'lead', 'robot', 'date'):
        if not поля.get(k):
            беды.append(f'{p.name}: нет поля {k}')
    if поля.get('rubrika') not in ИМЯ_РУБРИКИ:
        беды.append(f'{p.name}: неизвестная рубрика {поля.get("rubrika")}')
    if not (КОРЕНЬ / 'assets' / 'robot' / f'{поля.get("robot")}.webp').exists():
        беды.append(f'{p.name}: нет позы робота {поля.get("robot")}')
    # метка источника в приложении обрезается до 40 знаков вместе с «сайт: »
    if len('сайт: ' + поля.get('kod', '')) > 40:
        беды.append(f'{p.name}: kod длиннее 34 знаков')
    if len(поля.get('title', '')) > 75:
        беды.append(f'{p.name}: title длиннее 75 знаков ({len(поля["title"])})')
    if not 70 <= len(поля.get('description', '')) <= 170:
        беды.append(f'{p.name}: description {len(поля.get("description", ""))} знаков, нужно 70–170')
    поля['related'] = [x.strip() for x in поля.get('related', '').split(',') if x.strip()]
    поля['updated'] = поля.get('updated') or поля.get('date')
    return поля


ИКОНКА_TG = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M21.4 4.3 2.9 11.4c-1.3.5-1.2 '
             '1.3-.2 1.6l4.7 1.5 1.8 5.6c.2.6.4.8.9.8.4 0 .6-.2.9-.5l2.3-2.2 4.7 3.5c.9.5 1.5.2 1.7-.8l3.1-14.5c.3'
             '-1.3-.5-1.9-1.4-1.5ZM9.6 14.7l-.4 4-1.5-4.8 10.6-6.7-8.7 7.5Z"/></svg>')


def запрос(текст, название='Запрос'):
    t = html.unescape(текст.strip('\n'))
    t = re.sub(r'^[ \t]+', '', t, flags=re.M)
    тело = esc(t)
    тело = re.sub(r'\[[^\]\n]{1,80}\]', lambda m: f'<span class="ph">{m.group(0)}</span>', тело)
    return (f'<figure class="zapros"><figcaption><span>{esc(название)}</span>'
            f'<button type="button" class="copy" data-copy>Копировать</button></figcaption>'
            f'<pre>{тело}</pre></figure>')


def карточка_урока(uid, kod, d):
    u = урок_с_сайта(uid)
    if not u:
        return ''
    буква = БУКВЫ.get(uid.rsplit('-', 1)[0], 'И')
    tg = f'{БОТ}?startapp={u["старт"]}__{kod}' if u['старт'] else f'{БОТ}?startapp=src_site__{kod}'
    return (f'<div class="urok"><span class="lt" aria-hidden="true">{esc(буква)}</span><div>'
            f'<small>Бесплатный урок · {esc(u["курс"])}</small>'
            f'<a class="urok-t" href="{d}uroki/{uid}/">{esc(u["h1"])}</a>'
            f'<span>{esc(u["lead"])}</span>'
            f'<span class="urok-a"><a href="{d}uroki/{uid}/">Читать на сайте</a>'
            f'<a href="{tg}">Открыть в Telegram</a></span></div></div>')


def блок_канала(kod):
    return ('<aside class="kanal"><div><b>Канал «ИИ без людей»</b>'
            '<p>Каждый день один материал: готовый запрос, короткий гайд или разбор нейросети. '
            'Ведёт нейросеть, людей в редакции нет.</p></div>'
            f'<a class="btn mint" href="{КАНАЛ}">{ИКОНКА_TG}Подписаться</a></aside>')


def блок_приложения(kod, d, данные, поза='privet', заголовок='h2'):
    n = данные
    return (f'<section class="app"><img src="{d}assets/robot/{поза}.webp" width="320" height="397" alt="" loading="lazy">'
            f'<div><{заголовок}>Учись на живых задачах</{заголовок}>'
            f'<p>{n["курсов"]} {склонение(n["курсов"], "курс", "курса", "курсов")} '
            f'по {n["уроков"]} уроков в приложении в Telegram: GigaChat, Алиса и Шедеврум, DeepSeek, Qwen, '
            f'Perplexity и другие. В каждом уроке — задача, готовый запрос и проверка ответа. '
            f'Первые {n["бесплатных"]} {склонение(n["бесплатных"], "урок", "урока", "уроков")} каждого курса бесплатны.</p>'
            f'<div class="btns"><a class="btn" href="{БОТ}?startapp=src_site__{kod}">{ИКОНКА_TG}Открыть в Telegram</a>'
            f'<a class="btn line" href="{d}uroki/">Бесплатные уроки</a></div></div></section>')


def словарь(данные):
    слова = данные['словарь']
    буквы = []
    out = []
    for i, (слово, смысл) in enumerate(слова):
        б = слово[0].upper()
        if б not in буквы:
            буквы.append(б)
        out.append(f'<div><dt id="{якорь(слово)}">{esc(слово)}</dt><dd>{esc(смысл)}</dd></div>')
    ссылки = ''.join(f'<a href="#{якорь(next(w for w, _ in слова if w[0].upper() == б))}">{esc(б)}</a>' for б in буквы)
    return f'<nav class="bukvy" aria-label="Буквы">{ссылки}</nav><dl class="slovar">{"".join(out)}</dl>'


def памятка(данные, pid):
    п = данные['памятки'].get(pid)
    if not п:
        беды.append(f'нет памятки {pid} в S_SAFE')
        return ''
    out = [f'<h2>{esc(п["t"])}</h2>']
    for b in п['b']:
        вид, текст = b[0], b[1]
        if вид == 'p':
            out.append(f'<p>{esc(текст)}</p>')
        elif вид == 'h':
            out.append(f'<h3>{esc(текст)}</h3>')
        elif вид == 'ul':
            out.append('<ul>' + ''.join(f'<li>{esc(x)}</li>' for x in текст.split('|')) + '</ul>')
        elif вид == 'tip':
            out.append(f'<div class="sovet"><p>{esc(текст)}</p></div>')
        elif вид == 'prompt':
            out.append(запрос(текст, b[2] if len(b) > 2 else 'Запрос'))
        else:
            беды.append(f'памятка {pid}: неизвестный блок {вид}')
    return ''.join(out)


РАЗБОРЫ = {'gigachat': 'kak-polzovatsya-gigachat', 'alice': 'kak-polzovatsya-alisoy', 'deepseek': 'deepseek-v-rossii',
           'perplexity': 'kak-polzovatsya-perplexity', 'shedevrum': 'narisovat-kartinku'}
УРОК_ПО = {'gigachat': 'gigachat-1', 'alice': 'alice-1', 'deepseek': 'deepseek-1', 'perplexity': 'perplexity-1',
           'shedevrum': 'alice-3', 'qwen': 'qwen-1'}


def нейросети_рф(данные, d):
    """Карточки «открывается из России» — те же данные, что в приложении и в гиде neyroseti/.
    Дату проверки страница освежает с сервера (как гид): нет ответа — остаётся дата из данных."""
    по_id = {x['id']: x for x in данные['нейросети']}
    задачи = ''.join(
        f'<tr><td><b>{esc(t)}</b><br><span class="tip">{esc(dd)}</span></td><td>'
        + ', '.join(f'<a href="#ai-{i}">{esc(по_id[i]["t"])}</a>' for i in ids if i in по_id) + '</td></tr>'
        for t, dd, ids in данные['задачи'])
    out = [f'<h2>Какую выбрать под задачу</h2><div class="tab"><table><tr><th>Задача</th><th>Нейросети</th></tr>{задачи}</table></div>',
           f'<h2>{len(по_id)} нейросетей: как войти и с чего начать</h2>']
    for x in данные['нейросети']:
        г, м, дн = x['checked'].split('-')
        ссылки = [f'<a class="btn" href="{esc(x["url"])}" rel="noopener">Открыть {esc(x["t"])}</a>']
        if x['id'] in РАЗБОРЫ:
            ссылки.append(f'<a class="btn line" href="{d}neyroseti/{РАЗБОРЫ[x["id"]]}/">Подробный разбор</a>')
        if x['id'] in УРОК_ПО:
            ссылки.append(f'<a class="ai-u" href="{d}uroki/{УРОК_ПО[x["id"]]}/">Бесплатный урок →</a>')
        out.append(
            f'<section class="ai" id="ai-{x["id"]}"><div class="ai-h"><span class="lt">{esc(x["буква"])}</span><div>'
            f'<h3>{esc(x["t"])}</h3><small>{esc(x["maker"])} · {esc(x["what"])}</small></div></div>'
            f'<p class="ru" data-sverka="{x["id"]}">Открывается из России · проверено '
            f'<time datetime="{x["checked"]}">{int(дн)} {МЕСЯЦЫ[int(м) - 1]}</time></p>'
            '<ul class="ai-f">' + ''.join(f'<li>{esc(f)}</li>' for f in x['facts']) + '</ul>'
            '<b class="ai-k">Как войти</b><ol class="ai-v">' + ''.join(f'<li>{esc(v)}</li>' for v in x['вход']) + '</ol>'
            + (запрос(x['запросы'][0], 'Попробуй · замени [скобки]') if x.get('запросы') else '')
            + '<div class="btns">' + ''.join(ссылки) + '</div></section>')
    return ''.join(out)


СВЕРКА_JS = ("fetch('https://abstract-tolerant-ember.ruweb.place/api/sverka').then(r=>r.json()).then(d=>{"
             "const м='января февраля марта апреля мая июня июля августа сентября октября ноября декабря'.split(' ');"
             "for(const e of document.querySelectorAll('[data-sverka]')){const ok=d.sites&&d.sites[e.dataset.sverka],"
             "t=e.querySelector('time');if(ok&&t&&ok>t.dateTime){t.dateTime=ok;t.textContent=+ok.slice(8)+'\\u00a0'+м[+ok.slice(5,7)-1];}}"
             "}).catch(()=>{});")


def собрать_тело(с, данные, d):
    тело = с['тело']
    kod = с['kod']
    тело = re.sub(r'<slovar\s*/?>(?:</slovar>)?', lambda m: словарь(данные), тело)
    тело = re.sub(r'<neyroseti-rf\s*/?>(?:</neyroseti-rf>)?', lambda m: нейросети_рф(данные, d), тело)
    тело = re.sub(r'<pamyatka id="([a-z-]+)"\s*/?>(?:</pamyatka>)?', lambda m: памятка(данные, m.group(1)), тело)

    # частые вопросы: и видимый блок, и разметка FAQPage
    вопросы = []

    def faq(m):
        пары = re.findall(r'<vopros>(.*?)</vopros>\s*<otvet>(.*?)</otvet>', m.group(1), re.S)
        if not пары:
            беды.append(f'{с["slug"]}: пустой <faq>')
        out = ['<section class="faq"><h2 id="chastye-voprosy">Частые вопросы</h2>']
        for q, a in пары:
            q, a = q.strip(), a.strip()
            вопросы.append((без_тегов(q).strip(), re.sub(r'\s+', ' ', без_тегов(a)).strip()))
            if not a.startswith('<p'):
                a = f'<p>{a}</p>'
            out.append(f'<details><summary>{q}</summary><div class="otv">{a}</div></details>')
        out.append('</section>')
        return ''.join(out)

    тело = re.sub(r'<faq>(.*?)</faq>', faq, тело, flags=re.S)
    тело = re.sub(r'<zapros(?:\s+nazvanie="([^"]*)")?>(.*?)</zapros>',
                  lambda m: запрос(m.group(2), m.group(1) or 'Запрос'), тело, flags=re.S)

    def сравнение(m):
        слабо = re.search(r'<slabo(?:\s+nazvanie="([^"]*)")?>(.*?)</slabo>', m.group(1), re.S)
        сильно = re.search(r'<silno(?:\s+nazvanie="([^"]*)")?>(.*?)</silno>', m.group(1), re.S)
        if not (слабо and сильно):
            беды.append(f'{с["slug"]}: <sravn> без <slabo>/<silno>')
            return ''
        def сторона(x, cls, имя):
            return (f'<div class="{cls}"><b>{esc(x.group(1) or имя)}</b>'
                    f'<p>{esc(html.unescape(x.group(2).strip()))}</p></div>')
        return ('<div class="sravn">' + сторона(слабо, 'slabo', 'Так нейросеть додумает')
                + сторона(сильно, 'silno', 'Так получишь нужное') + '</div>')

    тело = re.sub(r'<sravn>(.*?)</sravn>', сравнение, тело, flags=re.S)

    def выноска(cls):
        def f(m):
            загол = f'<b>{esc(m.group(1))}</b>' if m.group(1) else ''
            внутри = m.group(2).strip()
            if not внутри.startswith('<'):
                внутри = f'<p>{внутри}</p>'
            return f'<div class="{cls}">{загол}{внутри}</div>'
        return f
    тело = re.sub(r'<sovet(?:\s+nazvanie="([^"]*)")?>(.*?)</sovet>', выноска('sovet'), тело, flags=re.S)
    тело = re.sub(r'<vazhno(?:\s+nazvanie="([^"]*)")?>(.*?)</vazhno>', выноска('vazhno'), тело, flags=re.S)
    тело = re.sub(r'<urok id="([a-z0-9-]+)"\s*/?>(?:</urok>)?', lambda m: карточка_урока(m.group(1), kod, d), тело)
    тело = re.sub(r'<kanal\s*/?>(?:</kanal>)?', lambda m: блок_канала(kod), тело)
    тело = re.sub(r'<prilozhenie\s*/?>(?:</prilozhenie>)?', lambda m: блок_приложения(kod, d, данные), тело)
    тело = тело.replace('{D}', d)

    # подзаголовки: якоря и оглавление (вопросы в оглавление не идут — у них свой заголовок)
    оглавление = []
    занято = set()

    def h2(m):
        attrs, текст = m.group(1), m.group(2)
        if 'id=' in attrs:
            return m.group(0)
        a = якорь(текст)
        while a in занято:
            a += '-2'
        занято.add(a)
        оглавление.append((a, без_тегов(текст).strip()))
        return f'<h2{attrs} id="{a}">{текст}</h2>'

    тело = re.sub(r'<h2([^>]*)>(.*?)</h2>', h2, тело, flags=re.S)
    if re.search(r'<(zapros|sravn|slabo|silno|sovet|vazhno|urok|kanal|prilozhenie|faq|vopros|otvet|slovar|pamyatka|neyroseti-rf)\b', тело):
        беды.append(f'{с["slug"]}: осталась необработанная метка')
    return тело, оглавление, вопросы


# ---------- общие куски страницы ----------

def шрифты(d):
    out = []
    for w in (400, 500, 600, 700):
        out.append(f"@font-face{{font-family:'Golos Text';font-weight:{w};font-display:swap;"
                   f"src:url({d}assets/fonts/golos-text-{w}-cyrillic.woff2) format('woff2');"
                   "unicode-range:U+0400-045F,U+0490-0491,U+04B0-04B1,U+2116}")
        out.append(f"@font-face{{font-family:'Golos Text';font-weight:{w};font-display:swap;"
                   f"src:url({d}assets/fonts/golos-text-{w}-latin.woff2) format('woff2');"
                   "unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+2000-206F,U+2074,"
                   "U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}")
    return '\n'.join(out)


CSS = (Path(__file__).resolve().parent / 'stil.css').read_text(encoding='utf-8')
JS = (Path(__file__).resolve().parent / 'skript.js').read_text(encoding='utf-8')


def голова(d, title, description, путь, og_img, тип='article', ld=None, ещё_css=''):
    url = f'{САЙТ}/{путь}'
    ld_txt = ''
    if ld:
        ld_txt = ('<script type="application/ld+json">'
                  + json.dumps(ld, ensure_ascii=False).replace('</', '<\\/') + '</script>')
    return f'''<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{url}">
<meta name="theme-color" content="#FBFAF8">
<link rel="icon" type="image/png" sizes="120x120" href="{d}stati/favicon.png">
<link rel="apple-touch-icon" href="{d}stati/favicon.png">
<meta property="og:type" content="{тип}">
<meta property="og:site_name" content="ИИ без людей">
<meta property="og:locale" content="ru_RU">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{САЙТ}/{og_img}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="preload" href="{d}assets/fonts/golos-text-400-cyrillic.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{d}assets/fonts/golos-text-700-cyrillic.woff2" as="font" type="font/woff2" crossorigin>
<style>{шрифты(d)}
{CSS}{ещё_css}</style>
{ld_txt}
</head>'''


def шапка(d, где):
    def пункт(href, текст, ключ):
        тек = ' aria-current="page"' if ключ == где else ''
        return f'<a href="{href}"{тек}>{текст}</a>'
    return (f'<a class="skip" href="#glavnoe">К тексту</a>'
            f'<header class="site"><div class="site-in">'
            f'<a class="brand" href="{d}kursy/"><span class="mk">ии</span>ИИ без людей</a>'
            f'<nav class="nav" aria-label="Разделы">'
            + пункт(f'{d}kursy/', 'О курсах', 'kursy')
            + пункт(f'{d}stati/', 'Статьи', 'stati')
            + пункт(f'{d}uroki/', 'Бесплатные уроки', 'uroki')
            + пункт(f'{d}neyroseti/', 'Нейросети в России', 'neyroseti')
            + f'</nav><a class="tg" href="{КАНАЛ}">{ИКОНКА_TG}<span>Канал</span></a></div></header>')


def подвал(d, kod):
    return (f'<footer class="ft"><div class="wrap ft-in"><div class="ft-about">'
            f'<a class="brand" href="{d}kursy/"><span class="mk">ии</span>ИИ без людей</a>'
            '<p>Нейросети для тех, кто только начинает. Материалы собирает нейросеть. Людей в редакции нет.</p></div>'
            '<nav aria-label="Сайт"><b>Сайт</b>'
            f'<a href="{d}kursy/">Курсы по нейросетям</a><a href="{d}stati/">Статьи о нейросетях</a><a href="{d}uroki/">Бесплатные уроки</a>'
            f'<a href="{d}neyroseti/">Нейросети в России без VPN</a><a href="{d}neyroseti/gotovye-zaprosy/">Готовые запросы</a>'
            f'<a href="{d}stati/slovar-neyrosetey/">Словарь нейросетей</a></nav>'
            '<nav aria-label="Telegram"><b>Telegram</b>'
            f'<a href="{КАНАЛ}">Канал «ИИ без людей»</a><a href="{БОТ}?startapp=src_site__{kod}">Приложение с курсами</a></nav>'
            '</div></footer>')


# ---------- страница статьи ----------

def карточка(с, d, уровень='h3', с_картинкой=True):
    поза = (f'<img src="{d}assets/robot/{с["robot"]}.webp" width="320" height="400" alt="" loading="lazy">'
            if с_картинкой else '')
    return (f'<a class="card" href="{d}stati/{с["slug"]}/" data-r="{с["rubrika"]}">'
            f'<span class="chip">{esc(ИМЯ_РУБРИКИ[с["rubrika"]])}</span>'
            f'<{уровень}>{esc(с["h1"])}</{уровень}><p>{esc(с.get("kratko") or с["lead"])}</p>'
            f'<span class="min">{с["минут"]} {склонение(с["минут"], "минута", "минуты", "минут")} чтения</span>{поза}</a>')


def страница_статьи(с, все, данные):
    d = '../../'
    тело, оглавление, вопросы = собрать_тело(с, данные, d)
    слов = len(без_тегов(тело).split())
    с['минут'] = max(2, math.ceil(слов / 170))
    с['слов'] = слов
    путь = f'stati/{с["slug"]}/'
    url = f'{САЙТ}/{путь}'
    og = f'stati/og/{с["slug"]}.jpg'
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'Article', 'headline': с['h1'][:110], 'description': с['description'], 'inLanguage': 'ru',
         'datePublished': с['date'], 'dateModified': с['updated'], 'url': url, 'mainEntityOfPage': url,
         'image': f'{САЙТ}/{og}', 'wordCount': слов,
         'author': {'@type': 'Organization', 'name': 'ИИ без людей', 'url': КАНАЛ},
         'publisher': {'@type': 'Organization', 'name': 'ИИ без людей', 'url': КАНАЛ,
                       'logo': {'@type': 'ImageObject', 'url': f'{САЙТ}/stati/logo.png'}}},
        {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Статьи о нейросетях', 'item': f'{САЙТ}/stati/'},
            {'@type': 'ListItem', 'position': 2, 'name': с['h1'], 'item': url}]}]}
    if вопросы:
        ld['@graph'].append({'@type': 'FAQPage', 'mainEntity': [
            {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in вопросы]})
    if 'class="slovar"' in тело:
        ld['@graph'].append({'@type': 'DefinedTermSet', 'name': с['h1'], 'url': url, 'inLanguage': 'ru',
                             'hasDefinedTerm': [{'@type': 'DefinedTerm', 'name': w, 'description': t,
                                                 'url': f'{url}#{якорь(w)}'} for w, t in данные['словарь']]})

    toc = ''.join(f'<li><a href="#{a}">{esc(t)}</a></li>' for a, t in оглавление)
    if вопросы:
        toc += '<li><a href="#chastye-voprosy">Частые вопросы</a></li>'
    похожие = [все[x] for x in с['related'] if x in все]
    for x in с['related']:
        if x not in все:
            беды.append(f'{с["slug"]}: в related нет статьи {x}')
    if len(похожие) < 3:
        похожие += [x for x in все.values() if x['slug'] != с['slug'] and x not in похожие
                    and x['rubrika'] == с['rubrika']][:3 - len(похожие)]
    if len(похожие) < 3:
        похожие += [x for x in все.values() if x['slug'] != с['slug'] and x not in похожие][:3 - len(похожие)]

    проверено = f'<span>{esc(с["proverka"])}</span>' if с.get('proverka') else ''
    страница = (голова(d, с['title'], с['description'], путь, og, 'article', ld)
                + '<body class="pg-art"><div class="prog" aria-hidden="true"><i></i></div>' + шапка(d, 'stati')
                + '<main id="glavnoe"><div class="wrap">'
                + '<div class="hero">'
                + f'<div class="hero-top"><p class="crumbs"><a href="{d}stati/">Статьи</a><span aria-hidden="true">/</span>'
                + f'<a href="{d}stati/#r-{с["rubrika"]}">{esc(ИМЯ_РУБРИКИ[с["rubrika"]])}</a></p></div>'
                + f'<img class="hero-bot" src="{d}assets/robot/{с["robot"]}.webp" width="320" height="400" alt="" fetchpriority="high">'
                + f'<div class="hero-text"><h1>{esc(с["h1"])}</h1><p class="lead">{с["lead"]}</p>'
                + f'<p class="meta"><span>Обновлено <time datetime="{с["updated"]}">{дата_словами(с["updated"])}</time></span>'
                + f'<span>{с["минут"]} {склонение(с["минут"], "минута", "минуты", "минут")} чтения</span>{проверено}</p></div>'
                + '</div>'
                + '<div class="layout"><article class="body">'
                + (f'<details class="toc-m"><summary>Содержание</summary><ol>{toc}</ol></details>' if toc else '')
                + тело
                + блок_приложения(с['kod'], d, данные)
                + '</article>'
                + (f'<aside class="side"><div class="side-in"><nav class="toc" aria-label="Содержание"><b>Содержание</b><ol>{toc}</ol></nav>'
                   f'<div class="side-cta"><b>Канал «ИИ без людей»</b><p>Готовые запросы и короткие гайды — каждый день.</p>'
                   f'<a class="btn mint" href="{КАНАЛ}">{ИКОНКА_TG}Подписаться</a></div></div></aside>' if toc else '')
                + '</div>'
                + '<section class="more"><h2>Читать дальше</h2><div class="cards">'
                + ''.join(карточка(x, d) for x in похожие[:3]) + '</div></section>'
                + '</div></main>' + подвал(d, с['kod'])
                + f'<script>{JS}{СВЕРКА_JS if "data-sverka" in тело else ""}</script></body></html>')
    return страница


# ---------- главная раздела ----------

def главная(статьи, данные):
    d = '../'
    kod = 's-glavnaya'
    путь = 'stati/'
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'CollectionPage', 'name': 'Статьи о нейросетях', 'url': f'{САЙТ}/{путь}', 'inLanguage': 'ru',
         'description': 'Как пользоваться нейросетями: инструкции, готовые запросы и проверка ответа.',
         'publisher': {'@type': 'Organization', 'name': 'ИИ без людей', 'url': КАНАЛ,
                       'logo': {'@type': 'ImageObject', 'url': f'{САЙТ}/stati/logo.png'}},
         'mainEntity': {'@type': 'ItemList', 'itemListElement': [
             {'@type': 'ListItem', 'position': i + 1, 'url': f'{САЙТ}/stati/{с["slug"]}/', 'name': с['h1']}
             for i, с in enumerate(статьи)]}},
        {'@type': 'Organization', 'name': 'ИИ без людей', 'url': КАНАЛ, 'logo': f'{САЙТ}/stati/logo.png',
         'sameAs': [КАНАЛ]}]}
    n = данные
    главные = [с for с in статьи if с.get('nachalo')]
    главные.sort(key=lambda с: int(с['nachalo']))
    кнопки = ''.join(f'<button type="button" class="f" data-f="{k}" aria-pressed="false">{esc(v)}</button>'
                     for k, v in РУБРИКИ if any(с['rubrika'] == k for с in статьи))
    # якоря рубрик: хлебные крошки статьи ведут на #r-<рубрика>
    якоря = ''.join(f'<span id="r-{k}" class="anchor"></span>' for k, _ in РУБРИКИ)

    курсы = []
    for slug, буква in БУКВЫ.items():
        if slug == 'proekty':
            continue
        u = урок_с_сайта(f'{slug}-1')
        if u:
            курсы.append(f'<a class="kurs" href="{d}uroki/{slug}-1/"><span class="lt">{esc(буква)}</span>'
                         f'<span><b>{esc(u["курс"])}</b><small>{esc(u["h1"])}</small></span></a>')

    гид = [('', 'Нейросети, которые работают в России без VPN'),
           ('kak-polzovatsya-gigachat/', 'Как пользоваться GigaChat'),
           ('kak-polzovatsya-alisoy/', 'Как пользоваться Алисой AI'),
           ('deepseek-v-rossii/', 'DeepSeek в России'),
           ('kak-polzovatsya-perplexity/', 'Как пользоваться Perplexity'),
           ('narisovat-kartinku/', 'Как нарисовать картинку нейросетью'),
           ('kak-napisat-zapros/', 'Как написать запрос нейросети'),
           ('kak-proverit-otvet/', 'Как проверить ответ нейросети'),
           ('gotovye-zaprosy/', 'Готовые запросы для нейросети')]
    for p, _ in гид:
        if not (КОРЕНЬ / 'neyroseti' / p / 'index.html').exists():
            беды.append(f'нет страницы гида neyroseti/{p}')

    title = 'Нейросети простыми словами: статьи и инструкции | ИИ без людей'
    description = ('Как пользоваться нейросетями без сложных слов: с чего начать, какую выбрать в России, '
                   'готовые запросы для текстов, работы и учёбы и как проверить ответ.')
    стр = (голова(d, title, description, путь, 'stati/og/glavnaya.jpg', 'website', ld)
           + '<body class="pg-hub">' + шапка(d, 'stati') + '<main id="glavnoe">' + якоря
           + '<section class="hh"><div class="wrap hh-in"><div class="hh-text">'
           + '<span class="chip">Ведёт нейросеть</span>'
           + '<h1>Нейросети простыми словами</h1>'
           + '<p class="lead">Статьи для тех, кто только начинает: какую нейросеть открыть в России, '
           + 'что ей написать и как проверить ответ. С готовыми запросами — копируешь и пробуешь.</p>'
           + f'<div class="btns"><a class="btn" href="{КАНАЛ}">{ИКОНКА_TG}Канал в Telegram</a>'
           + f'<a class="btn line" href="{БОТ}?startapp=src_site__{kod}">Приложение с курсами</a></div>'
           + f'<ul class="stats"><li><b>{len(статьи)}</b>{склонение(len(статьи), "статья", "статьи", "статей")}</li>'
           + f'<li><b>{n["курсов"]}</b>{склонение(n["курсов"], "курс", "курса", "курсов")} в приложении</li>'
           + f'<li><b>{n["всего_бесплатных"]}</b>{склонение(n["всего_бесплатных"], "бесплатный урок", "бесплатных урока", "бесплатных уроков")}</li></ul>'
           + '</div>'
           + f'<img class="hh-bot" src="{d}assets/robot/privet.webp" width="320" height="397" alt="Робот — лицо канала «ИИ без людей»" fetchpriority="high">'
           + '</div></section>'
           + '<div class="wrap">'
           + '<section class="blk"><h2>С чего начать</h2><div class="cards big">'
           + ''.join(карточка(с, d) for с in главные) + '</div></section>'
           + '<section class="blk" id="vse"><div class="blk-h"><h2>Все статьи</h2>'
           + f'<div class="filters" role="group" aria-label="Рубрики"><button type="button" class="f" data-f="" aria-pressed="true">Все</button>{кнопки}</div></div>'
           + '<div class="cards" id="spisok">' + ''.join(карточка(с, d) for с in статьи) + '</div></section>'
           + f'<aside class="kanal wide"><div><b>Канал «ИИ без людей»</b><p>Каждый день один материал: готовый запрос, '
           + f'короткий гайд или разбор нейросети. Бесплатно, пока ты подписан.</p></div>'
           + f'<a class="btn mint" href="{КАНАЛ}">{ИКОНКА_TG}Подписаться</a></aside>'
           + '<section class="blk"><div class="blk-h"><h2>Бесплатные уроки</h2>'
           + f'<a class="more-l" href="{d}uroki/">Все {n["всего_бесплатных"]} уроков →</a></div>'
           + f'<p class="blk-lead">Первые {n["бесплатных"]} {уроков(n["бесплатных"])} каждого курса открыты прямо на сайте. '
           + 'Одна живая задача, готовый запрос и разбор, как проверить ответ.</p>'
           + '<div class="kursy">' + ''.join(курсы) + '</div></section>'
           + '<section class="blk"><h2>Гид: нейросети в России</h2>'
           + '<p class="blk-lead">Какие открываются без VPN, как войти и с чего начать — с датой проверки у каждой.</p>'
           + '<ul class="gid">' + ''.join(f'<li><a href="{d}neyroseti/{p}">{esc(t)}</a></li>' for p, t in гид) + '</ul></section>'
           + блок_приложения(kod, d, данные, поза='planshet')
           + '</div></main>' + подвал(d, kod)
           + f'<script>{JS}</script></body></html>')
    return стр


# ---------- главная сайта: о канале и приложении ----------

ЛЕНДИНГ_CSS = (Path(__file__).resolve().parent / 'lending.css').read_text(encoding='utf-8')
ЛЕНДИНГ_JS = (Path(__file__).resolve().parent / 'lending.js').read_text(encoding='utf-8')


def лендинг(статьи, данные):
    d = '../'
    kod = 's-kursy'
    путь = 'kursy/'
    n = данные
    tg = f'{БОТ}?startapp=src_site__{kod}'
    имена = [c['t'] for c in n['secs']]
    title = 'ИИ без людей — курсы по нейросетям с нуля в Telegram'
    description = (f'{n["курсов"]} {склонение(n["курсов"], "курс", "курса", "курсов")} по нейросетям для начинающих: '
                   f'GigaChat, Алиса, DeepSeek, Qwen, ChatGPT и другие. Живая задача, готовый запрос и проверка ответа. '
                   f'Первые {n["бесплатных"]} {уроков(n["бесплатных"])} бесплатно.')
    вопросы = [
        ('Нужно ли разбираться в технике?',
         'Нет. Уроки — для тех, кто только начинает: открытка, жалоба в управляющую компанию, резюме, '
         'домашка ребёнка. Программировать не нужно.'),
        ('Какие нейросети разбираете?',
         f'{n["курсов"]} {склонение(n["курсов"], "курс", "курса", "курсов")} по {n["уроков"]} уроков: '
         + ', '.join(имена) + '.'),
        ('Сколько стоит?',
         f'Первые {n["бесплатных"]} {уроков(n["бесплатных"])} каждого курса бесплатны — всего {n["всего_бесплатных"]}. '
         f'Полный доступ — {n["месяц"]} ⭐ в месяц или {n["год"]} ⭐ за год, звёздами Telegram, без автосписаний.'),
        ('Нужно ли платить за саму нейросеть?',
         'Для уроков хватает бесплатных версий — на них мы и проверяем каждый запрос. '
         'Наша подписка не включает платные тарифы нейросетей.'),
        ('Какие нейросети открываются из России?',
         'Список с датой проверки у каждой — в нашем гиде «Нейросети, которые работают в России без VPN».'),
        ('Почему «без людей»?',
         'Канал и приложение ведёт нейросеть: она собирает материалы, людей в редакции нет. '
         'У неё есть лицо — робот, которого ты видишь на этой странице.'),
    ]
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'WebPage', 'name': title, 'url': f'{САЙТ}/{путь}', 'inLanguage': 'ru', 'description': description},
        {'@type': 'Organization', 'name': 'ИИ без людей', 'url': КАНАЛ, 'logo': f'{САЙТ}/stati/logo.png',
         'sameAs': [КАНАЛ]},
        {'@type': 'FAQPage', 'mainEntity': [
            {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in вопросы]}]}

    курсы = []
    for c in n['secs']:
        slug = c['slug']
        уроки = [урок_с_сайта(f'{slug}-{k}') for k in range(1, n['бесплатных'] + 1)]
        уроки = [u for u in уроки if u]
        if not уроки:
            continue
        пункты = ''.join(f'<li>{esc(u["h1"])}</li>' for u in уроки)
        курсы.append(f'<a class="kurs-l" href="{d}uroki/{slug}-1/"><span class="kh"><span class="lt">{esc(БУКВЫ.get(slug, "И"))}</span>'
                     f'<span><b>{esc(c["t"])}</b><small>{len(c["ls"])} {склонение(len(c["ls"]), "урок", "урока", "уроков")} · {len(уроки)} бесплатно</small></span></span>'
                     f'<ol>{пункты}</ol><span class="go">Читать первый урок →</span></a>')

    позы = [('privet', 397, ''), ('ukazyvaet', 365, 'data-'), ('raduetsya', 378, 'data-'), ('dumaet', 505, 'data-')]
    робот = ('<div class="bot" aria-hidden="true"><span class="bot-ten"></span><div class="bot-t">'
             + ''.join(f'<img data-p="{p}" {pre}src="{d}assets/robot/sayt/{p}.webp" width="320" height="{h}" alt=""'
                       + (' class="on" fetchpriority="high"' if not pre else '') + '>'
                       for p, h, pre in позы)
             + '</div><span class="bot-replika"></span></div>')

    главные = sorted([с for с in статьи if с.get('nachalo')], key=lambda с: int(с['nachalo']))
    ещё = [с for с in статьи if с not in главные][:3]

    стр = (голова(d, title, description, путь, 'stati/og/kursy.jpg', 'website', ld, ЛЕНДИНГ_CSS)
           + '<body class="pg-land">' + шапка(d, 'kursy') + '<main id="glavnoe">'
           + '<section class="scena">' + робот
           + '<div class="scena-in"><h1><span class="giant"><span>ИИ без</span> <span>людей</span></span>'
           + '<span class="sub">Курсы по нейросетям с нуля — прямо в Telegram</span></h1>'
           + '<p class="pod">Живая задача, готовый запрос и проверка ответа. Ведёт нейросеть — людей в редакции нет.</p>'
           + f'<div class="btns"><a class="btn" href="{tg}">{ИКОНКА_TG}Начать бесплатно</a>'
           + f'<a class="btn line" href="{d}uroki/">Бесплатные уроки</a></div></div></section>'
           + '<div class="wrap">'
           + '<section class="l-blk"><h2>Нейросеть объясняет, как пользоваться нейросетями</h2>'
           + '<p class="l-lead">Не лекции про будущее, а дела, которые есть у тебя на этой неделе. '
           + 'Каждый урок — одна задача от начала до готового результата.</p><div class="tri">'
           + '<div><span class="num">1</span><h3>Живая задача</h3><p>Открытка, жалоба в управляющую компанию, '
           + 'резюме под вакансию, список литературы к реферату — то, что пригодится сегодня.</p></div>'
           + '<div><span class="num">2</span><h3>Готовый запрос</h3><p>Копируешь, меняешь слова в [скобках] на свои '
           + 'и отправляешь. Рядом — что пришло у нас и почему запрос составлен именно так.</p></div>'
           + '<div><span class="num">3</span><h3>Проверка ответа</h3><p>Нейросеть уверенно додумывает: книги, законы, '
           + 'цифры. В каждом уроке — где она ошибается и как поймать это за пару минут.</p></div>'
           + '</div></section>'
           + '<section class="l-blk"><h2>Как это выглядит в уроке</h2>'
           + '<p class="l-lead">Пример из бесплатного урока по Perplexity: список литературы для реферата по ГОСТу.</p>'
           + '<div class="primer"><div class="bylo"><b>Короткая просьба</b>'
           + '<p>«Список литературы для реферата по истории, 8 класс» — и пришли пять «книг» без единой ссылки.</p>'
           + '<p>Мы поискали каждую в каталоге Российской государственной библиотеки. Четырёх книг из пяти там нет.</p></div>'
           + '<div class="stalo"><b>Запрос из урока</b>'
           + '<p>У каждой строки появилась ссылка: каталог РГБ, Президентская библиотека, КиберЛенинка. '
           + 'Мы открыли все — книги и статьи настоящие.</p>'
           + '<p>Но одна книга стояла двумя строками — это ловит проверка за пять минут: та же книга, тот же автор, '
           + 'год и страницы как в каталоге.</p></div>'
           + f'<div class="itog"><p><b>Так устроен каждый урок:</b> не «нейросеть всё знает», а запрос, ответ как есть '
           + f'и проверка. Урок открыт на сайте — посмотри целиком.</p><a class="btn mint" href="{d}uroki/perplexity-2/">Открыть урок</a></div>'
           + '</div></section>'
           + f'<section class="l-blk" id="kursy"><h2>{n["курсов"]} {склонение(n["курсов"], "курс", "курса", "курсов")} '
           + f'по {n["уроков"]} уроков</h2>'
           + f'<p class="l-lead">Первые {n["бесплатных"]} {уроков(n["бесплатных"])} каждого курса открыты на сайте и в приложении. '
           + 'Остальные — в приложении, вместе с отметками, серией дней и практикой.</p>'
           + '<div class="kursy-l">' + ''.join(курсы) + '</div></section>'
           + '<section class="l-blk" id="cena"><h2>Сколько стоит</h2>'
           + '<p class="l-lead">Оплата звёздами Telegram прямо в приложении. Без автосписаний: продлить или нет — решаешь сам.</p>'
           + '<div class="ceny"><div class="cena"><small>Бесплатно</small>'
           + f'<div class="summa">{n["всего_бесплатных"]} {склонение(n["всего_бесплатных"], "урок", "урока", "уроков")}</div>'
           + f'<ul><li>Первые {n["бесплатных"]} {уроков(n["бесплатных"])} каждого курса</li><li>Читать можно на сайте и в Telegram</li>'
           + '<li>Без регистрации и без карты</li></ul>'
           + f'<a class="btn line" href="{d}uroki/">Бесплатные уроки</a></div>'
           + '<div class="cena glav"><small>Полный доступ</small>'
           + f'<div class="summa">{n["месяц"]} ⭐ в месяц</div><p>или {n["год"]} ⭐ за год</p>'
           + f'<ul><li>Все {n["курсов"] * n["уроков"]} {склонение(n["курсов"] * n["уроков"], "урок", "урока", "уроков")} во всех курсах</li>'
           + '<li>Уроки сохраняются на телефоне и открываются без сети</li><li>Звёздами Telegram, без автосписаний</li></ul>'
           + f'<a class="btn" href="{tg}">{ИКОНКА_TG}Открыть в Telegram</a></div></div></section>'
           + '<section class="l-blk"><div class="blk-h"><h2 class="l-h2">Статьи о нейросетях</h2>'
           + f'<a class="more-l" href="{d}stati/">Все статьи →</a></div>'
           + '<div class="cards">' + ''.join(карточка(с, d) for с in главные + ещё) + '</div></section>'
           + блок_канала(kod).replace('class="kanal"', 'class="kanal wide"')
           + '<section class="l-blk l-faq faq"><h2>Частые вопросы</h2>'
           + ''.join(f'<details><summary>{esc(q)}</summary><div class="otv"><p>{esc(a)}'
                     + (f' <a href="{d}neyroseti/">Открыть гид</a>.' if 'гиде' in a else '') + '</p></div></details>'
                     for q, a in вопросы)
           + '</section>'
           + блок_приложения(kod, d, данные, поза='raduetsya')
           + '</div></main>' + подвал(d, kod)
           + f'<script>{JS}{ЛЕНДИНГ_JS}</script></body></html>')
    return стр


# ---------- сборка ----------

def добавить_в_карту(адреса):
    """Общую sitemap.xml пишет сборщик уроков в мастерской. Наши адреса дописываем в конец
    (и убираем прежние свои), а полный список держим ещё и в sitemap-sayt.xml — его сборщик уроков не трогает."""
    p = КОРЕНЬ / 'sitemap.xml'
    s = p.read_text(encoding='utf-8')
    s = re.sub(r'  <url><loc>' + re.escape(САЙТ) + r'/(?:stati|kursy)/[^<]*</loc>.*?</url>\n', '', s)
    s = s.replace('</urlset>', ''.join(адреса) + '</urlset>')
    p.write_text(s, encoding='utf-8')


def главная_функция():
    данные = данные_приложения()
    n = len(данные['словарь'])
    слов = f'{n} {склонение(n, "слово", "слова", "слов")}'
    статьи = []
    for p in sorted(ИСХОДНИКИ.glob('*.html')):
        с = читать(p)
        if с:
            for k in ('title', 'description', 'h1', 'lead', 'kratko', 'og'):
                if с.get(k):
                    с[k] = с[k].replace('{slov}', слов)
            if с['slug'] != p.stem:
                беды.append(f'{p.name}: slug «{с["slug"]}» не совпадает с именем файла')
            статьи.append(с)
    # порядок на главной: по полю poryadok, потом по имени
    статьи.sort(key=lambda с: (int(с.get('poryadok', 99)), с['slug']))
    все = {с['slug']: с for с in статьи}
    коды = [с['kod'] for с in статьи]
    if len(set(коды)) != len(коды):
        беды.append('повторяются kod у статей')

    # сначала тела: минуты чтения нужны карточкам на соседних страницах
    for с in статьи:
        тело, _, _ = собрать_тело(с, данные, '../../')
        с['минут'] = max(2, math.ceil(len(без_тегов(тело).split()) / 170))

    страницы = {}
    for с in статьи:
        страницы[f'stati/{с["slug"]}/index.html'] = страница_статьи(с, все, данные)
    страницы['stati/index.html'] = главная(статьи, данные)
    страницы['kursy/index.html'] = лендинг(статьи, данные)

    # проверка ссылок внутри сайта: каждая относительная ссылка ведёт на файл
    свои_файлы = ('stati/og/', 'stati/favicon.png', 'stati/logo.png')
    for имя, текст in страницы.items():
        база = (КОРЕНЬ / имя).parent
        for href in re.findall(r'(?:href|src)="([^"#:?]+)(?:#[^"]*)?"', текст):
            цель = (база / href).resolve()
            if href.endswith('/') or цель.is_dir():
                цель = цель / 'index.html'
            rel = str(цель.relative_to(КОРЕНЬ)) if str(цель).startswith(str(КОРЕНЬ)) else str(цель)
            if not цель.exists() and rel not in страницы and not rel.startswith(свои_файлы):
                беды.append(f'{имя}: битая ссылка {href}')

    if беды:
        print('Не собрано:\n  ' + '\n  '.join(беды))
        # черновик: страницы всё равно пишутся, чтобы посмотреть их до того, как готово всё
        if '--chernovik' not in sys.argv:
            sys.exit(1)

    for имя, текст in страницы.items():
        f = КОРЕНЬ / имя
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(текст, encoding='utf-8')

    свежая = max(с['updated'] for с in статьи)
    адреса = [f'  <url><loc>{САЙТ}/kursy/</loc><lastmod>{свежая}</lastmod></url>\n',
              f'  <url><loc>{САЙТ}/stati/</loc><lastmod>{свежая}</lastmod></url>\n']
    адреса += [f'  <url><loc>{САЙТ}/stati/{с["slug"]}/</loc><lastmod>{с["updated"]}</lastmod></url>\n' for с in статьи]
    (КОРЕНЬ / 'sitemap-sayt.xml').write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + ''.join(адреса) + '</urlset>\n', encoding='utf-8')
    добавить_в_карту(адреса)

    обложки = [{'slug': 'kursy', 'title': 'ИИ без людей', 'rubrika': 'Курсы по нейросетям с нуля', 'robot': 'privet',
                'big': True},
               {'slug': 'glavnaya', 'title': 'Нейросети простыми словами', 'rubrika': 'Статьи и инструкции',
                'robot': 'chitaet'}]
    обложки += [{'slug': с['slug'], 'title': с.get('og') or с['h1'], 'rubrika': ИМЯ_РУБРИКИ[с['rubrika']],
                 'robot': с['robot']} for с in статьи]
    (КОРЕНЬ / '_stati' / 'oblozhki.json').write_text(json.dumps(обложки, ensure_ascii=False, indent=1) + '\n',
                                                     encoding='utf-8')
    for с in статьи:
        print(f'  {с["slug"]:<34} {с.get("слов", 0):>5} слов · {с["минут"]} мин')
    print(f'Собрано: главная kursy/, {len(статьи)} статей + главная раздела stati/, карта — sitemap-sayt.xml')


if __name__ == '__main__':
    главная_функция()
