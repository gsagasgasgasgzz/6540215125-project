const cards = document.getElementById('cards');
const statusBox = document.getElementById('status');
const dialog = document.getElementById('detail');
let all = [], view = 'explore', selected = null;
const icons = {'วิชาการ':'⌘','จิตอาสา':'♥','แข่งขัน':'✦','แนะแนว':'◈'};
function escapeHTML(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function render(items){
  cards.innerHTML = items.map(a=>`<article class="card"><div class="art">${icons[a.category]||'✦'}</div>
  <div class="cardcontent"><span class="tag">${escapeHTML(a.category)}</span><h3>${escapeHTML(a.title)}</h3>
  <div class="meta">◷ ${escapeHTML(a.activity_date)}<br>⌖ ${escapeHTML(a.location)}
  ${view==='explore'?`<br>♙ ${a.registered}/${a.capacity} คน`:''}</div>
  <div class="action"><button class="primary" data-id="${a.id}">ดูรายละเอียด <span>→</span></button></div></div></article>`).join('');
  if(!items.length) statusBox.textContent='ไม่พบกิจกรรมในรายการนี้'; else statusBox.textContent='';
  cards.querySelectorAll('[data-id]').forEach(btn=>btn.addEventListener('click',()=>openDetail(Number(btn.dataset.id))));
}
async function load(){
  statusBox.textContent='กำลังโหลดข้อมูลกิจกรรม...';
  try{
    const url=view==='mine'?'/api/my-activities':'/api/activities';
    const res=await fetch(url);if(!res.ok)throw new Error('โหลดข้อมูลไม่สำเร็จ');
    all=await res.json();filter();
  }catch(e){statusBox.textContent='เกิดข้อผิดพลาด: '+e.message;cards.innerHTML='';}
}
function filter(){const q=document.getElementById('search').value.toLowerCase();render(all.filter(a=>a.title.toLowerCase().includes(q)));}
async function openDetail(id){
  try{
    const res=await fetch('/api/activities/'+id);if(!res.ok)throw new Error('ไม่พบกิจกรรม');
    selected=await res.json();
    document.getElementById('d-title').textContent=selected.title;
    document.getElementById('d-meta').textContent=`${selected.category} • ${selected.activity_date} • ${selected.location}`;
    document.getElementById('d-desc').textContent=selected.description;
    document.getElementById('d-cap').textContent=`ลงทะเบียนแล้ว ${selected.registered} / ${selected.capacity} คน`;
    document.getElementById('feedback').textContent='';
    const button=document.getElementById('register');
    button.disabled=selected.registered>=selected.capacity;
    button.textContent=button.disabled?'กิจกรรมเต็มแล้ว':'ลงทะเบียนกิจกรรม →';
    dialog.showModal();
  }catch(e){statusBox.textContent=e.message;}
}
document.getElementById('register').addEventListener('click',async()=>{
  if(!selected)return;
  const btn=document.getElementById('register');btn.disabled=true;
  try{
    const res=await fetch('/api/registrations',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({student_id:1,activity_id:selected.id})});
    const data=await res.json();const msg=document.getElementById('feedback');
    msg.textContent=data.message||data.error||'เกิดข้อผิดพลาด';
    msg.style.color=res.ok?'#7ce1b1':'#ff9b91';
    if(res.ok){btn.textContent='ลงทะเบียนสำเร็จ ✓';await load();}
    else btn.disabled=false;
  }catch(e){document.getElementById('feedback').textContent='ไม่สามารถเชื่อมต่อเซิร์ฟเวอร์';btn.disabled=false;}
});
document.getElementById('close').addEventListener('click',()=>dialog.close());
document.getElementById('search').addEventListener('input',filter);
document.querySelectorAll('.nav').forEach(btn=>btn.addEventListener('click',()=>{
  view=btn.dataset.view;
  document.querySelectorAll('.nav').forEach(n=>n.classList.toggle('active',n===btn));
  document.getElementById('page-title').textContent=view==='mine'?'กิจกรรมของฉัน':'ค้นพบกิจกรรมที่ใช่สำหรับคุณ.';
  document.getElementById('page-desc').textContent=view==='mine'?'กิจกรรมที่คุณลงทะเบียนไว้':'เลือกดูรายละเอียดและลงทะเบียนกิจกรรมได้จากหน้าเดียว';
  document.getElementById('section-title').textContent=view==='mine'?'รายการที่ลงทะเบียนแล้ว':'กิจกรรมที่เปิดให้เข้าร่วม';
  document.getElementById('search').value='';load();
}));
load();
