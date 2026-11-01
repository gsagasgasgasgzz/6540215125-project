(async function(){
 const el=id=>document.getElementById(id);
 async function setup(){
  const me=await fetch('/api/me').then(r=>r.json());if(!me.user||me.user.role!=='admin')return;
  el('announcementAdmin').hidden=false;
  const token=me.csrf;
  async function refreshNews(){
   const r=await fetch('/api/announcements');const b=await r.json();
   el('announcementAdminList').innerHTML=b.data.map(x=>`<div class="adminrow"><span>${x.kind==='maintenance'?'[แจ้งปรับปรุง] ':''}${escapeText(x.title)}</span><button class="danger" data-id="${x.id}">ลบ</button></div>`).join('');
   el('announcementAdminList').querySelectorAll('[data-id]').forEach(btn=>btn.onclick=async()=>{
    if(!confirm('ยืนยันลบประกาศนี้?'))return;
    const r=await fetch('/api/announcements/'+btn.dataset.id,{method:'DELETE',headers:{'X-CSRF-Token':token}});const b=await r.json();if(!r.ok)alert(b.error||'เกิดข้อผิดพลาด');await refreshNews();
   });
  }
  function escapeText(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
  el('announcementForm').onsubmit=async e=>{
   e.preventDefault();const f=e.currentTarget,button=f.querySelector('button');button.disabled=true;
   try{const fd=new FormData(f);const file=fd.get('image');if(file&&file.size>5*1024*1024)throw Error('รูปต้องไม่เกิน 5 MB');
    const r=await fetch('/api/announcements',{method:'POST',headers:{'X-CSRF-Token':token},body:fd});const b=await r.json();if(!r.ok)throw Error(b.error||'ไม่สำเร็จ');f.reset();alert('เผยแพร่ประกาศแล้ว');await refreshNews();
   }catch(err){alert(err.message)}finally{button.disabled=false}
  };await refreshNews();
 }
 setup().catch(e=>console.error(e));
})();
