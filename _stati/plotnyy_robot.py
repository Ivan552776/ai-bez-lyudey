#!/usr/bin/env python3
"""Плотные позы робота для первого экрана сайта (09.10.2026).

Картинки в assets/robot/ вырезаны так, что белое тело робота почти прозрачное:
на светлом фоне не заметно, а поверх тёмных букв робот «просвечивает насквозь».
Здесь тело заливается непрозрачным — цветом, каким оно выглядит на белом,
а мягкий край и тень под ногами остаются как были.

Внутренность находим заливкой снаружи: всё, куда от края картинки можно дойти
по почти прозрачным точкам, — фон; остальное — робот.
Пишет assets/robot/sayt/<поза>.webp (новые имена: старые файлы живут в кеше у людей).
Запуск: python3 _stati/plotnyy_robot.py
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

КОРЕНЬ = Path(__file__).resolve().parent.parent
ПОЗЫ = ['privet', 'ukazyvaet', 'raduetsya', 'dumaet']
ПОРОГ = 40       # ниже — «почти прозрачно», по таким точкам заливка идёт снаружи внутрь
ШОВ = 21         # контур тела местами рвётся: сначала его «зашиваем», потом заливаем


def плотная(путь):
    im = Image.open(путь).convert('RGBA')
    a = np.asarray(im.getchannel('A'), dtype=np.float32) / 255
    rgb = np.asarray(im.convert('RGB'), dtype=np.float32)
    # как точка выглядит на белом — так робота и рисовали
    на_белом = rgb * a[..., None] + 255 * (1 - a[..., None])

    маска = Image.fromarray(((a * 255) >= ПОРОГ).astype(np.uint8) * 255)
    маска = маска.filter(ImageFilter.MaxFilter(ШОВ)).filter(ImageFilter.MinFilter(ШОВ))
    рамка = Image.new('L', (маска.width + 2, маска.height + 2), 0)
    рамка.paste(маска, (1, 1))
    ImageDraw.floodfill(рамка, (0, 0), 128)
    снаружи = np.asarray(рамка, dtype=np.uint8)[1:-1, 1:-1] == 128
    внутри = ~снаружи
    # тень под ногами нарисована вместе с роботом: её не заливаем — у сцены своя тень
    # «под ногами» — всё, что в своём столбце ниже последней плотной точки
    строки = np.arange(a.shape[0])[:, None]
    плотно = a >= .6
    подошва = np.where(плотно.any(axis=0), (плотно * строки).max(axis=0), -1)
    внутри &= ~(строки > подошва[None, :])
    # кольцо в 2 точки по краю оставляем мягким, глубже — полностью непрозрачно
    глубоко = np.asarray(Image.fromarray(внутри.astype(np.uint8) * 255).filter(ImageFilter.MinFilter(5))) > 0

    новая_a = np.where(глубоко, 1.0, np.where(внутри, np.maximum(a, 0.85), a))
    цвет = np.where(внутри[..., None], на_белом, rgb)
    out = np.dstack([np.clip(цвет, 0, 255), np.clip(новая_a * 255, 0, 255)]).astype(np.uint8)
    return Image.fromarray(out, 'RGBA')


if __name__ == '__main__':
    куда = КОРЕНЬ / 'assets' / 'robot' / 'sayt'
    куда.mkdir(exist_ok=True)
    for п in ПОЗЫ:
        im = плотная(КОРЕНЬ / 'assets' / 'robot' / f'{п}.webp')
        f = куда / f'{п}.webp'
        im.save(f, 'WEBP', quality=88, method=6)
        print(f'{f.relative_to(КОРЕНЬ)}  {im.size}  {f.stat().st_size // 1024} КБ')
