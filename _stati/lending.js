(function(){
/* Первый экран — пруд (09.10, по ролику-образцу от Ivan'а): огромная надпись лежит
   под водой, над ней плавает карп кои.
   • Вода: сетка высот поверхности, волны бегут и затухают (уравнение волны на сетке).
     Рыбка оставляет за собой след, нажатие пускает круги. Наклон поверхности
     преломляет надпись — буквы ломаются и сдвигаются, как сквозь воду.
   • Блики на дне: по буквам и рыбке бегут солнечные переливы, на гребнях волн — отблеск.
   • Рыбка: картинка сверху + «скелет» (_stati/ryba_podgotovka.py); сетку гнём,
     как позвоночник: волна от головы к хвосту, на повороте тело ложится дугой.
     Плавает сама, иногда замирает; есть курсор — кружит рядом; на телефоне касание
     зовёт к пальцу; нажатие по рыбке — рывок прочь.
   Всё рисует один WebGL-холст. Нет WebGL — видна обычная надпись из HTML, без рыбки.
   Надпись в HTML остаётся всегда: её читают поиск и экранный диктор, мы лишь прячем краску. */
var сцена=document.querySelector('.scena');
if(!сцена)return;
var холст=сцена.querySelector('.ryba'),надпись=сцена.querySelector('.giant');
if(!холст||!холст.dataset.src||!надпись)return;
var gl=холст.getContext('webgl',{alpha:true,premultipliedAlpha:true,antialias:true});
if(!gl){холст.style.display='none';return}
var меньшеДвижения=matchMedia('(prefers-reduced-motion: reduce)'),тихо=меньшеДвижения.matches;
var пауза=false,потерян=false,виден=true,номерКадра=0;
var кнопка=сцена.querySelector('[data-pond-pause]');
/* выше 1.75 разницы под водой не видно, а старые телефоны греются от каждого лишнего пикселя */
var плотность=Math.min(innerWidth<620?1.5:1.75,window.devicePixelRatio||1);

/* ---------- шейдеры ---------- */
function шейдер(тип,код){var s=gl.createShader(тип);gl.shaderSource(s,код);gl.compileShader(s);return s}
function программа(в,ф){var p=gl.createProgram();gl.attachShader(p,шейдер(gl.VERTEX_SHADER,в));gl.attachShader(p,шейдер(gl.FRAGMENT_SHADER,ф));gl.linkProgram(p);
  if(!gl.getProgramParameter(p,gl.LINK_STATUS))throw new Error('шейдер');return p}
/* блики на дне: три бегущие синусоиды под углом, слегка закрученные, — светлые жилки там,
   где они гасят друг друга. Своё, без чужих шейдеров */
var БЛИКИ='float blik(vec2 p,float t){vec2 q=p+vec2(sin(p.y*1.7+t*.6),cos(p.x*1.3-t*.5))*.35;'+
 'float a=sin(dot(q,vec2(1.,.35))*3.1+t*.9);float b=sin(dot(q,vec2(-.55,1.))*3.6-t*1.05);'+
 'float c=sin(dot(q,vec2(.45,-1.))*2.7+t*.75+a*.8);return pow(1.-abs((a+b+c)/3.),7.);}';
var прогВода,прогРыба;
try{
  прогВода=программа(
   'attribute vec2 p;varying vec2 v;void main(){v=vec2(p.x*.5+.5,.5-p.y*.5);gl_Position=vec4(p,0.,1.);}',
   'precision mediump float;uniform sampler2D txt;uniform sampler2D voda;uniform float t;uniform float rezhim;uniform vec2 vid;varying vec2 v;'+БЛИКИ+
   'void main(){vec2 g=(texture2D(voda,v).rg-.5)*2.;'+
   ' vec2 kol=vec2(sin(v.y*22.+t*1.6),cos(v.x*17.+t*1.3))*.0016;'+
   ' float bl=blik(v*vid*5.+g*1.5,t*.8);'+
   ' if(rezhim<.5){vec4 c=texture2D(txt,v+g*.04+kol);'+
   '  c.rgb=min(c.rgb*(.91+.3*bl),vec3(c.a));gl_FragColor=c;}'+
   ' else{float s=-(g.x*.6+g.y*.8);float svet=bl*.11+max(s,0.)*.6;'+
   '  gl_FragColor=vec4(vec3(.9,1.,.96)*svet,max(-s,0.)*.22);}}');
  прогРыба=программа(
   'attribute vec2 p;attribute vec2 uv;uniform vec2 res;uniform vec2 sdvig;varying vec2 v;'+
   'void main(){vec2 q=(p+sdvig)/res*2.-1.;gl_Position=vec4(q.x,-q.y,0.,1.);v=uv;}',
   /* тень — та же картинка, но прозрачность из уменьшенной копии текстуры: выходит размытой даром */
   'precision mediump float;uniform sampler2D tex;uniform float ten;varying vec2 v;'+
   'void main(){if(ten>.5){float a=texture2D(tex,v,3.).a*.34;gl_FragColor=vec4(.02,.16,.11,1.)*a;}else gl_FragColor=texture2D(tex,v);}');
}catch(e){холст.style.display='none';return}
gl.enable(gl.BLEND);gl.blendFunc(gl.ONE,gl.ONE_MINUS_SRC_ALPHA);

var буфЭкран=gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER,буфЭкран);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,1,1]),gl.STATIC_DRAW);
function текстура(){var т=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,т);
  gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
  /* пустая точка, пока не пришла настоящая картинка: иначе браузер ругается на пустую текстуру */
  gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,1,1,0,gl.RGBA,gl.UNSIGNED_BYTE,new Uint8Array(4));return т}
