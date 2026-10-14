// Картинки-превью 1200×630 для ссылок в Telegram, ВК и поиске (09.10.2026).
// Список пишет sobrat.py в _stati/oblozhki.json; картинки — stati/og/<slug>.jpg.
// Рисует невидимый Chrome, шрифты и робот — свои, из assets/.
//
//   node _stati/oblozhki.mjs            (нужен playwright; путь к нему — PLAYWRIGHT или глобальная установка)
//
// Новая статья — новая картинка; у старой, если поменялся заголовок, лучше новое имя:
// Telegram долго помнит превью по адресу картинки.
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import { fileURLToPath, pathToFileURL } from 'node:url';

const здесь = path.dirname(fileURLToPath(import.meta.url));
const корень = path.resolve(здесь, '..');
const pw = await import(process.env.PLAYWRIGHT || '/opt/node22/lib/node_modules/playwright/index.mjs')
  .catch(() => import('playwright'));
const chromium = pw.chromium || pw.default.chromium;

const список = JSON.parse(fs.readFileSync(path.join(здесь, 'oblozhki.json'), 'utf8'));
const куда = path.join(корень, 'stati', 'og');
fs.mkdirSync(куда, { recursive: true });
const ф = n => pathToFileURL(path.join(корень, 'assets', 'fonts', n)).href;
const esc = s => s.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
const робот = п => pathToFileURL(path.join(корень, 'assets', 'robot', п + '.webp')).href;

const стиль = `
@font-face{font-family:G;font-weight:500;src:url(${ф('golos-text-500-cyrillic.woff2')})}
@font-face{font-family:G;font-weight:700;src:url(${ф('golos-text-700-cyrillic.woff2')})}
@font-face{font-family:G;font-weight:500;src:url(${ф('golos-text-500-latin.woff2')});unicode-range:U+0000-00FF}
@font-face{font-family:G;font-weight:700;src:url(${ф('golos-text-700-latin.woff2')});unicode-range:U+0000-00FF}
*{box-sizing:border-box;margin:0}
body{width:1200px;height:630px;overflow:hidden;font-family:G,sans-serif;color:#0E2420;
 background:radial-gradient(700px 420px at 90% 0%,rgba(255,255,255,.8),transparent 62%),radial-gradient(640px 400px at 0% 100%,rgba(127,224,180,.55),transparent 60%),#D6F2E4}
.top{position:absolute;left:64px;top:56px;display:flex;align-items:center;gap:16px;font-weight:700;font-size:30px}
.mk{display:grid;place-items:center;width:56px;height:56px;border-radius:17px;background:#0E2420;color:#7FE0B4;font-size:24px}
.chip{position:absolute;left:64px;bottom:60px;font-weight:700;font-size:24px;background:#fff;color:#08563E;border-radius:999px;padding:12px 24px}
h1{position:absolute;left:64px;top:160px;width:640px;font-weight:700;font-size:62px;line-height:1.08;letter-spacing:-.02em}
img{position:absolute;right:48px;bottom:30px;height:520px;max-width:440px;object-fit:contain;object-position:right bottom;filter:drop-shadow(0 22px 22px rgba(14,36,32,.16))}
.big h1{top:150px;width:900px;font-size:150px;line-height:.98;letter-spacing:-.05em;text-transform:uppercase}
.big .chip{font-size:28px}
`;

// Пруд снимается с настоящей страницы: file:// не даёт загрузить JSON скелета.
const server = http.createServer((req,res)=>{
  let name;try{name=decodeURIComponent(new URL(req.url,'http://localhost').pathname)}catch{res.writeHead(400).end();return}
  const file=path.resolve(корень,'.'+name+(name.endsWith('/')?'index.html':''));
  if(!file.startsWith(корень+path.sep)){res.writeHead(403).end();return}
  const mime={'.html':'text/html; charset=utf-8','.json':'application/json','.webp':'image/webp','.woff2':'font/woff2'};
  fs.readFile(file,(err,data)=>{if(err){res.writeHead(404).end();return}res.setHeader('Content-Type',mime[path.extname(file)]||'application/octet-stream');res.end(data)});
});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const b = await chromium.launch({...(process.env.CHROME ? { executablePath: process.env.CHROME } : {}),args:['--enable-unsafe-swiftshader']});
const p = await b.newPage({ viewport: { width: 1200, height: 630 } });
for (const o of список.filter(o=>!process.argv.includes('--tolko-kursy')||o.slug==='kursy')) {
  if(o.slug==='kursy'){
    await p.emulateMedia({colorScheme:'light',reducedMotion:'reduce'});
    await p.goto(`http://127.0.0.1:${server.address().port}/kursy/`);
    await p.evaluate(()=>document.fonts.ready);
    await p.addStyleTag({content:'.site,.ft,.scena~.wrap,.pod,.btns,.pond-pause{display:none!important}.scena{margin:0;border-radius:0;height:630px;min-height:630px}.scena-in{padding:40px 16px}.giant{font-size:200px}.scena .sub{font-size:24px;max-width:1000px}'});
    await p.evaluate(()=>dispatchEvent(new Event('resize')));
    await p.waitForSelector('.scena.voda');
    await p.waitForFunction(()=>{const i=performance.getEntriesByType('resource').find(x=>x.name.includes('koi-v2.webp'));return !!i});
    await p.waitForTimeout(250);
    await p.screenshot({path:path.join(куда,'kursy-prud-v2.jpg'),type:'jpeg',quality:88});
    console.log('stati/og/kursy-prud-v2.jpg — кадр пруда');
    continue;
  }
  // длинный заголовок — мельче, чтобы влез в три строки
  const размер = o.big ? '' : o.title.length > 60 ? 'font-size:50px' : o.title.length > 42 ? 'font-size:56px' : '';
  const html = `<!doctype html><html lang="ru"><head><meta charset="utf-8"><style>${стиль}</style></head>
<body class="${o.big ? 'big' : ''}"><div class="top"><span class="mk">ии</span>ИИ без людей</div>
<h1 style="${размер}">${esc(o.title)}</h1><span class="chip">${esc(o.rubrika)}</span>
<img src="${робот(o.robot)}" alt=""></body></html>`;
  const tmp = path.join(здесь, '.og.html');
  fs.writeFileSync(tmp, html);
  await p.goto(pathToFileURL(tmp).href);
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(120);
  const выход = path.join(куда, o.slug + '.jpg');
  await p.screenshot({ path: выход, type: 'jpeg', quality: 84 });
  console.log(`stati/og/${o.slug}.jpg  ${Math.round(fs.statSync(выход).size / 1024)} КБ`);
  fs.unlinkSync(tmp);
}
await b.close();
server.close();
