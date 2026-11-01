/* Multi-page navigation and project board */
let activeBoard=null,newsItems=[];
const viewNames=['dashboard','projects','announcements','history'];
function navigate(view){
 if(!me){showAuth();return}
 if(!viewNames.includes(view))view='dashboard';
 for(const name of viewNames){const id=name==='history'?'historyPage':name;const node=el(id);if(node)node.hidden=name!==view}
 document.querySelectorAll('[data-view]').forEach(a=>a.classList.toggle('active',a.dataset.view===view));
 history.replaceState(null,'','#'+view);window.scrollTo({top:0,behavior:'smooth'});
}
function announcementCard(a){
 const maintenance=a.kind==='maintenance';
 return `<article class="news-card">${a.image?`<img loading="lazy" src="/media/${encodeURIComponent(a.image)}" alt="ภาพประกอบประกาศ">`:'<div class="news-placeholder"><span>UNIVERSITY</span><strong>ACADEMIC NEWS</strong></div>'}<div class="news-body"><small>${maintenance?'ประกาศปรับปรุงระบบ':'ข่าวประชาสัมพันธ์'} · ${esc(a.created_at)}</small><h3>${esc(a.title)}</h3><p>${esc(a.body)}</p></div></article>`;
}
async function loadAnnouncements(){
 if(!me)return;
 try{const result=await api('/api/announcements');newsItems=result.data;
  const placeholders=Array.from({length:Math.max(0,3-newsItems.length)},(_,i)=>({title:['ข่าวสารและประกาศมหาวิทยาลัย','การติดตามความก้าวหน้าโครงงาน','บริการสำหรับนักศึกษาและอาจารย์'][i],body:'รอผู้ดูแลระบบเผยแพร่ประกาศและภาพประกอบ',created_at:'',kind:'news',image:null}));
  el('announcementPreview').innerHTML=[...newsItems.slice(0,3),...placeholders].slice(0,3).map(announcementCard).join('');
  el('announcementList').innerHTML=newsItems.length?newsItems.map(announcementCard).join(''):'<p class="muted">ยังไม่มีประกาศจากผู้ดูแลระบบ</p>';
  const notices=newsItems.filter(x=>x.kind==='maintenance').slice(0,1);
  const banner=el('systemNotice');if(banner){banner.hidden=!notices.length;if(notices.length)banner.textContent='แจ้งจากผู้ดูแลระบบ: '+notices[0].title}
 }catch(e){toast(e.message)}
}
function initCampus(){
 const dash=el('dashboard'),projects=el('projects');
 const metrics=projects.querySelector('.metrics');if(metrics)dash.appendChild(metrics);
 const side=projects.querySelector('.side');if(side){const section=document.createElement('section');section.className='panel stats-panel';section.innerHTML='<h2>สถิติโครงงาน</h2>';section.appendChild(side);dash.appendChild(section)}
 const banner=document.createElement('div');banner.id='systemNotice';banner.className='system-notice';banner.hidden=true;dash.prepend(banner);
 document.querySelectorAll('[data-view]').forEach(a=>a.addEventListener('click',e=>{e.preventDefault();navigate(a.dataset.view)}));
 const nav=location.hash.replace('#','');navigate(viewNames.includes(nav)?nav:'dashboard');
 const observer=new MutationObserver(()=>{if(me && !el('workspace').hidden){loadAnnouncements();observer.disconnect()}});
 observer.observe(el('workspace'),{attributes:true,attributeFilter:['hidden']});
}
const originalRefresh=refresh;
refresh=async function(){await originalRefresh();await loadAnnouncements()};
const originalShowAuth=showAuth;
showAuth=function(){originalShowAuth();el('boardModal').hidden=true};
const oldRenderProjects=renderProjects;
renderProjects=function(){oldRenderProjects();el('projectList').querySelectorAll('.project').forEach(card=>{
 const btn=card.querySelector('[data-detail]');if(!btn)return;
 const id=Number(btn.dataset.detail);btn.textContent='เปิดกระดานโครงงาน';btn.onclick=()=>openBoard(id);
 })};
