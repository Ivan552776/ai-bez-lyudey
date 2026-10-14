#!/usr/bin/env python3
"""Рыбка первого экрана: из присланной картинки — вырезанная рыбка и её «скелет» (09.10.2026).

Исходник — _stati/ryba/iskhodnik.webp: карп кои сверху, «шахматка» прозрачности
нарисована прямо на картинке (так отдают сайты-сборники PNG). Скрипт:
  1. вырезает фон: клетки шахматки серые без оттенка, а белое у рыбки кремовое —
     заливаем от краёв картинки только по бесцветным светлым точкам;
  2. по хребту (точки ниже, размечены руками от носа к кончику хвоста) строит
     сетку: в каждой точке хребта — насколько рыбка с плавниками простирается
     влево и вправо. Идём от хребта наружу до первой прозрачной щели: так внутрь
     изгиба не попадает лопасть хвоста, что лежит рядом с телом;
  3. пишет assets/ryba/koi.webp (обрезанная, с прозрачностью) и assets/ryba/koi.json —
     сетку для lending.js, который гнёт рыбку волной.
Запуск: python3 _stati/ryba_podgotovka.py [--proverka путь.png] — картинка с сеткой для глаза.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

КОРЕНЬ = Path(__file__).resolve().parent.parent
ИСХОДНИК = КОРЕНЬ / '_stati' / 'ryba' / 'iskhodnik.webp'
КУДА = КОРЕНЬ / 'assets' / 'ryba'

# хребет от кончика носа к кончику хвоста, точки исходной картинки 920×990
ХРЕБЕТ = [(880, 772), (800, 745), (700, 702), (600, 662), (500, 618), (400, 572), (310, 522),
          (232, 466), (168, 402), (128, 332), (116, 272), (124, 226), (165, 190), (225, 162),
          (295, 138), (365, 112), (420, 92)]
ТОЧЕК = 44            # столько поперечных рядов сетки
ЩЕЛЬ = 7              # столько прозрачных точек подряд — уже не рыбка, а просвет
ДАЛЬШЕ = 300          # дальше от хребта не ищем
ЗАПАС = 5             # к краю сетки — немного прозрачного запаса, чтобы не резать сглаживание


def вырезать(im):
    a = np.asarray(im.convert('RGB'), dtype=np.int16)
    разброс = a.max(axis=2) - a.min(axis=2)
    клетка = (разброс <= 10) & (a.min(axis=2) >= 212)
    # .copy(): картинка из numpy только для чтения, заливка в неё молча не пишет
    маска = Image.fromarray((клетка * 255).astype(np.uint8)).copy()
    h, w = клетка.shape
    for x in range(w):
        for y in (0, h - 1):
            if маска.getpixel((x, y)) == 255:
                ImageDraw.floodfill(маска, (x, y), 128)
    for y in range(h):
        for x in (0, w - 1):
            if маска.getpixel((x, y)) == 255:
                ImageDraw.floodfill(маска, (x, y), 128)
    фон = np.asarray(маска) == 128
    альфа = Image.fromarray(((~фон) * 255).astype(np.uint8))
    # край: на 1 точку внутрь (там светлая кайма от сжатия) и мягкое сглаживание
    альфа = альфа.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(.8))
    out = im.convert('RGBA')
    out.putalpha(альфа)
    return out


def сплайн(точки, n):
    """Катмулл-Ром через точки, потом равные шаги по длине."""
    p = [точки[0]] + list(точки) + [точки[-1]]
    густо = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for k in range(20):
            t = k / 20
            густо.append(tuple(.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t * t
                                     + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t ** 3) for j in (0, 1)))
    густо.append(точки[-1])
    длины = [0.0]
    for a, b in zip(густо, густо[1:]):
        длины.append(длины[-1] + math.dist(a, b))
    итог = []
    for i in range(n):
        s = длины[-1] * i / (n - 1)
        j = max(0, min(len(длины) - 2, next(k for k in range(len(длины) - 1) if длины[k + 1] >= s)))
        u = (s - длины[j]) / max(1e-6, длины[j + 1] - длины[j])
        итог.append((густо[j][0] + (густо[j + 1][0] - густо[j][0]) * u, густо[j][1] + (густо[j + 1][1] - густо[j][1]) * u))
    return итог, длины[-1]


def ширины(альфа, точки):
    h, w = альфа.shape
    res = []
    for i, (x, y) in enumerate(точки):
        a, b = точки[max(0, i - 1)], точки[min(len(точки) - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        n = (-dy / d, dx / d)          # «левая» нормаль
        стороны = []
        for знак in (1, -1):
            даль, пусто = 0, 0
            for r in range(1, ДАЛЬШЕ):
                px, py = int(round(x + знак * n[0] * r)), int(round(y + знак * n[1] * r))
                if not (0 <= px < w and 0 <= py < h) or альфа[py, px] < 20:
                    пусто += 1
                    if пусто > ЩЕЛЬ:
                        break
                else:
                    пусто, даль = 0, r
            стороны.append(даль)
        res.append(стороны)
    # плавники стоят под углом к поперечнику: соседние ряды подтягиваем друг к другу,
    # чтобы край сетки шёл по самому дальнему соседу и не резал плавник
    сглаж = []
    for i in range(len(res)):
        окно = res[max(0, i - 1):i + 2]
        сглаж.append([max(r[0] for r in окно) + ЗАПАС, max(r[1] for r in окно) + ЗАПАС])
    return сглаж


def главная():
    im = Image.open(ИСХОДНИК)
    рыба = вырезать(im)
    альфа = np.asarray(рыба.getchannel('A'))
    точки, длина = сплайн(ХРЕБЕТ, ТОЧЕК)
    ш = ширины(альфа, точки)

    # обрезаем по сетке и прозрачности — лишние поля не качаем
    xs, ys = [], []
    for (x, y), (l, r), i in zip(точки, ш, range(len(точки))):
        a, b = точки[max(0, i - 1)], точки[min(len(точки) - 1, i + 1)]
        d = math.dist(a, b) or 1
        n = (-(b[1] - a[1]) / d, (b[0] - a[0]) / d)
        for s in (l, -r):
            xs.append(x + n[0] * s)
            ys.append(y + n[1] * s)
    x0, y0 = max(0, int(min(xs)) - 2), max(0, int(min(ys)) - 2)
    x1, y1 = min(рыба.width, int(max(xs)) + 3), min(рыба.height, int(max(ys)) + 3)
    рыба = рыба.crop((x0, y0, x1, y1))
    КУДА.mkdir(parents=True, exist_ok=True)
    рыба.save(КУДА / 'koi.webp', 'WEBP', quality=90, method=6)
    сетка = {'w': рыба.width, 'h': рыба.height, 'dlina': round(длина, 1),
             'hrebet': [[round(x - x0, 1), round(y - y0, 1), round(l, 1), round(r, 1)] for (x, y), (l, r) in zip(точки, ш)]}
    (КУДА / 'koi.json').write_text(json.dumps(сетка, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'assets/ryba/koi.webp  {рыба.width}×{рыба.height}  {(КУДА / "koi.webp").stat().st_size // 1024} КБ')
    print(f'assets/ryba/koi.json  {ТОЧЕК} рядов, длина хребта {длина:.0f}')

    if '--proverka' in sys.argv:
        путь = sys.argv[sys.argv.index('--proverka') + 1]
        фон = Image.new('RGBA', рыба.size, (11, 110, 79, 255))
        фон.alpha_composite(рыба)
        dr = ImageDraw.Draw(фон)
        pts = [(x - x0, y - y0) for x, y in точки]
        dr.line(pts, fill=(255, 255, 0, 255), width=2)
        лево, право = [], []
        for i, ((x, y), (l, r)) in enumerate(zip(pts, ш)):
            a, b = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]
            d = math.dist(a, b) or 1
            n = (-(b[1] - a[1]) / d, (b[0] - a[0]) / d)
            лево.append((x + n[0] * l, y + n[1] * l))
            право.append((x - n[0] * r, y - n[1] * r))
            dr.line([лево[-1], право[-1]], fill=(255, 255, 255, 90), width=1)
        dr.line(лево, fill=(0, 255, 255, 255), width=2)
        dr.line(право, fill=(255, 0, 255, 255), width=2)
        фон.save(путь)


if __name__ == '__main__':
    главная()
