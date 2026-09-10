/* Офлайн для «ИИ без людей».

   Стратегия: сеть первой, кеш запасным. Так человек всегда получает свежую
   версию, когда сеть есть, и приложение всё равно открывается в метро.
   Обратный порядок (кеш первым) заперал бы людей на старой версии — при том,
   что приложение мы правим почти каждый день. */
const КЕШ = 'mzr-v1';
// Только сама страница. Раньше в списке был и './' — если хоть один адрес
// не загрузится, установка падает целиком, а вместе с ней и весь офлайн.
const СВОЁ = ['./index.html'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(КЕШ).then(c => c.addAll(СВОЁ)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys()
    .then(имена => Promise.all(имена.filter(n => n !== КЕШ).map(n => caches.delete(n))))
    .then(() => self.clients.claim()));
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if(req.method !== 'GET') return;
  const url = new URL(req.url);
  // чужие адреса не трогаем: платные уроки и проверка доступа должны идти
  // только по-настоящему, иначе можно показать закрытое из кеша
  if(url.origin !== location.origin) return;

  e.respondWith(
    fetch(req).then(ответ => {
      if(ответ && ответ.status === 200){
        const копия = ответ.clone();
        caches.open(КЕШ).then(c => c.put(req, копия));
      }
      return ответ;
    }).catch(() => caches.match(req).then(c => c || caches.match('./index.html')))
  );
});