var тНадпись=текстура(),тВода=текстура(),тРыба=null;
gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL,true);

/* ---------- размеры ---------- */
var W=0,H=0,М=.4,надписьГотова=false,скелет=null;
function мерить(){
  if(потерян)return;
  var r=сцена.getBoundingClientRect();W=r.width;H=r.height;
  холст.width=Math.round(W*плотность);холст.height=Math.round(H*плотность);
  gl.viewport(0,0,холст.width,холст.height);
  /* крупная, как в образце: от носа до кончика хвоста — больше половины ширины */
  if(скелет)М=Math.max(260,Math.min(W*.58,H*1.1,760))/скелет.dlina;
  водаСетка();
  if(надписьГотова)нарисоватьНадпись();
}

/* ---------- надпись: каждую букву — туда же, где она стоит в HTML ---------- */
function нарисоватьНадпись(){
  if(потерян)return;
  var c=document.createElement('canvas');c.width=холст.width;c.height=холст.height;
  var x2=c.getContext('2d'),rs=сцена.getBoundingClientRect(),cs=getComputedStyle(надпись);
  var размер=parseFloat(cs.fontSize);
  x2.scale(плотность,плотность);
  x2.font='700 '+размер+'px "Golos Text", sans-serif';x2.textBaseline='alphabetic';
  x2.fillStyle='#FBFAF8';x2.shadowColor='rgba(6,40,28,.25)';x2.shadowBlur=30*плотность;x2.shadowOffsetY=10*плотность;
  var м=x2.measureText('ЙБ'),подъём=м.fontBoundingBoxAscent||размер*.92;
  var обход=document.createTreeWalker(надпись,NodeFilter.SHOW_TEXT),узел,диап=document.createRange();
  while((узел=обход.nextNode())){
    for(var i=0;i<узел.length;i++){
      var буква=узел.data[i];if(!буква.trim())continue;
      диап.setStart(узел,i);диап.setEnd(узел,i+1);
      var п=диап.getClientRects()[0];if(!п)continue;
      x2.fillText(буква.toLocaleUpperCase('ru'),п.left-rs.left,п.top-rs.top+подъём);
    }
  }
  gl.bindTexture(gl.TEXTURE_2D,тНадпись);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,c);
  // Прячем HTML только после готового кадра: загрузка и пауза не оставляют пустоту.
}

