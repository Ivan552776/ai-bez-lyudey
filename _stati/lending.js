(function(){
/* Робот первого экрана гуляет сам: идёт к случайной точке, останавливается,
   машет или думает и идёт дальше. Повёл мышью — подбегает к курсору;
   на телефоне — туда, где коснулись. Курсор замер — снова гуляет сам.
   Двигаем только transform: без перерисовки страницы и без рывков на слабых телефонах. */
var сцена=document.querySelector('.scena');
if(!сцена)return;
var бот=сцена.querySelector('.bot'),тело=бот.querySelector('.bot-t'),тень=бот.querySelector('.bot-ten'),реплика=бот.querySelector('.bot-replika');
var позы={};[].forEach.call(бот.querySelectorAll('img[data-p]'),function(i){позы[i.dataset.p]=i});
if(matchMedia('(prefers-reduced-motion: reduce)').matches)return;   // стоит и машет, без беготни

/* Остальные позы догружаем после первой отрисовки: первый экран не ждёт картинок, которых ещё не видно */
addEventListener('load',function(){[].forEach.call(бот.querySelectorAll('img[data-src]'),function(i){i.src=i.dataset.src;i.removeAttribute('data-src')})});

var W=0,H=0,bw=0,bh=0;
function мерить(){var r=сцена.getBoundingClientRect();W=r.width;H=r.height;bw=бот.offsetWidth;bh=бот.offsetHeight}
мерить();
/* Стартуем ровно с того места, где робот стоял без скрипта, — без прыжка */
var r0=бот.getBoundingClientRect(),rs=сцена.getBoundingClientRect();
var x=r0.left-rs.left,y=r0.top-rs.top,vx=0,vy=0;
бот.classList.add('zhivoy');

var режим='идёт',цельX=x,цельY=y,ждать=0,курсорX=0,курсорY=0,курсорКогда=0,касание=false;
var шаг=0,взгляд=-1,поза='privet',прежде=performance.now(),идёт=false,реплТаймер=0;
var РЕПЛИКИ=['Привет! Я веду этот канал','Людей в редакции нет — только я','Выбери нейросеть — научу','Попробуй бесплатный урок','Запрос копируй — и пробуй'];
var номерРеплики=0;

function показатьПозу(п){if(п===поза||!позы[п]||позы[п].dataset.src)return;позы[поза]&&позы[поза].classList.remove('on');позы[п].classList.add('on');поза=п}
function сказать(){реплика.textContent=РЕПЛИКИ[номерРеплики++%РЕПЛИКИ.length];
  /* у края сцены облачко прижимается к роботу с внутренней стороны, иначе его обрежет */
  var центр=x+bw/2,пол=Math.min(130,W/2);реплика.classList.toggle('l',центр<пол);реплика.classList.toggle('r',центр>W-пол);реплика.classList.add('on');clearTimeout(реплТаймер);реплТаймер=setTimeout(function(){реплика.classList.remove('on')},2600)}
function новаяЦель(){
    /* сверху запас под облачко с репликой */
  var поляX=Math.max(8,W*.04),верх=64,низ=Math.max(8,H*.05);
  for(var k=0;k<8;k++){
    var nx=поляX+Math.random()*Math.max(1,W-bw-2*поляX),ny=верх+Math.random()*Math.max(1,H-bh-верх-низ);
    if(Math.hypot(nx-x,ny-y)>Math.min(W,H)*.3)break;
  }
  цельX=nx;цельY=ny;
}
новаяЦель();ждать=1.2;показатьПозу('privet');

function кадр(сейчас){
  if(!идёт)return;
  var dt=Math.min(.05,(сейчас-прежде)/1000);прежде=сейчас;
  if(режим==='за курсором'&&сейчас-курсорКогда>(касание?2600:2200)){режим='идёт';новаяЦель();ждать=.6}
  var tx,ty,скорость;
  if(режим==='за курсором'){
    /* встаём рядом с курсором, а не на нём: стрелка видна, робот «смотрит» на неё */
    var сбоку=курсорX>x+bw/2?-1:1;
    tx=курсорX-bw/2+сбоку*bw*.55;ty=курсорY-bh*.7;
    tx=Math.max(-bw*.2,Math.min(W-bw*.8,tx));ty=Math.max(-bh*.1,Math.min(H-bh*.9,ty));
    скорость=Math.max(W,600)*.9;
  }else{tx=цельX;ty=цельY;скорость=Math.max(70,Math.min(140,W*.09))}
  var dx=tx-x,dy=ty-y,d=Math.hypot(dx,dy);
  var нужноX=0,нужноY=0;
  if(режим==='идёт'&&ждать>0){
    ждать-=dt;if(ждать<=0)новаяЦель();
  }else if(d>4){
    var v=Math.min(скорость,d*(режим==='за курсором'?5:3));
    нужноX=dx/d*v;нужноY=dy/d*v;
  }else if(режим==='идёт'){
    ждать=1.4+Math.random()*1.6;
    показатьПозу(Math.random()<.6?'privet':'dumaet');
    if(Math.random()<.5)сказать();
  }
  var мягко=Math.min(1,dt*(режим==='за курсором'?7:4));
  vx+=(нужноX-vx)*мягко;vy+=(нужноY-vy)*мягко;
  x+=vx*dt;y+=vy*dt;
  var быстрота=Math.hypot(vx,vy);
  if(Math.abs(vx)>12)взгляд=vx>0?1:-1;
  if(быстрота>25){
    показатьПозу(быстрота>260?'raduetsya':'ukazyvaet');
    шаг+=dt*Math.min(16,4+быстрота/22);
  }else if(режим==='за курсором'&&d<=24){показатьПозу('privet')}
  /* походка: подскок на каждом шаге, лёгкое покачивание и наклон по ходу */
  var ход=Math.min(1,быстрота/80),подскок=-Math.abs(Math.sin(шаг))*(быстрота>260?22:9)*ход;
  var качка=Math.sin(шаг)*5*ход,наклон=Math.max(-12,Math.min(12,vx/45));
  var дышит=быстрота<25?Math.sin(сейчас/520)*1.6:0;
  бот.style.transform='translate3d('+x.toFixed(1)+'px,'+y.toFixed(1)+'px,0)';
  тело.style.transform='translateY('+(подскок+дышит).toFixed(1)+'px) rotate('+(качка+наклон).toFixed(2)+'deg) scaleX('+(поза==='ukazyvaet'?взгляд:1)+')';
  тень.style.transform='scale('+(1+подскок/60).toFixed(3)+')';
  тень.style.opacity=(1+подскок/50).toFixed(2);
  requestAnimationFrame(кадр);
}
function пуск(){if(идёт)return;идёт=true;прежде=performance.now();requestAnimationFrame(кадр)}
function стоп(){идёт=false}

function куда(e){var r=сцена.getBoundingClientRect();курсорX=e.clientX-r.left;курсорY=e.clientY-r.top;курсорКогда=performance.now();режим='за курсором'}
сцена.addEventListener('pointermove',function(e){if(e.pointerType==='mouse'||e.pointerType==='pen'){касание=false;куда(e)}});
/* на телефоне — по касанию; прокрутку не трогаем */
сцена.addEventListener('pointerdown',function(e){if(e.pointerType==='touch'){касание=true;куда(e)}},{passive:true});
сцена.addEventListener('pointerleave',function(e){if(e.pointerType==='mouse')курсорКогда=0});
addEventListener('resize',function(){мерить();x=Math.min(x,W-bw);y=Math.min(y,H-bh);новаяЦель()});

/* Не тратим батарею, когда первый экран прокручен или вкладка скрыта */
var виден=true;
if('IntersectionObserver' in window){new IntersectionObserver(function(es){виден=es[0].isIntersecting;виден&&!document.hidden?пуск():стоп()}).observe(сцена)}
document.addEventListener('visibilitychange',function(){document.hidden||!виден?стоп():пуск()});
пуск();
})();
