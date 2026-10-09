(function(){
/* Копирование запроса. В вебвью буфер обмена бывает закрыт — тогда выделяем текст,
   чтобы человек скопировал сам, а не остался с пустыми руками. */
document.addEventListener('click',function(e){
  var b=e.target.closest('[data-copy]');if(!b)return;
  var pre=b.closest('figure').querySelector('pre');
  var готово=function(){b.textContent='Скопировано';setTimeout(function(){b.textContent='Копировать'},1800)};
  var выделить=function(){var r=document.createRange();r.selectNodeContents(pre);var s=getSelection();s.removeAllRanges();s.addRange(r);b.textContent='Выделено — скопируй'};
  (navigator.clipboard?navigator.clipboard.writeText(pre.textContent):Promise.reject()).then(готово,выделить);
});

/* Черта под шапкой и полоска дочитывания — одним кадром на прокрутку. */
var шапка=document.querySelector('.site'),полоска=document.querySelector('.prog i'),ждём=0;
function кадр(){
  ждём=0;var y=window.scrollY||0;
  if(шапка)шапка.classList.toggle('scrolled',y>4);
  if(полоска){var м=document.documentElement.scrollHeight-innerHeight;полоска.style.transform='scaleX('+(м>0?Math.min(1,y/м):0)+')'}
}
addEventListener('scroll',function(){if(!ждём)ждём=requestAnimationFrame(кадр)},{passive:true});кадр();

/* Оглавление сбоку подсвечивает раздел, который сейчас читают. */
var пункты=[].slice.call(document.querySelectorAll('.toc a'));
if(пункты.length&&'IntersectionObserver' in window){
  var по={};пункты.forEach(function(a){по[a.hash.slice(1)]=a});
  var io=new IntersectionObserver(function(es){es.forEach(function(en){
    if(en.isIntersecting&&по[en.target.id]){пункты.forEach(function(a){a.classList.remove('on')});по[en.target.id].classList.add('on')}
  })},{rootMargin:'-80px 0px -70% 0px'});
  Object.keys(по).forEach(function(id){var el=document.getElementById(id);if(el)io.observe(el)});
}
/* Мобильное оглавление закрывается после выбора пункта — иначе оно закрывает текст. */
document.addEventListener('click',function(e){var a=e.target.closest('.toc-m a');if(a)a.closest('details').open=false});

/* Рубрики на главной раздела. Без скрипта видны все статьи — фильтр только сужает. */
var кнопки=[].slice.call(document.querySelectorAll('.filters .f'));
if(кнопки.length){
  var карточки=[].slice.call(document.querySelectorAll('#spisok .card'));
  var выбрать=function(f){
    кнопки.forEach(function(b){b.setAttribute('aria-pressed',String(b.dataset.f===f))});
    карточки.forEach(function(c){c.hidden=!!f&&c.dataset.r!==f});
  };
  кнопки.forEach(function(b){b.addEventListener('click',function(){выбрать(b.dataset.f)})});
  /* Хлебные крошки статьи ведут на #r-<рубрика>: сразу показываем эту рубрику. */
  var поЯкорю=function(){
    var m=/^#r-([a-z]+)$/.exec(location.hash);
    if(m&&кнопки.some(function(b){return b.dataset.f===m[1]})){выбрать(m[1]);var v=document.getElementById('vse');if(v)v.scrollIntoView()}
  };
  поЯкорю();addEventListener('hashchange',поЯкорю);
}
})();
