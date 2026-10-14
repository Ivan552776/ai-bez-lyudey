// Проверка публичного сайта; настоящие телефоны и нагрев этим не измеряются.
// PLAYWRIGHT=/путь/playwright/index.mjs CHROME=/путь/Chrome node _stati/qa/proverka.mjs
// Сначала: python3 -m http.server с корнем, содержащим ai-bez-lyudey/.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const {chromium}=await import(process.env.PLAYWRIGHT || 'playwright');
const root=process.env.SITE_URL || 'http://127.0.0.1:4376/ai-bez-lyudey/';
const out=process.env.QA_OUT || '/tmp/mzr-seo-qa';fs.mkdirSync(out,{recursive:true});
const browser=await chromium.launch({executablePath:process.env.CHROME,args:['--enable-unsafe-swiftshader']});
const report={layouts:[],checks:[],errors:[]};
const context=await browser.newContext({viewport:{width:390,height:844},deviceScaleFactor:2,isMobile:true,hasTouch:true});
await context.addInitScript(()=>{
 window.__draws=0;
 const draw=WebGLRenderingContext.prototype.drawArrays;
 WebGLRenderingContext.prototype.drawArrays=function(...args){window.__draws++;return draw.apply(this,args)};
});
const p=await context.newPage();
p.on('pageerror',e=>report.errors.push(e.message));
p.on('console',m=>{if(m.type()==='error')report.errors.push(m.text()+' @ '+m.location().url)});
const open=async url=>{await p.goto(root+url);await p.evaluate(()=>document.fonts.ready)};
try{
 const slugs=fs.readdirSync(new URL('../../stati/',import.meta.url)).filter(n=>fs.existsSync(new URL('../../stati/'+n+'/index.html',import.meta.url)));
 for(const theme of (process.env.QA_BEHAVIOR_ONLY?[]:['light','dark']))for(const width of [360,390,430]){
  await p.setViewportSize({width,height:844});await p.emulateMedia({colorScheme:theme,reducedMotion:'reduce'});
  for(const route of ['kursy/','stati/',...slugs.map(s=>'stati/'+s+'/')]){
   await open(route);
   const measure=await p.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth,title:document.title,small:[...document.querySelectorAll('.nav a,.brand,.tg,.btn,.copy,.f,.crumbs a,.toc-m a,.urok-a a,summary,.pond-pause:not([hidden])')].filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0&&(r.width<44||r.height<44)}).map(e=>e.textContent.trim())}));
   assert(measure.scroll<=width+1,`${route} ${width} ${theme}: горизонтальная прокрутка`);assert.deepEqual(measure.small,[],`${route}: маленькая кнопка`);
   report.layouts.push({route,width,theme});
   if(route==='kursy/'||route==='stati/kak-polzovatsya-neyrosetyu/')await p.screenshot({path:path.join(out,`${route==='kursy/'?'pond':'article'}-${width}-${theme}.png`)});
  }
 }
 if(!process.env.QA_BEHAVIOR_ONLY)report.checks.push('14 страниц × 3 ширины × 2 темы: переполнение и кнопки');
 await p.setViewportSize({width:390,height:844});await p.emulateMedia({colorScheme:'light',reducedMotion:'no-preference'});await open('kursy/');
 await p.waitForSelector('.scena.voda');await p.waitForTimeout(300);
 const moving=await p.evaluate(()=>window.__draws);await p.waitForTimeout(350);assert(await p.evaluate(()=>window.__draws)>moving,'Пруд движется');
 await p.locator('[data-pond-pause]').click();const paused=await p.evaluate(()=>window.__draws);await p.waitForTimeout(200);assert.equal(await p.evaluate(()=>window.__draws),paused,'Пауза останавливает GPU');
 await p.locator('[data-pond-pause]').click();await p.waitForTimeout(100);
 await p.evaluate(()=>scrollTo(0,document.querySelector('.scena').offsetTop+document.querySelector('.scena').offsetHeight+100));await p.waitForTimeout(150);const off=await p.evaluate(()=>window.__draws);await p.waitForTimeout(200);assert.equal(await p.evaluate(()=>window.__draws),off,'Пруд за экраном остановлен');
 await p.evaluate(()=>scrollTo(0,0));await p.waitForTimeout(200);assert(await p.evaluate(()=>window.__draws)>off,'Пруд снова движется');
 await p.emulateMedia({reducedMotion:'reduce'});await p.waitForFunction(()=>document.querySelector('[data-pond-pause]').disabled);await p.waitForTimeout(50);const reduced=await p.evaluate(()=>window.__draws);await p.waitForTimeout(200);assert.equal(await p.evaluate(()=>window.__draws),reduced);assert(await p.locator('[data-pond-pause]').isDisabled());
 await p.emulateMedia({reducedMotion:'no-preference'});await p.waitForTimeout(200);assert(await p.evaluate(()=>window.__draws)>reduced);
 report.checks.push('Пруд: движение, пауза, прокрутка, изменение reduced-motion без перезагрузки');
 await p.locator('.kurs-l').first().click();await p.waitForURL('**/uroki/**');assert(await p.locator('h1').count());await p.goBack();await p.waitForSelector('.scena');
 await p.locator('.nav a[href$="stati/"]').click();await p.waitForURL('**/stati/');
 await p.locator('.f[data-f="teksty"]').click();assert.equal(await p.locator('#spisok .card:visible:not([data-r="teksty"])').count(),0);
 await p.locator('#spisok .card:visible').first().click();await p.waitForSelector('.body');
 await p.locator('.toc-m summary').click();await p.locator('.toc-m a').first().click();assert.equal(await p.locator('.toc-m').getAttribute('open'),null);
 await p.evaluate(()=>{window.__copy='';Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async text=>{window.__copy=text}}})});
 await p.locator('[data-copy]').first().click();assert((await p.evaluate(()=>window.__copy)).length>30);
 await p.evaluate(()=>Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:()=>Promise.reject(new Error('closed'))}}));
 await p.locator('[data-copy]').first().click();assert((await p.evaluate(()=>getSelection().toString())).length>30);
 report.checks.push('Курс → урок → назад; статьи → рубрика → статья → оглавление; копирование и отказ буфера');
 await open('kursy/');await p.locator('.faq summary').first().click();assert(await p.locator('.faq details').first().getAttribute('open')!==null);
 await p.waitForSelector('.scena.voda');await p.evaluate(()=>document.querySelector('.ryba').getContext('webgl').getExtension('WEBGL_lose_context').loseContext());await p.waitForTimeout(100);
 assert(!(await p.locator('.scena').getAttribute('class')).includes('voda'));assert.notEqual(await p.locator('.giant').evaluate(e=>getComputedStyle(e).color),'rgba(0, 0, 0, 0)');
 report.checks.push('FAQ; потеря WebGL возвращает заголовок и обычные ссылки');
 const nojs=await browser.newContext({javaScriptEnabled:false,viewport:{width:360,height:800}});const np=await nojs.newPage();await np.goto(root+'kursy/');assert(await np.locator('.giant').isVisible());await np.locator('.kurs-l').first().click();await np.waitForURL('**/uroki/**');await nojs.close();
 report.checks.push('Без JavaScript: заголовок, курсы и переход к уроку доступны');
 assert.deepEqual(report.errors,[],'Консоль браузера');report.passed=true;
}catch(e){report.passed=false;report.failure=e.stack;process.exitCode=1}
finally{fs.writeFileSync(path.join(out,process.env.QA_BEHAVIOR_ONLY?'behavior-report.json':'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({passed:report.passed,layouts:report.layouts.length,checks:report.checks,errors:report.errors,failure:report.failure},null,2));await browser.close()}
