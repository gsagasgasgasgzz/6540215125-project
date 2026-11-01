
let me=null,csrf='',all=[],people=[],advisors=[],editing=null,mode='login',toastTimer;
const el=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const statusLabel={planning:'วางแผน',in_progress:'กำลังทำ',completed:'เสร็จสิ้น',archived:'ประวัติเก่า'};
function toast(msg){el('toast').textContent=msg;el('toast').classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>el('toast').classList.remove('show'),3800)}
async function api(path,method='GET',data){
  const opts={method,credentials:'same-origin',headers:{}};
  if(data!==undefined){opts.headers['Content-Type']='application/json';opts.body=JSON.stringify(data)}
  if(!['GET','HEAD'].includes(method))opts.headers['X-CSRF-Token']=csrf;
  let r=await fetch(path,opts),body=await r.json().catch(()=>({}));
  if(!r.ok)throw new Error(body.error||'เกิดข้อผิดพลาด ('+r.status+')');
  return body;
}
function avatarMarkup(u,large=false){return u?.avatar?`<img class="avatar ${large?'large':''}" src="/avatars/${encodeURIComponent(u.avatar)}" alt="รูปโปรไฟล์">`:`<span class="avatar ${large?'large':''}">${esc((u?.name||'U').slice(0,1).toUpperCase())}</span>`}
function toggleUserMenu(){el('userMenu').hidden=!el('userMenu').hidden}
function openProfile(){el('userMenu').hidden=true;el('profileModal').hidden=false;el('profileAvatar').innerHTML=avatarMarkup(me,true);el('profileName').textContent=me.name;el('profileId').textContent=me.student_id+' • '+me.role;el('profileNameInput').value=me.name}
function closeProfile(){el('profileModal').hidden=true}
function authMode(next){mode=next;el('nameWrap').hidden=next==='login';el('name').required=next==='register';el('tabLogin').classList.toggle('active',next==='login');el('tabRegister').classList.toggle('active',next==='register');el('authSubmit').textContent=next==='login'?'เข้าสู่ระบบ':'สมัครสมาชิก'}
el('authForm').onsubmit=async e=>{
 e.preventDefault();
 const d={student_id:el('sid').value.trim(),password:el('password').value};
 if(mode==='register')d.name=el('name').value.trim();
 try{
   let out=await api(mode==='login'?'/api/login':'/api/register','POST',d);
   if(mode==='register'){toast('สมัครสำเร็จ กรุณาเข้าสู่ระบบ');authMode('login');el('password').value='';return}
   me=out.user;csrf=out.csrf;await refresh();
 }catch(err){toast(err.message)}
};
async function boot(){try{let out=await api('/api/me');me=out.user;csrf=out.csrf||'';if(me)await refresh();else showAuth()}catch(e){showAuth()}}
function showAuth(){el('adminQuickLink').hidden=true;el('sideAdminLink').hidden=true;el('auth').hidden=false;el('workspace').hidden=true;el('who').innerHTML=''}
async function logout(){try{await api('/api/logout','POST');me=null;csrf='';showAuth();toast('ออกจากระบบแล้ว')}catch(e){toast(e.message)}}
function canEdit(p){return me?.role==='admin'||(me?.role==='teacher'&&p.advisor_id===me.student_id)||(me?.role==='student'&&(p.created_by===me.student_id||p.members.some(m=>m.student_id===me.student_id)))}
function canManage(p){return me?.role==='admin'||(me?.role==='teacher'&&p.advisor_id===me.student_id)}
async function refresh(){
 el('auth').hidden=true;el('workspace').hidden=false;el('adminQuickLink').hidden=me.role!=='admin';el('sideAdminLink').hidden=me.role!=='admin';
 el('who').innerHTML=`<div class="account"><button class="account-button" id="accountToggle">${avatarMarkup(me)}<span class="account-label"><b>${esc(me.name)}</b><small>${esc(me.role)}</small></span>⌄</button><div class="account-menu" id="userMenu" hidden><button id="profileBtn">👤 ดูและแก้ไขโปรไฟล์</button>${me.role==='admin'?'<a href="/admin" class="admin-link">⚙️ ระบบหลังบ้าน Admin</a>':''}<button id="logoutBtn">↪ ออกจากระบบ</button></div></div>`;
 el('accountToggle').onclick=toggleUserMenu;el('profileBtn').onclick=openProfile;el('logoutBtn').onclick=logout;
 el('newBtn').hidden=false;
 el('adminPanel').hidden=true;
 try{
  let results=await Promise.all([api('/api/projects'),api('/api/users'),api('/api/advisors'),api('/api/stats'),api('/api/history')]);
  all=results[0].data;people=results[1].data;advisors=results[2].data;
  renderProjects();renderStats(results[3]);renderHistory(results[4].data);renderUsers();
 }catch(e){toast(e.message)}
}
function renderProjects(){
 const q=el('search').value.toLowerCase(),f=el('filter').value;
 const items=all.filter(p=>(p.title+' '+p.description).toLowerCase().includes(q)&&(!f||p.status===f));
 el('projectList').innerHTML=items.length?items.map(p=>`<div class="project"><div class="projecttop"><h3>${esc(p.title)}</h3><span class="pill">${esc(statusLabel[p.status])}</span></div><p>${esc(p.description).slice(0,170)}</p><small class="muted">ปี ${esc(p.academic_year)} • ที่ปรึกษา: ${esc(p.advisor_name||'ยังไม่กำหนด')} • สมาชิก ${p.members.length} คน</small><div class="buttons"><button class="ghost" data-detail="${p.id}">รายละเอียด</button>${me?.role==="teacher"&&!p.advisor_id?`<button class="primary" data-claim="${p.id}">รับเป็นที่ปรึกษา</button>`:""}${canEdit(p)?`<button class="ghost" data-edit="${p.id}">แก้ไข</button>${canManage(p)?`<button class="danger" data-delete="${p.id}">ลบ</button>`:''}`:''}</div></div>`).join(''):'<p class="muted">ไม่พบโครงงาน</p>';
 el('projectList').querySelectorAll('[data-claim]').forEach(b=>b.onclick=async()=>{if(!confirm('ยืนยันรับเป็นอาจารย์ที่ปรึกษาของโครงงานนี้?'))return;try{await api('/api/projects/'+b.dataset.claim+'/claim-advisor','POST');toast('รับเป็นอาจารย์ที่ปรึกษาสำเร็จ');await refresh()}catch(e){toast(e.message)}});
 el('projectList').querySelectorAll('[data-detail]').forEach(b=>b.onclick=()=>detail(+b.dataset.detail));
 el('projectList').querySelectorAll('[data-edit]').forEach(b=>b.onclick=()=>openProject(+b.dataset.edit));
 el('projectList').querySelectorAll('[data-delete]').forEach(b=>b.onclick=()=>confirmDelete(+b.dataset.delete));
}
function renderStats(stats){
 const count=k=>stats.status[k]||0;
 el('total').textContent=all.length;el('ongoing').textContent=count('in_progress');el('done').textContent=count('completed');el('archived').textContent=count('archived');
 const max=Math.max(1,...Object.values(stats.status));
 el('chart').innerHTML=Object.keys(statusLabel).map(k=>`<div class="barrow"><span>${statusLabel[k]}</span><div class="track"><div class="fill" style="width:${count(k)/max*100}%"></div></div><b>${count(k)}</b></div>`).join('');
 const maxY=Math.max(1,...stats.years.map(y=>y.n));
 el('years').innerHTML=stats.years.length?stats.years.map(y=>`<div class="barrow"><span>${y.academic_year}</span><div class="track"><div class="fill" style="width:${y.n/maxY*100}%"></div></div><b>${y.n}</b></div>`).join(''):'<p class="muted">ยังไม่มีข้อมูล</p>';
}
function renderHistory(items){
 const labels={created:'สร้าง',updated:'แก้ไข',deleted:'ลบ',member_added:'เพิ่มสมาชิก',member_removed:'ลบสมาชิก',progress_added:'บันทึกความก้าวหน้า'};
 el('history').innerHTML=items.length?items.map(x=>`<div class="historyitem"><div><strong>${esc(labels[x.action]||x.action)}</strong> — ${esc(x.project_title)}<br><small>โดย ${esc(x.actor_id)} ${esc(x.details)}</small></div><small>${esc(x.created_at)}</small></div>`).join(''):'<p class="muted">ยังไม่มีประวัติ</p>';
}
function renderUsers(){
 if(me.role!=='admin')return;
 el('users').innerHTML=people.map(u=>`<div class="userrow"><div class="useridentity">${avatarMarkup(u)}<div><strong>${esc(u.name)}</strong><br><small class="muted">${esc(u.student_id)}</small></div></div><div class="useractions"><button class="ghost" data-rename="${esc(u.student_id)}">แก้ชื่อ</button>${u.role==='admin'?'<span class="pill">admin</span>':`<select data-user="${esc(u.student_id)}"><option value="student" ${u.role==='student'?'selected':''}>นักศึกษา</option><option value="teacher" ${u.role==='teacher'?'selected':''}>อาจารย์</option></select>`}</div></div>`).join('');
 el('users').querySelectorAll('[data-rename]').forEach(b=>b.onclick=async()=>{let u=people.find(x=>x.student_id===b.dataset.rename);let name=prompt('แก้ไขชื่อผู้ใช้',u.name);if(name===null)return;try{await api('/api/users/'+encodeURIComponent(u.student_id)+'/profile','PUT',{name:name.trim()});toast('บันทึกชื่อแล้ว');await refresh()}catch(e){toast(e.message)}});
 el('users').querySelectorAll('[data-user]').forEach(s=>s.onchange=async()=>{try{await api('/api/users/'+encodeURIComponent(s.dataset.user)+'/role','PUT',{role:s.value});toast('ปรับสิทธิ์เรียบร้อย');await refresh()}catch(e){toast(e.message);await refresh()}});
}
function openProject(id=null){
 editing=id;const p=all.find(x=>x.id===id);
 el('modalTitle').textContent=p?'แก้ไขโครงงาน':'เพิ่มโครงงาน';
 el('pTitle').value=p?.title||'';el('pDesc').value=p?.description||'';el('pYear').value=p?.academic_year||2569;el('pStatus').value=p?.status||'planning';
 el('pAdvisor').innerHTML='<option value="">ยังไม่กำหนด</option>'+advisors.map(a=>`<option value="${esc(a.student_id)}">${esc(a.name)} (${esc(a.student_id)})</option>`).join('');
 if(me.role==='teacher'){el('pAdvisor').value=me.student_id;el('pAdvisor').disabled=true}
 else if(me.role==='student'){el('pAdvisor').value=p?.advisor_id||'';el('pAdvisor').disabled=true;el('pStatus').disabled=true}
 else{el('pAdvisor').disabled=false;el('pAdvisor').value=p?.advisor_id||''}
 if(me.role!=='student')el('pStatus').disabled=false;
 el('modal').hidden=false;
}
function closeModal(){el('modal').hidden=true}
el('projectForm').onsubmit=async e=>{
 e.preventDefault();let d={title:el('pTitle').value.trim(),description:el('pDesc').value.trim(),academic_year:Number(el('pYear').value),status:editing&&me.role==='student'?all.find(x=>x.id===editing).status:el('pStatus').value,advisor_id:el('pAdvisor').value||null};
 try{await api(editing?'/api/projects/'+editing:'/api/projects',editing?'PUT':'POST',d);closeModal();toast(editing?'แก้ไขสำเร็จ':'เพิ่มโครงงานสำเร็จ');await refresh()}catch(e){toast(e.message)}
};
function confirmDelete(id){const p=all.find(x=>x.id===id);el('confirmText').textContent='ต้องการลบ "'+p.title+'" ใช่หรือไม่? ระบบจะเก็บบันทึกการลบไว้';el('confirmModal').hidden=false;el('confirmYes').onclick=async()=>{try{await api('/api/projects/'+id,'DELETE');el('confirmModal').hidden=true;toast('ลบโครงงานแล้ว');await refresh()}catch(e){toast(e.message)}}}
function closeDetail(){el('detailModal').hidden=true}
async function detail(id){
 const p=all.find(x=>x.id===id);if(!p)return;
 el('detailTitle').textContent=p.title;
 el('detailContent').innerHTML=`<p>${esc(p.description)}</p><p class="muted">สถานะ: ${esc(statusLabel[p.status])} • ปี ${p.academic_year} • ที่ปรึกษา: ${esc(p.advisor_name||'ยังไม่กำหนด')}</p><h3>สมาชิกโครงงาน</h3><div id="memberList"></div>${canManage(p)?'<div class="actions"><select id="memberSelect"></select><button class="primary" id="addMember">เพิ่มสมาชิก</button></div>':''}<h3>บันทึกความก้าวหน้า</h3><div id="progressList"></div>${canEdit(p)?'<form id="progressForm"><label>รายละเอียด<input id="progressNote" required maxlength="500"></label><label>ความคืบหน้า (%)<input id="progressPercent" type="number" min="0" max="100" required></label><button class="primary">บันทึกความก้าวหน้า</button></form>':''}`;
 el('detailModal').hidden=false;
 async function loadDetail(){
  const [m,pr]=await Promise.all([api('/api/projects/'+id+'/members'),api('/api/projects/'+id+'/progress')]);
  el('memberList').innerHTML=m.data.length?m.data.map(x=>`<div class="userrow">${esc(x.name)} (${esc(x.student_id)}) ${canManage(p)?`<button class="danger" data-remove="${esc(x.student_id)}">ลบ</button>`:''}</div>`).join(''):'<p class="muted">ยังไม่มีสมาชิก</p>';
  el('progressList').innerHTML=pr.data.length?pr.data.map(x=>`<div class="historyitem progress-record"><div><strong>${x.percent}%</strong> — ${esc(x.note)}<br><small class="muted">โดย ${esc(x.created_by)} · ${esc(x.created_at)}</small></div>${(canManage(p)||(canEdit(p)&&x.created_by===me.student_id))?`<button class="ghost" data-progress-edit="${x.id}">แก้ไข</button>`:""}</div>`).join(''):'<p class="muted">ยังไม่มีบันทึก</p>';
  el('progressList').querySelectorAll('[data-progress-edit]').forEach(b=>b.onclick=()=>{
    const record=pr.data.find(x=>x.id===Number(b.dataset.progressEdit));if(!record)return;
    el('progressEditNote').value=record.note;el('progressEditPercent').value=record.percent;
    el('progressEditModal').hidden=false;
    el('progressEditForm').onsubmit=async e=>{e.preventDefault();try{
      await api('/api/projects/'+id+'/progress/'+record.id,'PUT',{note:el('progressEditNote').value.trim(),percent:Number(el('progressEditPercent').value)});
      el('progressEditModal').hidden=true;toast('แก้ไขความก้าวหน้าสำเร็จ');await loadDetail();await refresh()
    }catch(err){toast(err.message)}};
  });
  if(canManage(p)){
   el('memberSelect').innerHTML=people.filter(x=>x.role==='student'&&!m.data.some(z=>z.student_id===x.student_id)).map(x=>`<option value="${esc(x.student_id)}">${esc(x.name)}</option>`).join('');
   el('addMember').disabled=!el('memberSelect').options.length;
   el('addMember').onclick=async()=>{try{await api('/api/projects/'+id+'/members','POST',{student_id:el('memberSelect').value});toast('เพิ่มสมาชิกแล้ว');await loadDetail();await refresh()}catch(e){toast(e.message)}};
   el('memberList').querySelectorAll('[data-remove]').forEach(b=>b.onclick=async()=>{try{await api('/api/projects/'+id+'/members/'+encodeURIComponent(b.dataset.remove),'DELETE');toast('ลบสมาชิกแล้ว');await loadDetail();await refresh()}catch(e){toast(e.message)}});
  }
 }
 await loadDetail();
 if(canEdit(p))el('progressForm').onsubmit=async e=>{e.preventDefault();try{await api('/api/projects/'+id+'/progress','POST',{note:el('progressNote').value,percent:Number(el('progressPercent').value)});el('progressNote').value='';toast('บันทึกความก้าวหน้าแล้ว');await loadDetail();await refresh()}catch(err){toast(err.message)}};
}
boot();