/* ---------- вода: сетка высот ---------- */
var GW=0,GH=0,А,Б,пиксели;
function водаСетка(){
  GW=Math.round(Math.max(96,Math.min(200,W/6)));GH=Math.max(48,Math.round(GW*H/Math.max(1,W)));
  А=new Float32Array(GW*GH);Б=new Float32Array(GW*GH);пиксели=new Uint8Array(GW*GH*4);
  for(var i=0;i<GW*GH;i++){пиксели[i*4]=128;пиксели[i*4+1]=128;пиксели[i*4+3]=255}
  gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL,false);
  gl.bindTexture(gl.TEXTURE_2D,тВода);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,GW,GH,0,gl.RGBA,gl.UNSIGNED_BYTE,пиксели);
  gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL,true);
}
function капля(px,py,радиус,сила){
  var cx=px/W*GW,cy=py/H*GH,r=Math.max(1,радиус/W*GW);
  for(var yy=Math.max(1,Math.floor(cy-r));yy<=Math.min(GH-2,Math.ceil(cy+r));yy++)
    for(var xx=Math.max(1,Math.floor(cx-r));xx<=Math.min(GW-2,Math.ceil(cx+r));xx++){
      var d=Math.hypot(xx-cx,yy-cy);if(d<r)А[yy*GW+xx]+=сила*(.5+.5*Math.cos(d/r*Math.PI));
    }
}
function водаШаг(){
  for(var yy=1;yy<GH-1;yy++)for(var xx=1,i=yy*GW+1;xx<GW-1;xx++,i++){
    Б[i]=((А[i-1]+А[i+1]+А[i-GW]+А[i+GW])*.5-Б[i])*.982;
  }
  var т=А;А=Б;Б=т;
}
function водаВТекстуру(){
  for(var yy=1;yy<GH-1;yy++)for(var xx=1,i=yy*GW+1;xx<GW-1;xx++,i++){
    var gx=(А[i+1]-А[i-1])*55,gy=(А[i+GW]-А[i-GW])*55,k=i*4;
    пиксели[k]=gx>127?255:gx<-128?0:128+gx;пиксели[k+1]=gy>127?255:gy<-128?0:128+gy;
  }
  gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL,false);
  gl.bindTexture(gl.TEXTURE_2D,тВода);gl.texSubImage2D(gl.TEXTURE_2D,0,0,0,GW,GH,gl.RGBA,gl.UNSIGNED_BYTE,пиксели);
  gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL,true);
}

