// Ночная проверка живого приложения (02.10.2026).
// Робот открывает настоящее приложение, как новичок, и проходит главный путь:
// первый экран → «Начать бесплатно» → урок → главная со всеми курсами → поиск.
// Потом проверяет сервер доступа и открытые страницы сайта.
// Запускается в GitHub Actions каждую ночь (.github/workflows/nochnaya.yml).
// Итог — строками ::notice:: и ::error:: — утром забирает бот и пишет Ivan'у.
// Ключей и личных данных здесь нет: робот ходит как человек без входа.
//
//   CHROME=<путь к Chrome> node qa/nochnaya.mjs
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const САЙТ = 'https://ivan552776.github.io';
const ПРИЛОЖЕНИЕ = process.env.APP_URL || САЙТ + '/ai-bez-lyudey/';   // APP_URL — только для проверки самой проверки
const СЕРВЕР = 'https://abstract-tolerant-ember.ruweb.place';
const CHROME = process.env.CHROME || '/usr/bin/google-chrome';

const беды = [];
const итог = [];
const беда = (где, что) => беды.push(`${где}: ${что}`);
const sleep = ms => new Promise(r => setTimeout(r, ms));

// ---------- невидимый Chrome по протоколу отладки ----------
const port = 9400 + Math.floor(Math.random() * 400);
const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'nochnaya-'));
const chrome = spawn(CHROME, ['--headless=new', `--remote-debugging-port=${port}`, `--user-data-dir=${dir}`,
  '--no-first-run', '--no-sandbox', '--hide-scrollbars', '--window-size=390,844', 'about:blank'], { stdio: 'ignore' });