el('profileForm').onsubmit=async e=>{e.preventDefault();try{let r=await api('/api/profile','PUT',{name:el('profileNameInput').value.trim()});me=r.user;toast('อัปเดตชื่อเรียบร้อย');closeProfile();await refresh()}catch(err){toast(err.message)}};
el('avatarForm').onsubmit=async e=>{e.preventDefault();let file=el('avatarInput').files[0];if(!file)return;if(file.size>2*1024*1024){toast('รูปต้องไม่เกิน 2 MB');return}let fd=new FormData();fd.append('avatar',file);try{let r=await fetch('/api/profile/avatar',{method:'POST',credentials:'same-origin',headers:{'X-CSRF-Token':csrf},body:fd});let data=await r.json();if(!r.ok)throw Error(data.error||'อัปโหลดไม่สำเร็จ');me=data.user;el('avatarInput').value='';toast('เปลี่ยนรูปโปรไฟล์แล้ว');closeProfile();await refresh()}catch(err){toast(err.message)}};

let chatTarget=null;
async function openChat(){
 el('chatModal').hidden=false;
 try{const r=await api('/api/chat/contacts');el('chatContacts').innerHTML=r.data.length?r.data.map(u=>`<button class="ghost contact" data-contact="${esc(u.student_id)}">${esc(u.name)} <small>(${esc(u.role)})</small></button>`).join(''):'<p class="muted">ยังไม่มีผู้ติดต่อที่ได้รับอนุญาต</p>';
 el('chatContacts').querySelectorAll('[data-contact]').forEach(b=>b.onclick=()=>selectChat(b.dataset.contact,b.textContent));
 }catch(e){toast(e.message)}
}
async function selectChat(id,name){chatTarget=id;el('chatTitle').textContent=name;await loadChat()}
async function loadChat(){if(!chatTarget)return;try{let r=await api('/api/chat/'+encodeURIComponent(chatTarget));el('chatMessages').innerHTML=r.data.length?r.data.map(m=>`<div class="bubble ${m.sender_id===me.student_id?'mine':''}"><div>${esc(m.body)}</div><small>${esc(m.created_at)}</small></div>`).join(''):'<p class="muted">เริ่มส่งข้อความได้เลย</p>';el('chatMessages').scrollTop=el('chatMessages').scrollHeight}catch(e){toast(e.message)}}
el('chatForm').onsubmit=async e=>{e.preventDefault();if(!chatTarget)return toast('เลือกผู้ติดต่อก่อน');try{await api('/api/chat/'+encodeURIComponent(chatTarget),'POST',{body:el('chatInput').value});el('chatInput').value='';await loadChat();toast('ส่งข้อความแล้ว')}catch(e){toast(e.message)}};