/* ---------- рыбка: скелет и сетка ---------- */
var рис=null,готово=false,КОЛ=7;
var ПОЗ,УВ,точек,длины,покой,смещения,опора=12,индексов=0;
var буфP=gl.createBuffer(),буфUV=gl.createBuffer(),буфИ=gl.createBuffer();
function собрать(){
  var h=скелет.hrebet,n=h.length,i,j;точек=n;
  /* хребет в покое: длины звеньев и углы без скачков через ±π */
  длины=[];покой=[];var пред=null;
  for(i=0;i<n-1;i++){
    var dx=h[i+1][0]-h[i][0],dy=h[i+1][1]-h[i][1];длины.push(Math.hypot(dx,dy));
    var a=Math.atan2(dy,dx);if(пред!==null){while(a-пред>Math.PI)a-=2*Math.PI;while(a-пред<-Math.PI)a+=2*Math.PI}
    покой.push(a);пред=a;
  }
  /* поперёк: от левого края через хребет к правому; нормаль та же, что в ryba_podgotovka.py */
  смещения=[];УВ=new Float32Array(n*КОЛ*2);ПОЗ=new Float32Array(n*КОЛ*2);
  for(i=0;i<n;i++){
    var a0=h[Math.max(0,i-1)],b0=h[Math.min(n-1,i+1)],ddx=b0[0]-a0[0],ddy=b0[1]-a0[1],d=Math.hypot(ddx,ddy)||1;
    var nx=-ddy/d,ny=ddx/d,ряд=[];
    for(j=0;j<КОЛ;j++){
      var u=j/(КОЛ-1),с=u<.5?h[i][2]*(1-u*2):-h[i][3]*(u*2-1);
      ряд.push(с);УВ[(i*КОЛ+j)*2]=(h[i][0]+nx*с)/скелет.w;УВ[(i*КОЛ+j)*2+1]=(h[i][1]+ny*с)/скелет.h;
    }
    смещения.push(ряд);
  }
  var инд=[];
  for(i=0;i<n-1;i++)for(j=0;j<КОЛ-1;j++){var a1=i*КОЛ+j,b1=a1+1,c1=a1+КОЛ,d1=c1+1;инд.push(a1,c1,b1,b1,c1,d1)}
  индексов=инд.length;
  gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,буфИ);gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,new Uint16Array(инд),gl.STATIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER,буфUV);gl.bufferData(gl.ARRAY_BUFFER,УВ,gl.STATIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER,буфP);gl.bufferData(gl.ARRAY_BUFFER,ПОЗ,gl.DYNAMIC_DRAW);
  /* текстура 1024×1024: со степенью двойки работают уменьшенные копии — мелкая рыбка не рябит,
     а тень берёт размытую копию */
  var c=document.createElement('canvas');c.width=c.height=1024;c.getContext('2d').drawImage(рис,0,0,1024,1024);
  тРыба=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,тРыба);
  gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,c);gl.generateMipmap(gl.TEXTURE_2D);
  gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR_MIPMAP_LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
  готово=true;мерить();
}

/* ---------- поза: гнём хребет ---------- */
var РАСПРЯМИТЬ=.5;    // насколько распрямить свёрнутый на картинке хвост: 0 — как нарисован, 1 — в струнку
var x=0,y=0,vx=-330,vy=-20,курс=Math.PI,угВ=0,фаза=0,t=0,изгиб=0,нос=[0,0],хвост=[0,0];
function поза(скорость){
  var n=точек,звенья=n-1,общ=0,i;for(i=0;i<звенья;i++)общ+=длины[i];
  var размах=.2+Math.min(.18,скорость/2600);                 // радиан на кончике хвоста
  var кривизна=Math.max(-.0016,Math.min(.0016,изгиб));      // дуга по траектории, 1/px
  var px=0,py=0,s=0,углы=[],хр=[[0,0]];
  for(i=0;i<звенья;i++){
    var u=(s+длины[i]/2)/общ,гибк=Math.pow(Math.max(0,(u-.2)/.8),1.4);
    var фи=покой[0]+(покой[i]-покой[0])*(1-РАСПРЯМИТЬ*Math.min(1,u*2.2))
           +размах*гибк*Math.sin(фаза-u*5.6)-кривизна*(s+длины[i]/2)*М;
    углы.push(фи);px+=Math.cos(фи)*длины[i];py+=Math.sin(фи)*длины[i];хр.push([px,py]);s+=длины[i];
  }
  /* нос — по курсу; вращаем вокруг середины тела у грудных плавников, голова чуть водит в такт хвосту */
  var R=курс-(углы[0]+Math.PI)-Math.sin(фаза)*.035,cR=Math.cos(R)*М,sR=Math.sin(R)*М,ox=хр[опора][0],oy=хр[опора][1];
  for(i=0;i<n;i++){
    var т1=углы[Math.max(0,i-1)],т2=углы[Math.min(звенья-1,i)];
    var кс=Math.cos(т1)+Math.cos(т2),сн=Math.sin(т1)+Math.sin(т2),d=Math.hypot(кс,сн)||1,nx=-сн/d,ny=кс/d;
    for(var j=0;j<КОЛ;j++){
      var с=смещения[i][j],lx=хр[i][0]+nx*с-ox,ly=хр[i][1]+ny*с-oy,k=(i*КОЛ+j)*2;
      ПОЗ[k]=x+lx*cR-ly*sR;ПОЗ[k+1]=y+lx*sR+ly*cR;
    }
  }
  var сер=(КОЛ-1)/2*2;нос=[ПОЗ[сер],ПОЗ[сер+1]];var кх=((n-8)*КОЛ)*2+сер;хвост=[ПОЗ[кх],ПОЗ[кх+1]];
}