function closeBoard(){el('boardModal').hidden=true;activeBoard=null}
async function openBoard(id){
 if(!me){toast('กรุณาเข้าสู่ระบบก่อน');return}
 activeBoard=id;const p=all.find(x=>x.id===id);if(!p)return;
 el('boardTitle').textContent=p.title;el('boardSubtitle').textContent=`ปีการศึกษา ${p.academic_year} • อาจารย์ที่ปรึกษา ${p.advisor_name||'ยังไม่กำหนด'}`;
 el('postForm').hidden=!canEdit(p);el('boardModal').hidden=false;await loadBoard();
}
async function loadBoard(){
 if(activeBoard===null)return;
 const id=activeBoard,p=all.find(x=>x.id===id);
 try{const {data}=await api(`/api/projects/${id}/posts`);
 el('boardFeed').innerHTML=data.length?data.map(post=>`<article class="board-post"><div class="post-meta"><strong>${esc(post.author_name)}</strong><small>${esc(post.created_at)}</small>${(canManage(p)||(canEdit(p)&&post.author_id===me.student_id))?`<button class="danger" data-remove-post="${post.id}">ลบอัปเดต</button>`:''}</div><p>${esc(post.body)}</p>${post.image?`<img class="post-photo" loading="lazy" src="/media/${encodeURIComponent(post.image)}" alt="รูปภาพอัปเดตโครงงาน">`:''}<div class="comments"><h4>ความคิดเห็น (${post.comments.length})</h4>${post.comments.map(c=>`<div class="comment"><span><b>${esc(c.author_name)}</b> ${esc(c.body)}</span>${(canManage(p)||c.author_id===me.student_id)?`<button class="ghost" data-remove-comment="${post.id}:${c.id}">ลบ</button>`:''}</div>`).join('')}<form class="comment-form" data-post="${post.id}"><input name="body" maxlength="1000" required placeholder="เขียนความคิดเห็น..."><button class="primary">ส่ง</button></form></div></article>`).join(''):'<div class="empty-board">ยังไม่มีการอัปเดตโครงงาน เริ่มโพสต์ความก้าวหน้าและรูปภาพได้เลย</div>';
 el('boardFeed').querySelectorAll('[data-remove-post]').forEach(b=>b.onclick=async()=>{if(!confirm('ยืนยันลบอัปเดตนี้และความคิดเห็นทั้งหมด?'))return;try{await api(`/api/projects/${id}/posts/${b.dataset.removePost}`,'DELETE');toast('ลบอัปเดตแล้ว');await loadBoard()}catch(e){toast(e.message)}});
 el('boardFeed').querySelectorAll('[data-remove-comment]').forEach(b=>b.onclick=async()=>{const [post,cid]=b.dataset.removeComment.split(':');try{await api(`/api/projects/${id}/posts/${post}/comments/${cid}`,'DELETE');await loadBoard()}catch(e){toast(e.message)}});
 el('boardFeed').querySelectorAll('.comment-form').forEach(f=>f.onsubmit=async e=>{e.preventDefault();try{await api(`/api/projects/${id}/posts/${f.dataset.post}/comments`,'POST',{body:f.elements.body.value.trim()});await loadBoard()}catch(e){toast(e.message)}});
 }catch(e){toast(e.message)}
}
el('postForm').onsubmit=async e=>{e.preventDefault();if(activeBoard===null)return;
 const file=el('postImage').files[0];if(file&&file.size>5*1024*1024){toast('รูปภาพต้องไม่เกิน 5 MB');return}
 const fd=new FormData();fd.append('body',el('postBody').value.trim());if(file)fd.append('image',file);
 const button=e.currentTarget.querySelector('button[type=submit],button.primary');button.disabled=true;
 try{const r=await fetch(`/api/projects/${activeBoard}/posts`,{method:'POST',credentials:'same-origin',headers:{'X-CSRF-Token':csrf},body:fd});const data=await r.json();if(!r.ok)throw Error(data.error||'บันทึกไม่สำเร็จ');el('postForm').reset();toast('เผยแพร่อัปเดตแล้ว');await loadBoard()}catch(err){toast(err.message)}finally{button.disabled=false}
};
// Move nested progress-edit dialog to topmost layer: fixes modal being hidden behind project details.
const progressEdit=el('progressEditModal');progressEdit.style.zIndex='2000';
const details=el('detailModal');details.style.zIndex='1000';
initCampus();
