/* Офлайн для «ИИ без людей».

   Стратегия: сеть первой, кеш запасным. Так человек всегда получает свежую
   версию, когда сеть есть, и приложение всё равно открывается в метро.
   Обратный порядок (кеш первым) заперал бы людей на старой версии — при том,
   что приложение мы правим почти каждый день. */
const КЕШ = 'mzr-v3';
// Только сама страница. Раньше в списке был и './' — если хоть один адрес
// не загрузится, установка падает целиком, а вместе с ней и весь офлайн.
const СВОЁ = ['./index.html'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(КЕШ).then(c => c.addAll(СВОЁ)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys()
    .then(имена => Promise.all(имена.filter(n => /^mzr-v\d+$/.test(n) && n !== КЕШ).map(n => caches.delete(n))))
    .then(() => self.clients.claim()));
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if(req.method !== 'GET') return;
  const url = new URL(req.url);
  // чужие адреса не трогаем: платные уроки и проверка доступа должны идти
  // только по-настоящему, иначе можно показать закрытое из кеша
  if(url.origin !== location.origin) return;

  // Сеть по-прежнему первая, но ждём её не дольше двух с половиной секунд.
  // Страница весит почти мегабайт: на слабой мобильной связи ожидание
  // превращалось в белый экран, хотя вчерашняя копия лежала рядом. Свежую
  // всё равно докачиваем в кеш — следующий запуск будет уже новым.
  const свежая = fetch(req).then(ответ => {
    if(ответ && ответ.status === 200){
      const копия = ответ.clone();
      e.waitUntil(caches.open(КЕШ).then(c => c.put(req, копия)).catch(() => {}));
    }
    return ответ;
  });

  e.respondWith((async () => {
    const копия = await caches.match(req);
    if(!копия){
      try { return await свежая; }
      catch(err){
        if(req.mode === 'navigate'){
          const page = await caches.match('./index.html');
          if(page) return page;
        }
        // Missing media must never receive an HTML page as its response.
        return new Response('Нет сети', {status: 503, headers: {'Content-Type': 'text/plain; charset=utf-8'}});
      }
    }
    // Самой странице даём сети больше времени: показать вчерашнюю сборку
    // приложения хуже, чем подождать секунду-другую. Картинкам и шрифтам
    // хватает и двух с половиной секунд — они между версиями не меняются.
    const окно = req.mode === 'navigate' ? 6000 : 2500;
    const подождать = new Promise(готово => setTimeout(() => готово(null), окно));
    return (await Promise.race([свежая.catch(() => null), подождать])) || копия;
  })());
});