/* ---------- кадр ---------- */
var лВода={},лРыба={};
['txt','voda','t','rezhim','vid'].forEach(function(k){лВода[k]=gl.getUniformLocation(прогВода,k)});
['res','sdvig','ten','tex'].forEach(function(k){лРыба[k]=gl.getUniformLocation(прогРыба,k)});
var лЭкран=gl.getAttribLocation(прогВода,'p'),лP=gl.getAttribLocation(прогРыба,'p'),лUV=gl.getAttribLocation(прогРыба,'uv');
function вода(режим){
  gl.useProgram(прогВода);
  gl.bindBuffer(gl.ARRAY_BUFFER,буфЭкран);gl.enableVertexAttribArray(лЭкран);gl.vertexAttribPointer(лЭкран,2,gl.FLOAT,false,0,0);
  gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,тНадпись);gl.uniform1i(лВода.txt,0);
  gl.activeTexture(gl.TEXTURE1);gl.bindTexture(gl.TEXTURE_2D,тВода);gl.uniform1i(лВода.voda,1);
  gl.uniform1f(лВода.t,t);gl.uniform1f(лВода.rezhim,режим);gl.uniform2f(лВода.vid,W/Math.max(1,H),1);
  gl.drawArrays(gl.TRIANGLE_STRIP,0,4);gl.activeTexture(gl.TEXTURE0);
}
function нарисовать(скорость){
  if(потерян)return;
  gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT);
  if(надписьГотова)вода(0);                       // надпись под водой
  if(готово){                                     // тень и рыбка
    поза(скорость);
    gl.useProgram(прогРыба);
    gl.bindBuffer(gl.ARRAY_BUFFER,буфP);gl.bufferSubData(gl.ARRAY_BUFFER,0,ПОЗ);
    gl.enableVertexAttribArray(лP);gl.vertexAttribPointer(лP,2,gl.FLOAT,false,0,0);
    gl.bindBuffer(gl.ARRAY_BUFFER,буфUV);gl.enableVertexAttribArray(лUV);gl.vertexAttribPointer(лUV,2,gl.FLOAT,false,0,0);
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,буфИ);gl.bindTexture(gl.TEXTURE_2D,тРыба);gl.uniform1i(лРыба.tex,0);
    gl.uniform2f(лРыба.res,W,H);
    gl.uniform1f(лРыба.ten,1);gl.uniform2f(лРыба.sdvig,W*.012+8,H*.02+12);gl.drawElements(gl.TRIANGLES,индексов,gl.UNSIGNED_SHORT,0);
    gl.uniform1f(лРыба.ten,0);gl.uniform2f(лРыба.sdvig,0,0);gl.drawElements(gl.TRIANGLES,индексов,gl.UNSIGNED_SHORT,0);
    gl.disableVertexAttribArray(лUV);
  }
  вода(1);                                        // блики и отблески волн поверх всего
  if(надписьГотова)сцена.classList.add('voda');
}