let target;
for (let i = 0; i < 80 && !target; i++) {
  await sleep(150);
  try { target = (await (await fetch(`http://127.0.0.1:${port}/json`)).json()).find(t => t.type === 'page'); } catch {}
}
if (!target) { console.log('::error title=Ночная проверка::Chrome не запустился'); process.exit(1); }
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise(r => (ws.onopen = r));
let id = 0;
const ждут = new Map();
const ошибкиСтраницы = [];
ws.onmessage = m => {
  const d = JSON.parse(m.data);
  if (d.id && ждут.has(d.id)) { ждут.get(d.id)(d); ждут.delete(d.id); return; }
  if (d.method === 'Runtime.exceptionThrown') {
    const e = d.params.exceptionDetails;
    ошибкиСтраницы.push(`${(e.url || '').split('/').pop()}:${e.lineNumber} ${e.exception?.description?.split('\n')[0] || e.text}`);
  }
};
const send = (method, params = {}) => new Promise(r => { const i = ++id; ждут.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
const ev = async js => {
  const r = await send('Runtime.evaluate', { expression: `(async()=>{${js}})()`, awaitPromise: true, returnByValue: true });
  if (r.result?.exceptionDetails) throw Error(r.result.exceptionDetails.exception?.description || 'ошибка в проверке');
  return r.result?.result?.value;
};
// ждать, пока условие на странице не станет правдой
const дождаться = async (js, мс = 15000) => {
  const до = Date.now() + мс;
  while (Date.now() < до) {
    try { if (await ev(`return !!(${js})`)) return true; } catch {}
    await sleep(250);
  }
  return false;
};

await send('Runtime.enable');
await send('Network.enable');
await send('Network.setCacheDisabled', { cacheDisabled: true });   // как новичок: ничего не закешировано
await send('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 2, mobile: true });

// ---------- 1. первый экран ----------
const старт = Date.now();
await send('Page.navigate', { url: ПРИЛОЖЕНИЕ });
if (!(await дождаться(`document.querySelector('.view.on')`, 30000))) {
  беда('Первый экран', 'за 30 секунд не появился ни один экран');
} else {
  const секунд = ((Date.now() - старт) / 1000).toFixed(1);
  const экран = await ev(`return document.querySelector('.view.on').id`);
  итог.push(`первый экран за ${секунд} с`);
  if (+секунд > 10) беда('Первый экран', `появился только через ${секунд} с`);
  if (экран !== 'v-hello') беда('Первый экран', `новичку открылся ${экран}, а не знакомство`);

  // ---------- 2. «Начать бесплатно» → урок ----------
  if (await дождаться(`document.getElementById('hi-go')`, 5000)) {
    await ev(`document.getElementById('hi-go').click()`);
    if (!(await дождаться(`document.querySelector('#v-lesson.on, #v-study.on, #v-route.on')`, 15000))) {
      беда('«Начать бесплатно»', 'после нажатия не открылся ни урок, ни главная');
    } else {
      const куда = await ev(`return document.querySelector('.view.on').id`);
      if (куда === 'v-lesson') {
        await дождаться(`document.querySelectorAll('#v-lesson .on, #v-lesson p').length > 10`, 15000);
        const абзацев = await ev(`return document.querySelectorAll('#v-lesson p').length`);
        if (абзацев < 10) беда('Первый урок', `в уроке всего ${абзацев} абзацев — похоже, текст не загрузился`);
        else итог.push(`первый урок открылся (${абзацев} абзацев)`);
      } else {
        итог.push(`после «Начать» открылся ${куда}`);
      }
    }
  } else {
    беда('Первый экран', 'нет кнопки «Начать бесплатно»');
  }

  // ---------- 3. главная: все курсы ----------
  await ev(`document.querySelector('[data-go="study"]')?.click()`);
  if (!(await дождаться(`document.getElementById('v-study')?.classList.contains('on')`, 10000))) {
    беда('Главная', 'не открылась');
  } else {
    await дождаться(`document.querySelectorAll('#v-study .s-course-chip').length >= 8`, 10000);
    const курсов = await ev(`return document.querySelectorAll('#v-study .s-course-chip').length`);
    if (курсов < 8) беда('Главная', `видно ${курсов} курсов вместо восьми`);
    else итог.push(`на главной ${курсов} карточек курсов`);
  }

  // ---------- 4. поиск ----------
  await ev(`document.querySelector('[data-go="search"]')?.click()`);
  if (await дождаться(`document.getElementById('v-search')?.classList.contains('on') && document.getElementById('sr-input')`, 10000)) {
    // результаты считаем как прибавку кнопок после ввода: пустой экран поиска их тоже содержит
    const было = await ev(`return document.querySelectorAll('#v-search button, #v-search a').length`);
    await ev(`const i=document.getElementById('sr-input'); i.value='договор'; i.dispatchEvent(new Event('input',{bubbles:true}))`);
    await sleep(1500);
    const найдено = await ev(`return document.querySelectorAll('#v-search button, #v-search a').length`) - было;
    if (найдено < 3) беда('Поиск', `по слову «договор» нашлось ${Math.max(0, найдено)} — поиск, похоже, сломан`);
    else итог.push(`поиск находит (${найдено} по слову «договор»)`);
  } else {
    беда('Поиск', 'экран поиска не открылся');
  }

  // ---------- 5. ошибки на странице ----------
  const сбои = await ev(`return (window.__сбои || []).map(x => x.join(' '))`);
  for (const с of [...new Set([...ошибкиСтраницы, ...сбои])].slice(0, 5)) беда('Ошибка в приложении', с);
}
ws.close();
chrome.kill();

// ---------- 6. сервер доступа ----------
try {
  const r = await fetch(СЕРВЕР + '/health', { signal: AbortSignal.timeout(15000) });
  const d = await r.json();
  if (!d.ok) беда('Сервер', `/health ответил ${r.status}`);
  else итог.push('сервер отвечает');
} catch (e) { беда('Сервер', `не отвечает: ${e.message}`); }
try {
  const r = await fetch(СЕРВЕР + '/api/posts', { headers: { Origin: САЙТ }, signal: AbortSignal.timeout(15000) });
  const d = await r.json();
  if (!r.headers.get('access-control-allow-origin')) беда('Сервер', 'приложению запрещено к нему обращаться (нет CORS)');
  if (!(d.posts || []).length) беда('Сервер', 'список постов канала пуст');
} catch (e) { беда('Сервер', `посты не отдаёт: ${e.message}`); }

// ---------- 7. открытые страницы сайта ----------
const страницы = ['/', '/ai-bez-lyudey/uroki/', '/ai-bez-lyudey/neyroseti/', '/ai-bez-lyudey/sitemap.xml',
  '/robots.txt', '/yandex_88c739c6c4c16d75.html', '/google14408fe3eb5d61da.html'];
let открылось = 0;
for (const п of страницы) {
  try {
    const r = await fetch(САЙТ + п, { signal: AbortSignal.timeout(15000) });
    if (r.ok) открылось++;
    else беда('Сайт', `${п} отвечает ${r.status}`);
  } catch (e) { беда('Сайт', `${п} не открылся: ${e.message}`); }
}
итог.push(`страниц сайта открылось ${открылось} из ${страницы.length}`);

// ---------- отчёт ----------
const чисто = s => String(s).replace(/[\r\n]+/g, ' ').replace(/%/g, '%25').slice(0, 300);
console.log(`::notice title=Итог::${чисто(итог.join(' · '))}`);
for (const б of беды) console.log(`::error title=Поломка::${чисто(б)}`);
try { fs.rmSync(dir, { recursive: true, force: true }); } catch {}
process.exit(беды.length ? 1 : 0);
