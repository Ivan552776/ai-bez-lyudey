# Карп кои первого экрана сайта

## Действующая картинка — собственная генерация, 14.10.2026

- Исходник: `_stati/ryba/koi-generated-v2.png`, 1024×1536, настоящий RGBA.
- Создан встроенным инструментом OpenAI `image_gen` в Codex для этого проекта.
  Входных изображений и чужих референсов не передавали. Модель инструментом
  не указана, поэтому её название здесь не приписывается.
- Итог: `koi-v2.webp`, 731×1506, и `koi-v2.json` с 44 рядами сетки.
  Их воспроизводит `_stati/ryba_podgotovka.py`; он сохраняет исходную
  прозрачность и обрезает поля. Новые имена нужны для обновления кеша.
- Это сгенерированное изображение, **не CC0 и не найденная стоковая фотография**.
  Основание использования — условия сервиса OpenAI: права на результат между
  пользователем и OpenAI принадлежат пользователю в пределах применимого права.
  Коммерческое использование результата допускается при соблюдении условий.
  Это не утверждение об исключительности изображения или охране авторским правом.
  Сверено 14.10.2026: [Terms of Use](https://openai.com/en-GB/policies/row-terms-of-use/),
  [справка о коммерческом использовании](https://help.openai.com/en/articles/6783457-chatgpt-general-faq2023).

Проверка подготовки: сетка просмотрена на зелёном фоне; ни один видимый пиксель
(альфа ≥ 20 из 255) не выходит за её границы. Обе лопасти хвоста и плавники целые,
альфа в четырёх углах итоговой картинки — 0. Проверка анимации в браузере — отдельно.

## Точный запрос генерации

```text
Use case: stylized-concept
Asset type: a single transparent koi fish sprite for an elegant interactive pond on a website, to be gently animated using a flexible spine mesh.
Primary request: create one original beautiful Japanese koi fish, seen strictly from directly above. Full fish isolated on genuinely transparent background with a real alpha channel. A realistic three-dimensional premium natural-history rendering, refined scale detail, soft natural highlights. White ivory body with rich vermilion red patches and a few ink-black patches, delicate translucent cream fins with subtle warm orange accents. Natural healthy koi anatomy, a calm elegant look.
Composition/framing: portrait canvas. Nose centered near the top, tail toward the bottom. Whole fish visible with comfortable transparent margins; long streamlined body nearly straight along the vertical axis, only a very gentle graceful curve. Paired pectoral fins spread to each side, thin dorsal fin lying naturally along the spine, tapered rear body and a beautiful simple forked tail. The head should be smaller than the torso, two small natural eyes visible symmetrically from above. A single fish, no other objects.
Lighting/mood: even soft daylight from above, volumetric but no cast shadow.
Constraints: original artwork with no input references; anatomically credible koi, clean well-defined silhouette for animation, translucent fin detail preserved. No water, no ripples, no pool, no shadow outside fish, no floor, no background color, no checkerboard, no caption, no text, no logo, no watermark. Do not copy a stock illustration.
```

## Прежняя картинка

Первый исходник 920×990 прислал Ivan 09.10.2026. Его первоисточник и разрешение
на коммерческое использование не удалось подтвердить. Он не использовался
как референс новой генерации. Прежние `iskhodnik.webp`, `koi.webp` и `koi.json`
удалены из текущего дерева после переключения страницы на `koi-v2.*`.
В истории Git они могут оставаться.