/* ---------- движение ---------- */
var курсорX=0,курсорY=0,курсорКогда=-1e9,касание=false,орбита=0,замер=0,замерЧерез=7+Math.random()*3,рывок=0;
var ф=[Math.random()*6,Math.random()*6,Math.random()*6,Math.random()*6];
function кратчайший(a){while(a>Math.PI)a-=2*Math.PI;while(a<-Math.PI)a+=2*Math.PI;return a}
function путь(t){var ax=W*.42,ay=H*.36;
  return [W*.5+ax*(.6*Math.sin(t*.17+ф[0])+.4*Math.sin(t*.41+ф[1])),H*.5+ay*(.55*Math.sin(t*.25+ф[2])+.4*Math.sin(t*.53+ф[3]))]}
var прежде=performance.now(),идёт=false,копилка=0;
function кадр(сейчас){
  номерКадра=0;
  if(!идёт)return;
  // На экране 120 Гц пруду достаточно 60 кадров: вдвое меньше работы для GPU.
  if(сейчас-прежде<1000/60-.75){номерКадра=requestAnimationFrame(кадр);return}
  var dt=Math.min(.04,(сейчас-прежде)/1000);прежде=сейчас;t+=dt;
  var курсор=сейчас-курсорКогда<(касание?2600:3500),tx,ty,макс,тяга;
  if(курсор){орбита+=dt*1.15;var Rr=Math.min(W,H)*.16+60;tx=курсорX+Math.cos(орбита)*Rr;ty=курсорY+Math.sin(орбита)*Rr*.7;макс=Math.max(520,W*.6);тяга=4}
  else{var p=путь(t*.85);tx=p[0];ty=p[1];макс=Math.max(120,Math.min(200,W*.15));тяга=1.8;
    замерЧерез-=dt;if(замерЧерез<=0&&замер<=0&&x>W*.2&&x<W*.8&&y>H*.2&&y<H*.8){замер=2.8;замерЧерез=10+Math.random()*6}}
  if(замер>0&&!курсор){замер-=dt;tx=x+Math.cos(курс)*4;ty=y+Math.sin(курс)*4}
  if(рывок>0){рывок-=dt;vx*=1-dt*1.1;vy*=1-dt*1.1}
  else{var dx=tx-x,dy=ty-y,d=Math.hypot(dx,dy)||1,хочет=Math.min(макс,d*тяга),m=Math.min(1,dt*(курсор?3:1.9));vx+=(dx/d*хочет-vx)*m;vy+=(dy/d*хочет-vy)*m}
  x+=vx*dt;y+=vy*dt;
  var скорость=Math.hypot(vx,vy);
  /* нос — по ходу; сверху рыбка правильна при любом повороте, переворачивать не нужно */
  if(скорость>15){var нов=курс+кратчайший(Math.atan2(vy,vx)-курс)*Math.min(1,dt*(курсор||рывок>0?4.5:2.6));угВ=кратчайший(нов-курс)/Math.max(dt,.001);курс=кратчайший(нов)}else угВ*=.9;
  изгиб+=((скорость>40?угВ/скорость:0)-изгиб)*Math.min(1,dt*5);   // тело дугой по траектории
  фаза+=dt*Math.min(16,2.4+скорость/30);                            // быстрее плывёт — чаще бьёт хвостом
  /* след на воде: у носа — бурун, у хвоста — толчки в такт; вода шагает 60 раз в секунду при любой частоте экрана */
  if(готово){капля(нос[0],нос[1],16,-.45*Math.min(1.4,скорость/220));капля(хвост[0],хвост[1],20,.55*Math.sin(фаза)*Math.min(1.2,.3+скорость/300))}
  копилка+=dt;var шагов=0;while(копилка>1/60&&шагов<3){водаШаг();копилка-=1/60;шагов++}
  водаВТекстуру();
  нарисовать(скорость);
  номерКадра=requestAnimationFrame(кадр);
}
function пуск(){if(идёт||тихо||пауза||потерян||document.hidden||!виден)return;идёт=true;прежде=performance.now();номерКадра=requestAnimationFrame(кадр)}
function стоп(){идёт=false;cancelAnimationFrame(номерКадра);номерКадра=0}
function состояние(){
  if(кнопка){кнопка.hidden=потерян;кнопка.disabled=тихо;кнопка.textContent=тихо?'Пруд без движения':пауза?'Оживить пруд':'Остановить пруд';кнопка.setAttribute('aria-pressed',String(пауза||тихо))}
}
if(кнопка){кнопка.hidden=false;кнопка.addEventListener('click',function(){пауза=!пауза;состояние();пауза?стоп():пуск()})}
function движениеИзменилось(e){тихо=e.matches;состояние();if(тихо){стоп();x=W*.68;y=H*.4;нарисовать(0)}else пуск()}
if(меньшеДвижения.addEventListener)меньшеДвижения.addEventListener('change',движениеИзменилось);
else меньшеДвижения.addListener(движениеИзменилось);
// При потере GPU (память/свёрнутое приложение) сразу возвращается обычный заголовок.
// Не перехватываем восстановление контекста: возвращаемся к надёжной статичной странице.
холст.addEventListener('webglcontextlost',function(){потерян=true;стоп();сцена.classList.remove('voda');холст.style.display='none';состояние()});
состояние();

