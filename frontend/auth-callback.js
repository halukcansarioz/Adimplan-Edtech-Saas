(function(){
'use strict';
var path=window.location.pathname||'/';
var initial=window.__adimplanAuthUrl||window.location;
var search=initial.search||'';
var hash=initial.hash||'';
var q=new URLSearchParams(search);
var h=new URLSearchParams(hash.replace(/^#/,''));
var hasAuthParams=q.has('code')||q.has('token_hash')||h.has('access_token')||h.has('error')||q.has('error');
var isLogin=/\/login(\.html)?$/i.test(path);
if(!isLogin&&hasAuthParams&&(path==='/'||/\/index\.html$/i.test(path))){
var dest=new URL('./login.html',window.location.origin);
dest.search=search;
dest.hash=hash;
window.location.replace(dest.toString());
return;
}
if(!isLogin)return;
function cleanUrl(){try{window.history.replaceState(null,'',window.location.pathname);}catch(e){}}
function showNotice(msg,isErr){
var box=document.getElementById('authAlert');
if(box){box.textContent=msg;box.className='alert show '+(isErr?'error':'success');return;}
var el=document.getElementById('adimplanAuthNotice');
if(!el){el=document.createElement('div');el.id='adimplanAuthNotice';el.setAttribute('role','alert');el.style.cssText='position:fixed;top:16px;left:50%;transform:translateX(-50%);z-index:9999;max-width:460px;width:90%;padding:12px 16px;border-radius:10px;font-family:inherit;font-size:14px;font-weight:600;box-shadow:0 10px 30px rgba(0,0,0,0.2);';document.body.appendChild(el);}
el.style.background=isErr?'#fef2f2':'#ecfdf5';
el.style.color=isErr?'#991b1b':'#065f46';
el.style.border=isErr?'1px solid #fecaca':'1px solid #a7f3d0';
el.textContent=msg;
}
function mapError(code,desc){
var raw=(code||'')+' '+(desc||'');
if(/otp_expired|expired/i.test(raw))return 'Bağlantının süresi dolmuş. Lütfen yeni bir doğrulama veya şifre sıfırlama bağlantısı isteyin.';
if(/access_denied/i.test(raw))return 'Erişim reddedildi veya bağlantı geçersiz. Lütfen tekrar deneyin.';
if(/invalid/i.test(raw))return 'Geçersiz veya daha önce kullanılmış doğrulama bağlantısı.';
return desc?('İşlem tamamlanamadı: '+desc):'Kimlik doğrulama işlemi tamamlanamadı.';
}
function getClient(){
if(window.__adimplanAuthClient)return window.__adimplanAuthClient;
var cfg=window.ADIMPLAN_CONFIG||window.__CONFIG__||window.CONFIG||{};
var url=window.SUPABASE_URL||cfg.supabaseUrl||cfg.SUPABASE_URL||'';
var key=window.SUPABASE_ANON_KEY||cfg.supabaseAnonKey||cfg.SUPABASE_ANON_KEY||'';
if(url&&key&&window.supabase&&typeof window.supabase.createClient==='function'){return window.supabase.createClient(url,key);}
return null;
}
var modalOpen=false;
function openRecoveryModal(sb){
if(modalOpen||document.getElementById('adimplanRecoveryModal'))return;
modalOpen=true;
var overlay=document.createElement('div');
overlay.id='adimplanRecoveryModal';
overlay.style.cssText='position:fixed;inset:0;z-index:10000;background:rgba(15,23,42,0.65);display:flex;align-items:center;justify-content:center;padding:16px;';
var card=document.createElement('div');
card.style.cssText='background:#ffffff;color:#0f172a;border-radius:16px;max-width:420px;width:100%;padding:24px;box-shadow:0 20px 50px rgba(0,0,0,0.25);font-family:inherit;';
var title=document.createElement('h2');
title.textContent='Yeni Şifre Belirle';
title.style.cssText='margin:0 0 8px 0;font-size:20px;font-weight:700;';
var sub=document.createElement('p');
sub.textContent='Hesabınız için en az 6 karakterli yeni bir şifre belirleyin.';
sub.style.cssText='margin:0 0 16px 0;font-size:14px;color:#475569;';
var form=document.createElement('form');
var lbl1=document.createElement('label');
lbl1.textContent='Yeni Şifre';
lbl1.style.cssText='display:block;font-size:13px;font-weight:600;margin-bottom:6px;';
var inp1=document.createElement('input');
inp1.type='password';inp1.minLength=6;inp1.required=true;inp1.autocomplete='new-password';
inp1.placeholder='En az 6 karakter';
inp1.style.cssText='width:100%;box-sizing:border-box;padding:10px 12px;border:1px solid #cbd5e1;border-radius:8px;margin-bottom:12px;font-size:14px;';
var lbl2=document.createElement('label');
lbl2.textContent='Şifre Tekrar';
lbl2.style.cssText='display:block;font-size:13px;font-weight:600;margin-bottom:6px;';
var inp2=document.createElement('input');
inp2.type='password';inp2.minLength=6;inp2.required=true;inp2.autocomplete='new-password';
inp2.placeholder='Şifreyi tekrar girin';
inp2.style.cssText='width:100%;box-sizing:border-box;padding:10px 12px;border:1px solid #cbd5e1;border-radius:8px;margin-bottom:12px;font-size:14px;';
var errP=document.createElement('p');
errP.style.cssText='margin:0 0 12px 0;font-size:13px;color:#b91c1c;display:none;';
var actions=document.createElement('div');
actions.style.cssText='display:flex;gap:8px;justify-content:flex-end;';
var cancelBtn=document.createElement('button');
cancelBtn.type='button';cancelBtn.textContent='İptal';
cancelBtn.style.cssText='padding:10px 14px;border-radius:8px;border:1px solid #cbd5e1;background:#ffffff;color:#334155;font-weight:600;cursor:pointer;';
cancelBtn.addEventListener('click',function(){overlay.remove();modalOpen=false;});
var saveBtn=document.createElement('button');
saveBtn.type='submit';saveBtn.textContent='Şifreyi Güncelle';
saveBtn.style.cssText='padding:10px 16px;border-radius:8px;border:none;background:#4f46e5;color:#ffffff;font-weight:600;cursor:pointer;';
actions.appendChild(cancelBtn);actions.appendChild(saveBtn);
form.appendChild(lbl1);form.appendChild(inp1);form.appendChild(lbl2);form.appendChild(inp2);form.appendChild(errP);form.appendChild(actions);
form.addEventListener('submit',async function(ev){
ev.preventDefault();
var p1=inp1.value||'';var p2=inp2.value||'';
if(p1.length<6){errP.textContent='Şifre en az 6 karakter olmalıdır.';errP.style.display='block';return;}
if(p1!==p2){errP.textContent='Şifreler eşleşmiyor.';errP.style.display='block';return;}
saveBtn.disabled=true;saveBtn.textContent='Güncelleniyor...';errP.style.display='none';
try{
var res=await sb.auth.updateUser({password:p1});
if(res&&res.error){errP.textContent=res.error.message||'Şifre güncellenemedi.';errP.style.display='block';saveBtn.disabled=false;saveBtn.textContent='Şifreyi Güncelle';return;}
overlay.remove();modalOpen=false;cleanUrl();
showNotice('Şifreniz başarıyla güncellendi, şimdi giriş yapabilirsiniz.',false);
}catch(err){
errP.textContent='Şifre güncellenirken bir hata oluştu.';errP.style.display='block';saveBtn.disabled=false;saveBtn.textContent='Şifreyi Güncelle';
}
});
card.appendChild(title);card.appendChild(sub);card.appendChild(form);overlay.appendChild(card);document.body.appendChild(overlay);
inp1.focus();
}
async function init(){
var errCode=q.get('error')||h.get('error')||'';
var errDesc=q.get('error_description')||h.get('error_description')||'';
if(errCode||errDesc){showNotice(mapError(errCode,errDesc),true);cleanUrl();return;}
var sb=getClient();
if(!sb)return;
if(sb.auth&&typeof sb.auth.onAuthStateChange==='function'){
sb.auth.onAuthStateChange(function(event){if(event==='PASSWORD_RECOVERY'){openRecoveryModal(sb);}});
}
var code=q.get('code');
var tokenHash=q.get('token_hash');
var type=q.get('type')||h.get('type')||'';
var accessToken=h.get('access_token');
var refreshToken=h.get('refresh_token');
if(code&&sb.auth&&typeof sb.auth.exchangeCodeForSession==='function'){
try{
var ex=await sb.auth.exchangeCodeForSession(code);
if(ex&&ex.error){showNotice(mapError(ex.error.code,ex.error.message),true);return;}
cleanUrl();
if(type==='recovery'){openRecoveryModal(sb);}
else if(type==='signup'||type==='email'||!type){showNotice('E-posta adresiniz doğrulandı, şimdi giriş yapabilirsiniz.',false);}
}catch(e){showNotice('Doğrulama kodu işlenemedi.',true);}
return;
}
if(tokenHash&&type&&sb.auth&&typeof sb.auth.verifyOtp==='function'){
try{
var vo=await sb.auth.verifyOtp({token_hash:tokenHash,type:type});
if(vo&&vo.error){showNotice(mapError(vo.error.code,vo.error.message),true);return;}
cleanUrl();
if(type==='recovery'){openRecoveryModal(sb);}
else if(type==='signup'||type==='email'){showNotice('E-posta adresiniz doğrulandı, şimdi giriş yapabilirsiniz.',false);}
}catch(e){showNotice('Doğrulama bağlantısı işlenemedi.',true);}
return;
}
if(accessToken&&refreshToken&&sb.auth&&typeof sb.auth.setSession==='function'){
try{await sb.auth.setSession({access_token:accessToken,refresh_token:refreshToken});}catch(e){}
if(type==='recovery'){openRecoveryModal(sb);}
else if(type==='signup'||type==='email'){cleanUrl();showNotice('E-posta adresiniz doğrulandı, şimdi giriş yapabilirsiniz.',false);}
return;
}
if(type==='recovery'){openRecoveryModal(sb);}
else if(type==='signup'||type==='email'){cleanUrl();showNotice('E-posta adresiniz doğrulandı, şimdi giriş yapabilirsiniz.',false);}
}
if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',init);}else{init();}
})();
