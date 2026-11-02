/* JobLink Africa public listings. Uses Supabase when configured; otherwise displays clearly labelled demo data. */
const categories = [
  {name:'Technology & ICT', icon:'⌘'}, {name:'Healthcare & Medical',icon:'✚'}, {name:'Education & Teaching',icon:'▤'},
  {name:'Business, Finance & Administration',icon:'▥'}, {name:'Engineering & Construction',icon:'⚙'}, {name:'Hospitality & Tourism',icon:'⌂'},
  {name:'Transport & Logistics',icon:'↗'}, {name:'Sales & Marketing',icon:'◎'}, {name:'Customer Service & Call Centre',icon:'☏'},
  {name:'NGO & Development',icon:'♡'}, {name:'Government & Public Service',icon:'▦'}, {name:'Agriculture & Environment',icon:'♧'},
  {name:'Manufacturing & Skilled Trades',icon:'⚒'}, {name:'Legal & Compliance',icon:'⚖'}, {name:'Media, Design & Communications',icon:'✎'},
  {name:'Security & Safety',icon:'◇'}, {name:'Internships & Graduate Programmes',icon:'☆'}, {name:'Other',icon:'＋'}
];
const demoJobs = [
 {id:'demo-1',title:'DEMO: ICT Support Assistant',company:'Example Employer (Demo)',country:'Kenya',location:'Nairobi',category:'Technology & ICT',type:'Full-time',mode:'On-site',experience:'Entry level',salary:'Not provided',sponsor:false,featured:false,posted:'2026-10-20',deadline:'',source:'Demonstration only',url:'https://example.com/',description:'Fictional sample listing for layout demonstration only. It is not a real job vacancy.',requirements:'Replace with verified requirements.',status:'published',demo:true},
 {id:'demo-2',title:'DEMO: Customer Service Representative',company:'Sample Global Company (Demo)',country:'Remote / Worldwide',location:'Remote',category:'Customer Service & Call Centre',type:'Full-time',mode:'Remote',experience:'Entry level',salary:'Not provided',sponsor:false,featured:false,posted:'2026-10-18',deadline:'',source:'Demonstration only',url:'https://example.com/',description:'Fictional remote-job example for preview purposes. It is not an actual opening.',requirements:'Verify location and work eligibility with the employer.',status:'published',demo:true},
 {id:'demo-3',title:'DEMO: Graduate Engineering Trainee',company:'Sample Engineering Ltd (Demo)',country:'Australia',location:'Melbourne',category:'Engineering & Construction',type:'Graduate programme',mode:'On-site',experience:'Entry level',salary:'Not provided',sponsor:false,featured:false,posted:'2026-10-15',deadline:'',source:'Demonstration only',url:'https://example.com/',description:'Fictional example used to preview an international listing. No sponsorship is promised.',requirements:'Replace with verified requirements.',status:'published',demo:true},
 {id:'demo-4',title:'DEMO: Nursing Officer',company:'Sample Healthcare Provider (Demo)',country:'Kenya',location:'Nakuru',category:'Healthcare & Medical',type:'Contract',mode:'On-site',experience:'Mid level',salary:'Not provided',sponsor:false,featured:false,posted:'2026-10-12',deadline:'',source:'Demonstration only',url:'https://example.com/',description:'Fictional healthcare listing for design demonstration only.',requirements:'Replace with verified requirements.',status:'published',demo:true},
 {id:'demo-5',title:'DEMO: International Hospitality Team Member',company:'Example Hospitality Group (Demo)',country:'United Kingdom',location:'London',category:'Hospitality & Tourism',type:'Full-time',mode:'On-site',experience:'Any',salary:'Not provided',sponsor:false,featured:false,posted:'2026-10-10',deadline:'',source:'Demonstration only',url:'https://example.com/',description:'Fictional international opportunity. It does not indicate visa sponsorship.',requirements:'Verify work-rights rules with the employer.',status:'published',demo:true},
 {id:'demo-6',title:'DEMO: Finance Intern',company:'Sample Finance Organisation (Demo)',country:'Kenya',location:'Nairobi',category:'Business, Finance & Administration',type:'Internship',mode:'Hybrid',experience:'Entry level',salary:'Not provided',sponsor:false,featured:false,posted:'2026-10-08',deadline:'',source:'Demonstration only',url:'https://example.com/',description:'Fictional internship listing for demonstration only.',requirements:'Replace with verified vacancy details.',status:'published',demo:true}
];
const $ = id => document.getElementById(id); let jobs=[...demoJobs], page=1; const perPage=6; let usingCloud=false; let savedJobIds=JSON.parse(localStorage.getItem('joblink_saved_jobs')||'[]');
function esc(s=''){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function cloudClient(){const c=window.JOBLINK_CONFIG||{};if(!window.supabase||!c.SUPABASE_URL||c.SUPABASE_URL.includes('PASTE_')||!c.SUPABASE_ANON_KEY||c.SUPABASE_ANON_KEY.includes('PASTE_'))return null;try{return window.supabase.createClient(c.SUPABASE_URL,c.SUPABASE_ANON_KEY)}catch(e){return null}}
const client=cloudClient();
function mapJob(j){return {...j,sponsor:!!j.sponsor,featured:!!j.featured,demo:false,posted:j.posted||j.created_at?.slice(0,10)||'',deadline:j.deadline||'',salary:j.salary||'Not provided',source:j.source||'Employer website',description:j.description||'',requirements:j.requirements||''}}
async function loadJobs(){if(client){const {data,error}=await client.from('jobs').select('id,title,company,country,location,category,type,mode,experience,salary,sponsor,featured,posted,deadline,source,url,description,requirements,status').eq('status','published').order('featured',{ascending:false}).order('posted',{ascending:false});if(!error){jobs=(data||[]).map(mapJob).filter(j=>!j.deadline||j.deadline>=new Date().toISOString().slice(0,10));usingCloud=true;$('demoNotice').hidden=true;return}console.warn('JobLink cloud query failed; showing demo data.',error)}$('demoNotice').hidden=false;$('demoNotice').innerHTML='<b>Preview mode:</b> These fictional sample listings are for layout testing only. Configure Supabase in <code>assets/config.js</code> and publish verified vacancies from <a href="admin.html">the admin dashboard</a>.';}
function populateFilters(){const countrySel=$('country');[...new Set(jobs.map(j=>j.country).filter(Boolean))].sort().forEach(c=>countrySel.add(new Option(c,c)));categories.forEach(c=>$('category').add(new Option(c.name,c.name)));$('categoryGrid').innerHTML=categories.map(c=>`<a class="category-card" href="#jobs" data-category="${esc(c.name)}"><span class="category-icon">${c.icon}</span><span>${esc(c.name)}</span><span class="cat-arrow">↗</span></a>`).join('');$('categoryGrid').querySelectorAll('[data-category]').forEach(a=>a.addEventListener('click',()=>{$('category').value=a.dataset.category;page=1;renderJobs()}));}
function filteredJobs(){const q=$('q').value.trim().toLowerCase(),country=$('country').value,category=$('category').value,type=$('type').value,mode=$('mode').value,sponsor=$('sponsor').checked,experience=$('experienceFilter')?.value||'',sort=$('sortJobs')?.value||'newest',savedOnly=$('savedOnly')?.checked||false;return jobs.filter(j=>{const hay=[j.title,j.company,j.location,j.country,j.category,j.description,j.requirements].join(' ').toLowerCase();const active=!(j.deadline&&j.deadline<new Date().toISOString().slice(0,10));return active&&(!q||hay.includes(q))&&(!country||j.country===country)&&(!category||j.category===category)&&(!type||j.type===type)&&(!mode||j.mode===mode)&&(!sponsor||j.sponsor)&&(!experience||String(j.experience||'').toLowerCase().includes(experience.toLowerCase()))&&(!savedOnly||savedJobIds.includes(String(j.id)))}).sort((a,b)=>sort==='oldest'?(a.posted||'').localeCompare(b.posted||''):sort==='title'?(a.title||'').localeCompare(b.title||''):Number(b.featured)-Number(a.featured)||(b.posted||'').localeCompare(a.posted||''));}
function renderJobs(){const found=filteredJobs(),pages=Math.max(1,Math.ceil(found.length/perPage));page=Math.min(page,pages);const shown=found.slice((page-1)*perPage,page*perPage);$('resultCount').textContent=`${found.length} listing${found.length===1?'':'s'}${usingCloud?'':' (sample data)'}`;$('jobList').innerHTML=shown.length?shown.map(j=>`<article class="job-card"><button class="save-job" data-save="${esc(j.id)}" aria-label="${savedJobIds.includes(String(j.id))?'Remove saved job':'Save job'}">${savedJobIds.includes(String(j.id))?'★':'☆'}</button><div class="avatar">${esc((j.company||'?').charAt(0).toUpperCase())}</div><div class="job-main"><div class="topline"><span class="tag">${esc(j.category)}</span>${j.featured?'<span class="tag featured">SPONSORED</span>':''}${j.demo?'<span class="tag demo-tag">DEMO ONLY</span>':''}<span class="posted">${esc(j.posted)}</span></div><h3><button data-open="${esc(j.id)}">${esc(j.title)}</button></h3><p class="company">${esc(j.company)}</p><div class="meta"><span>⌖ ${esc(j.location)}, ${esc(j.country)}</span><span>◷ ${esc(j.type)}</span><span>▣ ${esc(j.mode)}</span>${j.sponsor?'<span class="sponsor">Visa sponsorship indicated</span>':''}</div><p class="excerpt">${esc(j.description.slice(0,175))}${j.description.length>175?'…':''}</p><small class="source">Source: ${esc(j.source)}</small></div><button class="view" data-open="${esc(j.id)}" aria-label="View ${esc(j.title)}">↗</button></article>`).join(''):`<div class="empty"><h3>No jobs found</h3><p>Try changing your search terms or filters, or check back later.</p></div>`;
$('jobList').querySelectorAll('[data-save]').forEach(b=>b.addEventListener('click',()=>{const id=String(b.dataset.save);savedJobIds=savedJobIds.includes(id)?savedJobIds.filter(x=>x!==id):[...savedJobIds,id];localStorage.setItem('joblink_saved_jobs',JSON.stringify(savedJobIds));renderJobs()}));
$('jobList').querySelectorAll('[data-open]').forEach(b => {
  b.addEventListener('click', () => {
    const id = b.dataset.open;
    window.location.href = `job.html?id=${encodeURIComponent(id)}`;
  });
});
$('pagination').innerHTML=pages>1?`${page>1?'<button id="prev">← Previous</button>':''}<span>Page ${page} of ${pages}</span>${page<pages?'<button id="next">Next →</button>':''}`:'';if($('prev'))$('prev').onclick=()=>{page--;renderJobs()};if($('next'))$('next').onclick=()=>{page++;renderJobs()};}
function openJob(id){const j=jobs.find(x=>String(x.id)===String(id));if(!j)return;$('modalContent').innerHTML=`<span class="eyebrow">${esc(j.category)}</span><h2 id="modalTitle">${esc(j.title)}</h2><p class="company">${esc(j.company)}</p><div class="modal-meta"><span>⌖ ${esc(j.location)}, ${esc(j.country)}</span><span>${esc(j.type)}</span><span>${esc(j.mode)}</span><span>${esc(j.experience)}</span>${j.salary?`<span>${esc(j.salary)}</span>`:''}</div>${j.demo?'<div class="notice" style="margin-top:20px"><b>Demonstration listing:</b> Fictional sample content, not a verified vacancy.</div>':''}<h3>Job description</h3><p class="modal-text">${esc(j.description)}</p><h3>Requirements</h3><p class="modal-text">${esc(j.requirements)}</p><div class="apply-box"><div><b>Application source</b><p>${esc(j.source)} · Verify the vacancy independently.</p></div><a class="btn primary" href="${esc(j.url)}" target="_blank" rel="noopener noreferrer">Apply on source ↗</a></div>`;$('jobModal').hidden=false;document.body.style.overflow='hidden';$('modalClose').focus();}
function closeModal(){$('jobModal').hidden=true;document.body.style.overflow=''}
$('filters').addEventListener('submit', e => {
  e.preventDefault();
  page = 1;
  renderJobs();
  $('jobs').scrollIntoView({ behavior: 'smooth', block: 'start' });
});

$('q').addEventListener('input', () => {
  page = 1;
  renderJobs();
});['country','category','type','mode','sponsor','experienceFilter','sortJobs','savedOnly'].forEach(id=>{if($(id))$(id).addEventListener('change',()=>{page=1;renderJobs()})});$('clear').addEventListener('click',()=>{$('filters').reset();page=1;renderJobs()});$('modalClose').addEventListener('click',closeModal);$('jobModal').addEventListener('click',e=>{if(e.target===$('jobModal'))closeModal()});document.addEventListener('keydown',e=>{if(e.key==='Escape')closeModal()});$('year').textContent=new Date().getFullYear();
(async()=>{await loadJobs();populateFilters();renderJobs();initPhaseOne();})();


// Phase 1 additions: enhanced filters, saved jobs, alert preference capture and lightweight analytics.
function trackJoblinkEvent(eventType, jobId=''){
  if(!client)return;
  client.from('site_events').insert({event_type:eventType,job_id:jobId||null,page_path:location.pathname}).then(({error})=>{if(error)console.debug('Analytics event not recorded:',error.message)});
}
function initPhaseOne(){
  const form=$('filters');
  if(form&&!$('experienceFilter')){
    const extra=document.createElement('div');extra.className='phase1-filters';
    extra.innerHTML='<label>Experience level<select id="experienceFilter"><option value="">Any experience</option><option>Entry</option><option>Mid</option><option>Senior</option><option>Any</option></select></label><label>Sort listings<select id="sortJobs"><option value="newest">Newest first</option><option value="oldest">Oldest first</option><option value="title">Job title A–Z</option></select></label><label class="phase1-saved"><input id="savedOnly" type="checkbox"> Show saved jobs only</label>';
    form.appendChild(extra);
    ['experienceFilter','sortJobs','savedOnly'].forEach(id=>$(id).addEventListener('change',()=>{page=1;renderJobs()}));
  }
  const section=$('jobs');
  if(section&&!$('jobAlertPanel')){
    const panel=document.createElement('section');panel.id='jobAlertPanel';panel.className='job-alert-panel';
    panel.innerHTML='<div><span class="eyebrow">STAY INFORMED</span><h3>Get matched with new opportunities</h3><p>Choose your interests and submit your email to register for JobLink Africa job alerts. Email delivery will be activated when the notification service is connected.</p></div><form id="jobAlertForm"><input id="alertEmail" type="email" required maxlength="254" placeholder="Your email address"><select id="alertCountry"><option value="">Any country</option></select><select id="alertCategory"><option value="">Any category</option></select><button class="btn primary" type="submit">Register for alerts</button><small id="alertStatus" role="status"></small></form>';
    section.insertBefore(panel,$('jobList'));
    categories.forEach(c=>$('alertCategory').add(new Option(c.name,c.name)));
    [...new Set(jobs.map(j=>j.country).filter(Boolean))].sort().forEach(c=>$('alertCountry').add(new Option(c,c)));
    $('jobAlertForm').addEventListener('submit',async e=>{
      e.preventDefault();const status=$('alertStatus');status.textContent='Submitting…';
      if(!client){status.textContent='Alerts registration is unavailable while the database is disconnected.';return}
      const payload={email:$('alertEmail').value.trim().toLowerCase(),country:$('alertCountry').value,category:$('alertCategory').value,active:true};
      const {error}=await client.from('job_alert_subscriptions').insert(payload);
      status.textContent=error?(error.code==='23505'?'This email already has an alert registration.':'Could not register right now. Please try again later.'):'Your alert preferences have been registered. Email notifications are not active yet.';
      if(!error)$('jobAlertForm').reset();
    });
  }
  trackJoblinkEvent('page_view');
  document.addEventListener('click',e=>{const open=e.target.closest('[data-open]');if(open)trackJoblinkEvent('job_open',open.dataset.open)});
  if(!document.getElementById('savedJobStyles')){
    const style=document.createElement('style');style.id='savedJobStyles';style.textContent='.save-job{order:4;margin-left:auto;border:1px solid #dce5ec;background:#fff;border-radius:9px;width:36px;height:36px;color:#087e8b;font-size:21px;cursor:pointer}.phase1-filters{grid-column:1/-1;display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;align-items:end}.phase1-filters label{display:flex;flex-direction:column;gap:7px;font-size:11px;font-weight:800;color:#526579}.phase1-filters select{border:1px solid #dce5ec;border-radius:9px;padding:12px;background:#fff}.phase1-saved{flex-direction:row!important;align-items:center}.job-alert-panel{margin:25px 0;padding:22px;border:1px solid #dce8ec;border-radius:15px;background:#f5fbfa;display:grid;grid-template-columns:1fr 1.2fr;gap:22px}.job-alert-panel h3{margin:7px 0;font-size:20px}.job-alert-panel p,.job-alert-panel small{font-size:11px;color:#607587}.job-alert-panel form{display:grid;grid-template-columns:1fr 1fr;gap:9px;align-content:center}.job-alert-panel input,.job-alert-panel select{min-width:0;padding:11px;border:1px solid #dce5ec;border-radius:8px;background:#fff}.job-alert-panel button{grid-column:1/-1}.job-alert-panel small{grid-column:1/-1}@media(max-width:620px){.phase1-filters,.job-alert-panel,.job-alert-panel form{grid-template-columns:1fr}}';
    document.head.appendChild(style);
  }
}
