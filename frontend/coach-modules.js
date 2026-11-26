(function(){
  if(window.__ivmeModLoaded) return;
  window.__ivmeModLoaded = true;
  const K='ivme_coach_modules_v1', TODAY=new Date().toISOString().slice(0,10);
  const GROUPS=['LGS','6. Sınıf','7. Sınıf','8. Sınıf','9. Sınıf','10. Sınıf','11. Sınıf','12. Sınıf','YKS (TYT/AYT)','KPSS Lisans','KPSS Ön Lisans','KPSS Orta Öğ.','ALES','DGS','YDS','TUS'];
  const CURR={
    YKS:[{s:'TYT Türkçe',t:['Sözcükte Anlam','Paragraf','Ses Bilgisi','Yazım Kuralları','Dil Bilgisi']},{s:'TYT Matematik',t:['Temel Kavramlar','Sayılar','Problemler','Fonksiyonlar','Olasılık']},{s:'AYT Kimya',t:['Modern Atom','Gazlar','Asit-Baz Dengesi','Organik Kimya']}],
    LGS:[{s:'LGS Matematik',t:['Çarpanlar ve Katlar','Üslü İfadeler','Kareköklü İfadeler','Veri Analizi']},{s:'LGS Fen',t:['Mevsimler','DNA ve Genetik','Basınç']}],
    KPSS:[{s:'Genel Yetenek',t:['Sayısal Mantık','Sözel Mantık','Problemler']},{s:'Genel Kültür',t:['İnkılap Tarihi','Coğrafya','Vatandaşlık']}]
  };
  const NEWS=[
    {tag:'İyileştirme',date:'25 Eyl 2026',title:'Deneme Analitiği artık öğrenci bazlı',desc:'Öğrenci seçip net grafiğini ve ders bazlı kırılımı tek tıkla görebilirsin.'},
    {tag:'Yeni',date:'25 Eyl 2026',title:'Kaynak Kütüphanem & Kitap Kapakları',desc:'16 sınıf/sınav grubunda kaynakları bir kez ekle, öğrencilere tek tıkla aktar.'},
    {tag:'Yeni',date:'23 Eyl 2026',title:'Fotoğraftan Optik Okuma (2 Adımlı Izgara)',desc:'Cevap anahtarı ve optik form fotoğrafını yükle, ızgarada düzeltip öğrenciye yaz.'},
    {tag:'Yeni',date:'21 Eyl 2026',title:'Haftalık Raporlar Onay Akışı',desc:'Taslakları Bekleyen, Onaylı ve Gönderilen aşamalarında yönet.'},
    {tag:'İyileştirme',date:'18 Eyl 2026',title:'Ödeme Takibi 4 Seanslık Kartlar',desc:'Seans Kullan, +4 Seans Ekle, +Telafi ve Manuel Seans işlemleri tek kartta.'},
    {tag:'İyileştirme',date:'15 Eyl 2026',title:'Genel Raporlar Karşılaştırma & Admin Notu',desc:'İki denemeyi yan yana kıyasla ve öğrenciye özel koç/admin notu kaydet.'}
  ];
  function def(){
    return {
      coach:{name:'Haluk Can Sarıöz',email:'halukcansarioz19@gmail.com'},
      students:[
        {id:'ms-1',name:'Demo Öğrenci (silebilirsin)',exam:'YKS',track:'Sayısal',risk:'Düzenli',archived:false,rem:3,tot:4,note:'Paragraf hızı artıyor.',topics:{'TYT Türkçe::Paragraf':'done','TYT Matematik::Sayılar':'progress'}},
        {id:'ms-2',name:'Elif Demir',exam:'YKS',track:'Eşit Ağırlık',risk:'Orta Riskli',archived:false,rem:2,tot:4,note:'Branş denemesi eklenecek.',topics:{'TYT Türkçe::Paragraf':'done'}},
        {id:'ms-3',name:'Kerem Yılmaz',exam:'LGS',track:'8. Sınıf',risk:'Riskli',archived:false,rem:0,tot:4,note:'Veli ile seans yenileme görüşmesi.',topics:{}}
      ],
      meetings:[{id:'mt-1',sid:'ms-1',date:TODAY,time:'16:00',title:'Haftalık Net Değerlendirmesi',done:false},{id:'mt-2',sid:'ms-2',date:TODAY,time:'18:30',title:'Problemler Hız Stratejisi',done:false}],
      goals:[{id:'gl-1',sid:'ms-1',subj:'TYT Matematik',title:'32+ Net Hedefi',cur:26,tgt:32,unit:'net',done:false},{id:'gl-2',sid:'ms-1',subj:'TYT Türkçe',title:'Haftalık 250 Paragraf',cur:180,tgt:250,unit:'soru',done:false}],
      books:[{id:'bk-1',sid:'ms-1',title:'3D Yayınları TYT Matematik',subj:'TYT Matematik',prog:45},{id:'bk-2',sid:'ms-1',title:'Bilgi Sarmal Paragraf',subj:'TYT Türkçe',prog:70}],
      library:[{id:'lb-1',grp:'YKS (TYT/AYT)',title:'3D Yayınları TYT Matematik',subj:'TYT Matematik',pages:320},{id:'lb-2',grp:'YKS (TYT/AYT)',title:'Bilgi Sarmal Paragraf',subj:'TYT Türkçe',pages:248},{id:'lb-3',grp:'8. Sınıf',title:'Okyanus Master LGS Matematik',subj:'LGS Matematik',pages:256},{id:'lb-4',grp:'KPSS Lisans',title:'Pegem Genel Yetenek',subj:'Genel Yetenek',pages:410}],
      exams:[{id:'ex-1',sid:'ms-1',kind:'general',name:'Özdebir TYT-1',date:'2026-10-18',net:74.5},{id:'ex-2',sid:'ms-1',kind:'general',name:'3D Türkiye Geneli',date:'2026-11-15',net:84.75},{id:'ex-3',sid:'ms-1',kind:'general',name:'İvme Kurumsal TYT-4',date:TODAY,net:88.5},{id:'ex-4',sid:'ms-1',kind:'branch',name:'3D Matematik Branş #6',date:TODAY,net:29.25}],
      weeklyReports:[{id:'wr-1',sid:'ms-1',week:'Bu Hafta',status:'pending',text:'Görev uyumu %75, son deneme 88.5 net (+3.75 artış).'},{id:'wr-2',sid:'ms-2',week:'Geçen Hafta',status:'sent',text:'180 soru tamamlandı, veli e-postası gönderildi.'}],
      dailyNotes:{}, optKey:false, optPhoto:'',
      optGrid:[{q:1,k:'A',m:'A'},{q:2,k:'C',m:'C'},{q:3,k:'B',m:'D'},{q:4,k:'E',m:'E'},{q:5,k:'D',m:'D'},{q:6,k:'B',m:''},{q:7,k:'A',m:'A'},{q:8,k:'C',m:'B'},{q:9,k:'E',m:'E'},{q:10,k:'D',m:'D'}],
      ui:{mod:null,stu:'ms-1',risk:'Tümü',stuTab:'active',goalTab:'active',libGrp:'YKS (TYT/AYT)',repTab:'general',wrTab:'pending',payF:'all',payQ:'',stuQ:'',cmpA:'ex-1',cmpB:'ex-3',pomoSec:1500,pomoRun:false,pomoMin:50}
    };
  }
  let S=def(), pInt=null;
  try{const r=localStorage.getItem(K); if(r) S=Object.assign(def(),JSON.parse(r));}catch(e){}
  const save=()=>{try{localStorage.setItem(K,JSON.stringify(S));}catch(e){}};
  const esc=v=>String(v==null?'':v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const stu=id=>S.students.find(x=>x.id===id)||S.students[0];
  function tPct(st){const a=CURR[st.exam]||CURR.YKS;let t=0,d=0;a.forEach(g=>g.t.forEach(tp=>{t++;const v=(st.topics||{})[g.s+'::'+tp];if(v==='done')d+=1;else if(v==='progress')d+=0.4;}));return t?Math.round(d/t*100):0;}
  function toast(msg){if(typeof window.showToast==='function'){window.showToast(msg);return;}let t=document.getElementById('ivme-mod-toast');if(!t){t=document.createElement('div');t.id='ivme-mod-toast';t.style.cssText='position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:#0f172a;color:#fff;padding:10px 18px;border-radius:12px;font-size:13px;z-index:9999;';document.body.appendChild(t);}t.textContent=msg;t.style.display='block';clearTimeout(t._tm);t._tm=setTimeout(()=>t.style.display='none',2200);}
  function addCss(){
    if(document.getElementById('ivme-mod-css')) return;
    const s=document.createElement('style'); s.id='ivme-mod-css';
    s.textContent='.im-gt{font-size:11px;font-weight:700;text-transform:uppercase;color:#64748b;padding:10px 12px 4px;display:flex;justify-content:space-between;cursor:pointer}.im-nb{width:100%;display:flex;align-items:center;justify-content:space-between;gap:8px;padding:8px 12px;border-radius:10px;border:none;background:transparent;color:inherit;font-size:13px;font-weight:500;cursor:pointer;text-align:left}.im-nb:hover{background:rgba(79,70,229,.08)}.im-nb.on{background:#4f46e5;color:#fff;font-weight:600}.im-bdg{font-size:10px;font-weight:700;padding:1px 6px;border-radius:999px;background:#4f46e5;color:#fff}#ivme-mod-host{display:none;max-width:1280px;margin:0 auto;padding:16px}#ivme-mod-host.show{display:block}.im-c{background:var(--card,#fff);border:1px solid var(--border,#e2e8f0);border-radius:16px;padding:16px;margin-bottom:12px}.im-g{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(240px,1fr))}.im-g4{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(160px,1fr))}.im-b{padding:8px 14px;border-radius:10px;border:1px solid var(--border,#cbd5e1);background:var(--card,#fff);color:inherit;font-size:12px;font-weight:600;cursor:pointer}.im-bp{background:#4f46e5;color:#fff;border-color:#4f46e5}.im-bg{background:#059669;color:#fff;border-color:#059669}.im-ba{background:#f59e0b;color:#fff;border-color:#f59e0b}.im-br{background:#e11d48;color:#fff;border-color:#e11d48}.im-p{padding:6px 12px;border-radius:999px;border:1px solid var(--border,#cbd5e1);background:transparent;color:inherit;font-size:12px;font-weight:600;cursor:pointer;white-space:nowrap}.im-p.on{background:#4f46e5;color:#fff;border-color:#4f46e5}.im-i{width:100%;padding:8px 12px;border-radius:10px;border:1px solid var(--border,#cbd5e1);background:transparent;color:inherit;font-size:13px}.im-bar{height:8px;border-radius:999px;background:rgba(148,163,184,.25);overflow:hidden}.im-bar>div{height:100%;background:#4f46e5}.im-fl{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:10px}.im-seg{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin:8px 0 12px}.im-seg>div{height:8px;border-radius:999px;background:rgba(148,163,184,.25)}.im-seg>div.on{background:#10b981}.im-sc{display:flex;gap:6px;overflow-x:auto;padding-bottom:6px}.im-m{font-size:12px;color:#64748b}.im-h{font-size:20px;font-weight:800;margin:0}body.student-mode #ivme-mod-nav-wrap,body.parent-mode #ivme-mod-nav-wrap{display:none!important}';
    document.head.appendChild(s);
  }
  function hide(){S.ui.mod=null;const h=document.getElementById('ivme-mod-host');if(h)h.classList.remove('show');document.querySelectorAll('.im-nb').forEach(b=>b.classList.remove('on'));}
  function open(m){
    S.ui.mod=m;
    document.querySelectorAll('.tab-content,[id^="tab-"]').forEach(el=>{if(el.id&&/^tab-(home|\d+)$/.test(el.id))el.style.display='none';});
    const h=document.getElementById('ivme-mod-host'); if(h) h.classList.add('show');
    document.querySelectorAll('.im-nb').forEach(b=>b.classList.toggle('on',b.dataset.im===m));
    render(); window.scrollTo({top:0,behavior:'smooth'});
  }
  function render(){
    const h=document.getElementById('ivme-mod-host'); if(!h||!S.ui.mod) return;
    const m=S.ui.mod, act=S.students.filter(s=>!s.archived), cs=stu(S.ui.stu);
    let o='';
    if(m==='daily'){
      const mm=String(Math.floor(S.ui.pomoSec/60)).padStart(2,'0'), ss=String(S.ui.pomoSec%60).padStart(2,'0'), ns=S.dailyNotes[TODAY]||[];
      o=`<div class="im-fl" style="margin-bottom:12px"><div><h1 class="im-h">Günlük Program</h1><div class="im-m">${TODAY} · Bugün</div></div><button class="im-b im-bp" onclick="window.print()">PDF</button></div>
      <div class="im-g"><div class="im-c" style="border-color:#f59e0b"><div class="im-m"><b>POMODORO</b></div><div style="font-size:20px;font-weight:800;margin:6px 0">${S.ui.pomoMin} dk · <span id="im-pc">${mm}:${ss}</span></div><button id="im-pb" class="im-b im-ba">${S.ui.pomoRun?'Duraklat':'Başlat'}</button></div>
      <div class="im-c" style="border-color:#10b981"><div class="im-m"><b>ÖĞRENCİ</b></div><div style="font-weight:800;margin:6px 0">${esc(cs.name)}</div><div class="im-m">Konu İlerlemesi: %${tPct(cs)}</div></div>
      <div class="im-c" style="border-color:#4f46e5"><div class="im-m"><b>KOÇ NOTU (${ns.length})</b></div><div style="display:flex;gap:6px;margin-top:8px"><input id="im-dn" class="im-i" placeholder="Not ekle..."/><button id="im-da" class="im-b im-bp">Ekle</button></div></div></div>
      <div class="im-c"><b>Günün Notları</b>${ns.map(n=>`<div style="margin-top:6px;font-size:13px">• ${esc(n)}</div>`).join('')||'<div class="im-m" style="margin-top:6px">Not yok.</div>'}</div>`;
    } else if(m==='meetings'){
      const tm=S.meetings.filter(x=>x.date===TODAY), dm=S.meetings.filter(x=>x.done).length;
      o=`<h1 class="im-h" style="margin-bottom:12px">Görüşmeler</h1>
      <div class="im-g4"><div class="im-c"><div class="im-m">BUGÜN</div><b style="font-size:22px;color:#4f46e5">${tm.length}</b></div><div class="im-c"><div class="im-m">TAMAMLANAN</div><b style="font-size:22px;color:#059669">${dm}</b></div><div class="im-c"><div class="im-m">TOPLAM</div><b style="font-size:22px">${S.meetings.length}</b></div></div>
      <div class="im-c im-g"><select id="im-ms" class="im-i">${act.map(s=>`<option value="${s.id}">${esc(s.name)}</option>`).join('')}</select><input id="im-mt" type="time" value="17:00" class="im-i"/><input id="im-ml" value="Haftalık Değerlendirme" class="im-i"/><button id="im-ma" class="im-b im-bp">+ Görüşme Ekle</button></div>
      <div class="im-c">${S.meetings.map(mt=>`<div class="im-fl" style="padding:8px 0;border-bottom:1px solid var(--border,#e2e8f0)"><div><b>${esc(stu(mt.sid).name)}</b> · ${mt.date} ${mt.time}<div class="im-m">${esc(mt.title)}</div></div><div style="display:flex;gap:6px"><button data-mtog="${mt.id}" class="im-b ${mt.done?'im-bg':'im-bp'}">${mt.done?'Tamamlandı ✓':'Tamamla'}</button><button data-mdel="${mt.id}" class="im-b im-br">Sil</button></div></div>`).join('')}</div>`;
    } else if(m==='students'){
      const l=S.students.filter(s=>(S.ui.stuTab==='active'?!s.archived:s.archived)&&(S.ui.risk==='Tümü'||s.risk===S.ui.risk)&&(!S.ui.stuQ||s.name.toLowerCase().includes(S.ui.stuQ.toLowerCase())));
      o=`<div class="im-fl" style="margin-bottom:12px"><div><h1 class="im-h">Öğrenciler</h1><div class="im-m">${act.length} aktif öğrenci</div></div><div style="display:flex;gap:6px"><button data-st="active" class="im-p ${S.ui.stuTab==='active'?'on':''}">Aktif</button><button data-st="archived" class="im-p ${S.ui.stuTab==='archived'?'on':''}">Arşiv</button></div></div>
      <div class="im-c im-fl"><input id="im-sq" value="${esc(S.ui.stuQ)}" placeholder="Öğrenci ara..." class="im-i" style="max-width:260px"/><div style="display:flex;gap:6px;flex-wrap:wrap">${['Tümü','Riskli','Orta Riskli','Düzenli'].map(r=>`<button data-rf="${r}" class="im-p ${S.ui.risk===r?'on':''}">${r}</button>`).join('')}</div></div>
      <div class="im-g">${l.map(s=>{const p=tPct(s);return `<div class="im-c"><div class="im-fl"><div><b>${esc(s.name)}</b><div class="im-m">${s.exam} · ${s.track}</div></div><span class="im-bdg" style="background:${s.risk==='Riskli'?'#e11d48':s.risk==='Orta Riskli'?'#f59e0b':'#059669'}">${s.risk}</span></div><div style="margin:10px 0"><div class="im-fl" style="font-size:12px"><span>Konu İlerlemesi</span><b>%${p}</b></div><div class="im-bar"><div style="width:${p}%"></div></div><div class="im-m" style="margin-top:6px">Kalan seans: <b>${s.rem}/${s.tot}</b></div></div><div style="display:flex;gap:6px;flex-wrap:wrap"><button data-go="topics:${s.id}" class="im-b">Konular</button><button data-go="goals:${s.id}" class="im-b">Hedefler</button><button data-go="reports:${s.id}" class="im-b">Rapor</button><button data-ar="${s.id}" class="im-b im-ba">${s.archived?'Geri Al':'Arşivle'}</button></div></div>`;}).join('')}</div>`;
    } else if(m==='topics'){
      const tr=CURR[cs.exam]||CURR.YKS;
      o=`<div class="im-fl" style="margin-bottom:12px"><div><h1 class="im-h">Konu Takibi</h1><div class="im-m">Konuya tıkla: Başlanmadı → Devam → Tamamlandı</div></div><select id="im-ts" class="im-i" style="max-width:260px">${act.map(s=>`<option value="${s.id}" ${s.id===cs.id?'selected':''}>${esc(s.name)} (%${tPct(s)})</option>`).join('')}</select></div>`+tr.map(g=>`<div class="im-c"><b style="color:#4f46e5">${esc(g.s)}</b><div class="im-g" style="margin-top:8px">${g.t.map(tp=>{const k=g.s+'::'+tp,v=(cs.topics||{})[k]||'none';return `<button data-tp="${esc(k)}" class="im-b" style="text-align:left;${v==='done'?'border-color:#10b981;background:rgba(16,185,129,.12)':v==='progress'?'border-color:#f59e0b;background:rgba(245,158,11,.12)':''}">${esc(tp)} — <b>${v==='done'?'Tamamlandı ✓':v==='progress'?'Devam':'Başlanmadı'}</b></button>`;}).join('')}</div></div>`).join('');
    } else if(m==='goals'){
      const gs=S.goals.filter(g=>g.sid===cs.id&&(S.ui.goalTab==='active'?!g.done:g.done));
      o=`<div class="im-fl" style="margin-bottom:12px"><h1 class="im-h">Hedefler</h1><select id="im-gs" class="im-i" style="max-width:250px">${act.map(s=>`<option value="${s.id}" ${s.id===cs.id?'selected':''}>${esc(s.name)}</option>`).join('')}</select></div>
      <div class="im-c im-g"><input id="im-gsu" value="TYT Matematik" class="im-i"/><input id="im-gtl" placeholder="Hedef başlığı" class="im-i"/><input id="im-gtg" type="number" value="30" class="im-i"/><button id="im-gad" class="im-b im-bp">+ Yeni Hedef</button></div>
      <div style="display:flex;gap:8px;margin-bottom:12px"><button data-gt="active" class="im-p ${S.ui.goalTab==='active'?'on':''}">Aktif</button><button data-gt="past" class="im-p ${S.ui.goalTab==='past'?'on':''}">Geçmiş</button></div>
      <div class="im-g">${gs.map(g=>{const p=g.tgt?Math.min(100,Math.round(g.cur/g.tgt*100)):0;return `<div class="im-c"><div class="im-m">${esc(g.subj)}</div><b>${esc(g.title)}</b><div class="im-m" style="margin:4px 0">${g.cur}/${g.tgt} ${g.unit} (%${p})</div><div class="im-bar" style="margin-bottom:8px"><div style="width:${p}%"></div></div><button data-gi="${g.id}" class="im-b">+ İlerlet</button> <button data-gd="${g.id}" class="im-b im-bg">${g.done?'Aktife Al':'Tamamla'}</button></div>`;}).join('')||'<div class="im-c im-m">Hedef yok.</div>'}</div>`;
    } else if(m==='resources'){
      const bks=S.books.filter(b=>b.sid===cs.id);
      o=`<div class="im-fl" style="margin-bottom:12px"><h1 class="im-h">Kaynaklar</h1><select id="im-rs" class="im-i" style="max-width:250px">${act.map(s=>`<option value="${s.id}" ${s.id===cs.id?'selected':''}>${esc(s.name)}</option>`).join('')}</select></div>
      <div class="im-g">${bks.map(b=>`<div class="im-c"><div class="im-m">${esc(b.subj)}</div><b>${esc(b.title)}</b><div class="im-bar" style="margin:8px 0"><div style="width:${b.prog}%;background:#f59e0b"></div></div><div class="im-fl"><span class="im-m">%${b.prog}</span><button data-bi="${b.id}" class="im-b im-ba">+%10 İlerlet</button></div></div>`).join('')||'<div class="im-c im-m">Kaynak Kütüphanem ekranından kitap aktarabilirsiniz.</div>'}</div>`;
    } else if(m==='library'){
      const its=S.library.filter(b=>b.grp===S.ui.libGrp);
      o=`<h1 class="im-h" style="margin-bottom:12px">Kaynak Kütüphanem</h1>
      <div class="im-c im-sc">${GROUPS.map(g=>`<button data-lg="${esc(g)}" class="im-p ${S.ui.libGrp===g?'on':''}">${esc(g)}</button>`).join('')}</div>
      <div class="im-c im-g"><input id="im-lt" placeholder="Kitap adı" class="im-i"/><input id="im-ls" value="Matematik" class="im-i"/><button id="im-la" class="im-b im-ba">+ ${esc(S.ui.libGrp)} Ekle</button></div>
      <div class="im-g">${its.map(b=>`<div class="im-c"><div class="im-m">${esc(b.subj)} · ${b.pages} sf</div><b>${esc(b.title)}</b><div style="display:flex;gap:6px;margin-top:8px"><select id="im-as-${b.id}" class="im-i">${act.map(s=>`<option value="${s.id}">${esc(s.name)}</option>`).join('')}</select><button data-as="${b.id}" class="im-b im-bp">Aktar</button></div></div>`).join('')||`<div class="im-c im-m">${esc(S.ui.libGrp)} grubunda kitap yok.</div>`}</div>`;
    } else if(m==='optical'){
      let d=0,y=0,b=0; S.optGrid.forEach(r=>{if(!r.m)b++;else if(r.m===r.k)d++;else y++;}); const net=+(d-y/4).toFixed(2);
      o=`<h1 class="im-h" style="margin-bottom:12px">Fotoğraftan Optik Okuma</h1>
      <div class="im-g"><div class="im-c"><b>1) Cevap Anahtarı .xlsx</b><div style="margin-top:8px"><button id="im-ok" class="im-b im-bg">Örnek Anahtar Yükle</button></div><div class="im-m" style="margin-top:6px">${S.optKey?'✓ Yüklendi':'Henüz yok'}</div></div>
      <div class="im-c"><b>2) Optik Form Fotoğrafı</b><div style="margin-top:8px"><button id="im-op" class="im-b im-bp">Örnek Formu Tara</button></div><div class="im-m" style="margin-top:6px">${S.optPhoto?'✓ '+esc(S.optPhoto):'Önce yükle veya tara'}</div></div></div>
      ${(S.optKey||S.optPhoto)?`<div class="im-c"><div class="im-fl" style="margin-bottom:10px"><span><b>${d}D / ${y}Y / ${b}B → ${net} Net</b></span><button id="im-os" class="im-b im-bp">Onayla ve Öğrenciye Yaz</button></div><div class="im-g4">${S.optGrid.map((r,i)=>`<div style="padding:8px;border:1px solid var(--border,#e2e8f0);border-radius:10px;display:flex;justify-content:space-between;align-items:center"><span>S${r.q} (${r.k})</span><select data-og="${i}" class="im-i" style="width:66px;padding:4px">${['','A','B','C','D','E'].map(c=>`<option value="${c}" ${r.m===c?'selected':''}>${c||'Boş'}</option>`).join('')}</select></div>`).join('')}</div></div>`:''}`;
    } else if(m==='reports'){
      const gen=S.exams.filter(e=>e.sid===cs.id&&e.kind==='general'), br=S.exams.filter(e=>e.sid===cs.id&&e.kind==='branch');
      const eA=gen.find(e=>e.id===S.ui.cmpA)||gen[0], eB=gen.find(e=>e.id===S.ui.cmpB)||gen[gen.length-1], df=eA&&eB?+(eB.net-eA.net).toFixed(2):0;
      o=`<div class="im-fl" style="margin-bottom:12px"><h1 class="im-h">Genel Raporlar</h1><select id="im-rps" class="im-i" style="max-width:250px">${act.map(s=>`<option value="${s.id}" ${s.id===cs.id?'selected':''}>${esc(s.name)}</option>`).join('')}</select></div>
      <div style="display:flex;gap:8px;margin-bottom:12px"><button data-rt="general" class="im-p ${S.ui.repTab==='general'?'on':''}">Genel (${gen.length})</button><button data-rt="branch" class="im-p ${S.ui.repTab==='branch'?'on':''}">Branş (${br.length})</button></div>
      ${S.ui.repTab==='general'?`<div class="im-c"><b>Deneme Karşılaştırma</b>${gen.length>=2?`<div class="im-g" style="margin-top:8px"><select id="im-ca" class="im-i">${gen.map(e=>`<option value="${e.id}" ${eA&&e.id===eA.id?'selected':''}>${esc(e.name)} (${e.net})</option>`).join('')}</select><select id="im-cb" class="im-i">${gen.map(e=>`<option value="${e.id}" ${eB&&e.id===eB.id?'selected':''}>${esc(e.name)} (${e.net})</option>`).join('')}</select><div style="padding:10px;border-radius:10px;background:rgba(16,185,129,.12);font-weight:800;text-align:center">Fark: ${df>=0?'+':''}${df} net</div></div>`:'<div class="im-m">En az 2 deneme gerekli.</div>'}</div>`:`<div class="im-c">${br.map(e=>`<div class="im-fl" style="padding:6px 0"><b>${esc(e.name)}</b><span>${e.net} net</span></div>`).join('')||'<div class="im-m">Branş denemesi yok.</div>'}</div>`}
      <div class="im-c"><div class="im-fl" style="margin-bottom:8px"><b>Admin Notu (${esc(cs.name)})</b><button id="im-ans" class="im-b im-bp">Kaydet</button></div><textarea id="im-ant" rows="3" class="im-i">${esc(cs.note||'')}</textarea></div>`;
    } else if(m==='weeklyReports'){
      const l=S.weeklyReports.filter(r=>r.status===S.ui.wrTab);
      o=`<div class="im-fl" style="margin-bottom:12px"><div><h1 class="im-h">Haftalık Raporlar</h1><div class="im-m">Bekleyen → Onaylı → Gönderilen akışı</div></div><button id="im-wrn" class="im-b im-bp">+ Şimdi Oluştur</button></div>
      <div style="display:flex;gap:8px;margin-bottom:12px"><button data-wt="pending" class="im-p ${S.ui.wrTab==='pending'?'on':''}">Bekleyen</button><button data-wt="approved" class="im-p ${S.ui.wrTab==='approved'?'on':''}">Onaylı</button><button data-wt="sent" class="im-p ${S.ui.wrTab==='sent'?'on':''}">Gönderilen</button></div>`
      +(l.map(r=>`<div class="im-c im-fl"><div><b>${esc(stu(r.sid).name)}</b> · ${esc(r.week)}<div class="im-m">${esc(r.text)}</div></div><div>${r.status==='pending'?`<button data-wa="approved:${r.id}" class="im-b im-bp">Onayla</button>`:r.status==='approved'?`<button data-wa="sent:${r.id}" class="im-b im-bg">Gönder</button>`:'<span class="im-bdg" style="background:#059669">Gönderildi ✓</span>'}</div></div>`).join('')||'<div class="im-c im-m">Rapor yok.</div>');
    } else if(m==='payments'){
      const l=act.filter(s=>(S.ui.payF==='all'||(S.ui.payF==='has'?s.rem>0:s.rem<=0))&&(!S.ui.payQ||s.name.toLowerCase().includes(S.ui.payQ.toLowerCase())));
      o=`<h1 class="im-h" style="margin-bottom:12px">Ödeme Takibi</h1>
      <div class="im-c im-fl"><input id="im-pq" value="${esc(S.ui.payQ)}" placeholder="Öğrenci ara..." class="im-i" style="max-width:250px"/><div style="display:flex;gap:6px">${[['all','Tümü'],['has','Seansı Var'],['none','Seansı Yok']].map(([k,lb])=>`<button data-pf="${k}" class="im-p ${S.ui.payF===k?'on':''}">${lb}</button>`).join('')}</div></div>
      <div class="im-g">${l.map(s=>`<div class="im-c"><div class="im-fl"><div><b>${esc(s.name)}</b><div class="im-m">${s.exam}</div></div><span class="im-bdg" style="background:${s.rem>0?'#059669':'#e11d48'}">${s.rem>0?'Seansı Var':'Bitti'}</span></div><div class="im-fl" style="margin-top:8px;font-size:12px"><span>AYLIK SEANS</span><b>${s.rem}/${s.tot} kaldı</b></div><div class="im-seg">${[0,1,2,3].map(i=>`<div class="${i<s.rem?'on':''}"></div>`).join('')}</div><div style="display:flex;flex-direction:column;gap:6px"><button data-ps="use:${s.id}" class="im-b im-bg">— Seans Kullan</button><button data-ps="add4:${s.id}" class="im-b im-bp">+ 4 Seans Ekle</button><div style="display:grid;grid-template-columns:1fr 1fr;gap:6px"><button data-ps="telafi:${s.id}" class="im-b im-ba">+ Telafi</button><button data-ps="man:${s.id}" class="im-b">— Manuel</button></div></div></div>`).join('')}</div>`;
    } else if(m==='news'){
      o=`<h1 class="im-h" style="margin-bottom:12px">Yenilikler</h1>`+NEWS.map(n=>`<div class="im-c"><div class="im-fl"><span class="im-bdg">${n.tag} · YENİ</span><span class="im-m">${n.date}</span></div><div style="font-weight:800;margin:6px 0">${n.title}</div><div class="im-m">${n.desc}</div></div>`).join('');
    } else if(m==='profile'){
      o=`<h1 class="im-h" style="margin-bottom:12px">Profil</h1><div class="im-c" style="max-width:520px"><b>${esc(S.coach.name)}</b><div class="im-m" style="margin-bottom:10px">${esc(S.coach.email)}</div><input id="im-pn" value="${esc(S.coach.name)}" class="im-i" style="margin-bottom:8px"/><button id="im-psv" class="im-b im-bg">Değişiklikleri Kaydet</button></div>`;
    }
    h.innerHTML=o; bind(h);
  }
  function bind(h){
    const q=id=>h.querySelector('#'+id);
    if(q('im-pb')) q('im-pb').onclick=()=>{S.ui.pomoRun=!S.ui.pomoRun;clearInterval(pInt);if(S.ui.pomoRun)pInt=setInterval(()=>{if(S.ui.pomoSec>0){S.ui.pomoSec--;const c=document.getElementById('im-pc');if(c)c.textContent=String(Math.floor(S.ui.pomoSec/60)).padStart(2,'0')+':'+String(S.ui.pomoSec%60).padStart(2,'0');}else{clearInterval(pInt);S.ui.pomoRun=false;S.ui.pomoMin+=25;S.ui.pomoSec=1500;save();render();toast('Pomodoro bitti!');}},1000);render();};
    if(q('im-da')) q('im-da').onclick=()=>{const v=q('im-dn').value.trim();if(!v)return;(S.dailyNotes[TODAY]=S.dailyNotes[TODAY]||[]).push(v);save();render();toast('Not eklendi.');};
    if(q('im-ma')) q('im-ma').onclick=()=>{S.meetings.unshift({id:'mt-'+Date.now(),sid:q('im-ms').value,date:TODAY,time:q('im-mt').value,title:q('im-ml').value||'Görüşme',done:false});save();render();toast('Görüşme eklendi.');};
    h.querySelectorAll('[data-mtog]').forEach(b=>b.onclick=()=>{const x=S.meetings.find(i=>i.id===b.dataset.mtog);if(x){x.done=!x.done;save();render();}});
    h.querySelectorAll('[data-mdel]').forEach(b=>b.onclick=()=>{S.meetings=S.meetings.filter(i=>i.id!==b.dataset.mdel);save();render();});
    h.querySelectorAll('[data-st]').forEach(b=>b.onclick=()=>{S.ui.stuTab=b.dataset.st;render();});
    h.querySelectorAll('[data-rf]').forEach(b=>b.onclick=()=>{S.ui.risk=b.dataset.rf;render();});
    if(q('im-sq')) q('im-sq').oninput=e=>{S.ui.stuQ=e.target.value;render();};
    h.querySelectorAll('[data-ar]').forEach(b=>b.onclick=()=>{const s=stu(b.dataset.ar);s.archived=!s.archived;save();render();});
    h.querySelectorAll('[data-go]').forEach(b=>b.onclick=()=>{const[v,id]=b.dataset.go.split(':');S.ui.stu=id;open(v);});
    if(q('im-ts')) q('im-ts').onchange=e=>{S.ui.stu=e.target.value;render();};
    h.querySelectorAll('[data-tp]').forEach(b=>b.onclick=()=>{const s=stu(S.ui.stu);s.topics=s.topics||{};const c=s.topics[b.dataset.tp]||'none';s.topics[b.dataset.tp]=c==='none'?'progress':c==='progress'?'done':'none';save();render();});
    if(q('im-gs')) q('im-gs').onchange=e=>{S.ui.stu=e.target.value;render();};
    h.querySelectorAll('[data-gt]').forEach(b=>b.onclick=()=>{S.ui.goalTab=b.dataset.gt;render();});
    if(q('im-gad')) q('im-gad').onclick=()=>{const t=q('im-gtl').value.trim();if(!t)return;S.goals.unshift({id:'gl-'+Date.now(),sid:S.ui.stu,subj:q('im-gsu').value,title:t,cur:0,tgt:Number(q('im-gtg').value)||30,unit:'net',done:false});save();render();toast('Hedef eklendi.');};
    h.querySelectorAll('[data-gi]').forEach(b=>b.onclick=()=>{const g=S.goals.find(x=>x.id===b.dataset.gi);if(g){g.cur=Math.min(g.tgt,g.cur+2);save();render();}});
    h.querySelectorAll('[data-gd]').forEach(b=>b.onclick=()=>{const g=S.goals.find(x=>x.id===b.dataset.gd);if(g){g.done=!g.done;save();render();}});
    if(q('im-rs')) q('im-rs').onchange=e=>{S.ui.stu=e.target.value;render();};
    h.querySelectorAll('[data-bi]').forEach(b=>b.onclick=()=>{const x=S.books.find(i=>i.id===b.dataset.bi);if(x){x.prog=Math.min(100,x.prog+10);save();render();}});
    h.querySelectorAll('[data-lg]').forEach(b=>b.onclick=()=>{S.ui.libGrp=b.dataset.lg;render();});
    if(q('im-la')) q('im-la').onclick=()=>{const t=q('im-lt').value.trim();if(!t)return;S.library.unshift({id:'lb-'+Date.now(),grp:S.ui.libGrp,title:t,subj:q('im-ls').value||'Genel',pages:240});save();render();toast('Kütüphaneye eklendi.');};
    h.querySelectorAll('[data-as]').forEach(b=>b.onclick=()=>{const lb=S.library.find(x=>x.id===b.dataset.as),sel=h.querySelector('#im-as-'+lb.id);if(lb&&sel){S.books.push({id:'bk-'+Date.now(),sid:sel.value,title:lb.title,subj:lb.subj,prog:0});save();toast('Öğrenciye aktarıldı.');}});
    if(q('im-ok')) q('im-ok').onclick=()=>{S.optKey=true;save();render();toast('Anahtar yüklendi.');};
    if(q('im-op')) q('im-op').onclick=()=>{S.optKey=true;S.optPhoto='ornek-tyt-optik.jpg';save();render();toast('Form tarandı.');};
    h.querySelectorAll('[data-og]').forEach(s=>s.onchange=e=>{S.optGrid[Number(s.dataset.og)].m=e.target.value;save();render();});
    if(q('im-os')) q('im-os').onclick=()=>{let d=0,y=0;S.optGrid.forEach(r=>{if(r.m){if(r.m===r.k)d++;else y++;}});const net=+(d-y/4).toFixed(2);S.exams.push({id:'ex-'+Date.now(),sid:S.ui.stu,kind:'branch',name:`Optik (${d}D/${y}Y)`,date:TODAY,net});save();toast(`Optik (${net} net) kaydedildi.`);};
    if(q('im-rps')) q('im-rps').onchange=e=>{S.ui.stu=e.target.value;render();};
    h.querySelectorAll('[data-rt]').forEach(b=>b.onclick=()=>{S.ui.repTab=b.dataset.rt;render();});
    if(q('im-ca')) q('im-ca').onchange=e=>{S.ui.cmpA=e.target.value;render();};
    if(q('im-cb')) q('im-cb').onchange=e=>{S.ui.cmpB=e.target.value;render();};
    if(q('im-ans')) q('im-ans').onclick=()=>{stu(S.ui.stu).note=q('im-ant').value;save();toast('Admin notu kaydedildi.');};
    h.querySelectorAll('[data-wt]').forEach(b=>b.onclick=()=>{S.ui.wrTab=b.dataset.wt;render();});
    if(q('im-wrn')) q('im-wrn').onclick=()=>{const st=stu(S.ui.stu);S.weeklyReports.unshift({id:'wr-'+Date.now(),sid:st.id,week:'Bu Hafta',status:'pending',text:`Konu ilerlemesi %${tPct(st)}, kalan seans ${st.rem}/${st.tot}.`});S.ui.wrTab='pending';save();render();toast('Taslak oluşturuldu.');};
    h.querySelectorAll('[data-wa]').forEach(b=>b.onclick=()=>{const[st,id]=b.dataset.wa.split(':');const r=S.weeklyReports.find(x=>x.id===id);if(r){r.status=st;save();render();toast(st==='approved'?'Onaylandı.':'Gönderildi.');}});
    if(q('im-pq')) q('im-pq').oninput=e=>{S.ui.payQ=e.target.value;render();};
    h.querySelectorAll('[data-pf]').forEach(b=>b.onclick=()=>{S.ui.payF=b.dataset.pf;render();});
    h.querySelectorAll('[data-ps]').forEach(b=>b.onclick=()=>{const[a,id]=b.dataset.ps.split(':'),s=stu(id);if(a==='use'||a==='man'){if(s.rem>0)s.rem--;}else if(a==='add4'){s.rem+=4;s.tot=Math.max(4,s.rem);}else if(a==='telafi')s.rem+=1;save();render();toast('Seans güncellendi.');});
    if(q('im-psv')) q('im-psv').onclick=()=>{S.coach.name=q('im-pn').value.trim()||S.coach.name;save();render();toast('Profil kaydedildi.');};
  }
  function mount(){
    const hh=window.location.hash||''; if(hh.startsWith('#davet=')||hh.startsWith('#veli=')) return;
    addCss();
    const sb=document.querySelector('.app-sidebar, aside'); if(!sb||document.getElementById('ivme-mod-nav-wrap')) return;
    const nw=document.createElement('div'); nw.id='ivme-mod-nav-wrap'; nw.style.cssText='border-top:1px solid var(--border,#e2e8f0);margin-top:8px;padding:6px 8px 14px;';
    nw.innerHTML=`
      <div class="im-gt" data-ac="im-g1"><span>Program Modülleri</span><span>▾</span></div><div id="im-g1"><button type="button" class="im-nb" data-im="daily">🕒 Günlük Program</button><button type="button" class="im-nb" data-im="meetings">📅 Görüşmeler</button></div>
      <div class="im-gt" data-ac="im-g2"><span>Öğrenci Takibi</span><span>▾</span></div><div id="im-g2"><button type="button" class="im-nb" data-im="students">👥 Öğrenciler</button><button type="button" class="im-nb" data-im="topics">✅ Konu Takibi</button><button type="button" class="im-nb" data-im="goals">🎯 Hedefler</button><button type="button" class="im-nb" data-im="resources">📚 Kaynaklar</button><button type="button" class="im-nb" data-im="library">📖 Kaynak Kütüphanem</button></div>
      <div class="im-gt" data-ac="im-g3"><span>Analiz & İşletme</span><span>▾</span></div><div id="im-g3"><button type="button" class="im-nb" data-im="optical">📷 Fotoğraftan Optik</button><button type="button" class="im-nb" data-im="reports">📊 Genel Raporlar</button><button type="button" class="im-nb" data-im="weeklyReports">🗓️ Haftalık Raporlar</button><button type="button" class="im-nb" data-im="payments">💳 Ödeme Takibi</button><button type="button" class="im-nb" data-im="news"><span>✨ Yenilikler</span><span class="im-bdg">6</span></button><button type="button" class="im-nb" data-im="profile">👤 Profil</button></div>`;
    sb.appendChild(nw);
    const host=document.createElement('section'); host.id='ivme-mod-host';
    const anc=document.getElementById('tab-home')||document.querySelector('main')||document.body;
    if(anc.parentNode&&anc!==document.body) anc.parentNode.insertBefore(host,anc.nextSibling); else document.body.appendChild(host);
    nw.querySelectorAll('[data-ac]').forEach(t=>t.onclick=()=>{const b=document.getElementById(t.dataset.ac);if(b)b.style.display=b.style.display==='none'?'block':'none';});
    nw.querySelectorAll('[data-im]').forEach(b=>b.onclick=()=>open(b.dataset.im));
    if(typeof window.switchTab==='function'){const orig=window.switchTab; window.switchTab=function(){hide(); return orig.apply(this,arguments);};}
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',mount); else mount();
})();