function куда(e){var r=сцена.getBoundingClientRect();курсорX=e.clientX-r.left;курсорY=e.clientY-r.top;курсорКогда=performance.now()}
сцена.addEventListener('pointermove',function(e){if(e.pointerType==='mouse'||e.pointerType==='pen'){касание=false;куда(e)}});
сцена.addEventListener('pointerdown',function(e){
  if(тихо||пауза||потерян||e.target.closest('a,button'))return;
  var r=сцена.getBoundingClientRect(),px=e.clientX-r.left,py=e.clientY-r.top;
  капля(px,py,26,3.2);                            // круги по воде от нажатия
  /* нажали по рыбке — пугается и уходит рывком */
  if(готово&&Math.hypot(px-x,py-y)<Math.max(70,240*М)){var a=Math.atan2(y-py,x-px)+(Math.random()-.5)*.8;vx=Math.cos(a)*880;vy=Math.sin(a)*880;рывок=.9;курсорКогда=-1e9;return}
  if(e.pointerType==='touch'){касание=true;куда(e)}
},{passive:true});
сцена.addEventListener('pointerleave',function(e){if(e.pointerType==='mouse')курсорКогда=-1e9});
addEventListener('resize',function(){мерить();if(тихо){x=W*.68;y=H*.4}if(!идёт)нарисовать(0)});

мерить();
x=W+180;y=H*.45;                                  // вплывает из-за правого края
if(тихо){x=W*.68;y=H*.4;курс=-.35}               // без движения: пруд и рыбка замерли
/* скелет, картинка и шрифт грузятся вместе; что-то не пришло — без рыбки, надпись на месте */
var ждём=2;
function пришло(){if(--ждём===0&&!потерян)try{собрать();if(!идёт)нарисовать(0)}catch(e){}}
fetch(холст.dataset.src.replace(/\.webp$/,'.json')).then(function(r){return r.json()}).then(function(j){скелет=j;пришло()}).catch(function(){});
рис=new Image();рис.onload=пришло;рис.src=холст.dataset.src;
(document.fonts&&document.fonts.ready?document.fonts.ready:Promise.resolve()).then(function(){
  надписьГотова=true;нарисоватьНадпись();if(!идёт)нарисовать(0);
});
/* Не тратим батарею, когда первый экран прокручен или вкладка скрыта */
if('IntersectionObserver' in window){new IntersectionObserver(function(es){виден=es[0].isIntersecting;виден&&!document.hidden?пуск():стоп()}).observe(сцена)}
document.addEventListener('visibilitychange',function(){document.hidden||!виден?стоп():пуск()});
addEventListener('pagehide',стоп);
addEventListener('pageshow',function(){if(!потерян){мерить();нарисовать(0);пуск()}});
пуск();
})();
