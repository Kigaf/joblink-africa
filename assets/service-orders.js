/* Admin-only career service order manager. */
(() => {
  const $ = id => document.getElementById(id);
  const config = window.JOBLINK_CONFIG || {};
  const panel = $('serviceOrdersPanel');
  if (!panel || !window.supabase || !config.SUPABASE_URL || !config.SUPABASE_ANON_KEY) return;
  const db = window.supabase.createClient(config.SUPABASE_URL, config.SUPABASE_ANON_KEY);
  const esc = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  let orders = [];
  const statuses = ['awaiting_payment','queued','in_progress','review','completed','cancelled'];
  const payments = ['pending','submitted','confirmed','rejected'];
  const label = value => value.replaceAll('_',' ');
  async function refresh() {
    const {data,error} = await db.from('service_orders').select('*').order('created_at',{ascending:false});
    if (error) { $('serviceOrderRows').innerHTML='<p class="muted">Could not load service orders. Check that the career-services SQL migration has been run and your admin access is active. '+esc(error.message)+'</p>'; return; }
    orders = data || [];
    render();
  }
  function render() {
    const host=$('serviceOrderRows');
    if (!orders.length) { host.innerHTML='<p class="muted">No career service requests have been received yet.</p>'; return; }
    host.innerHTML=orders.map(o=>`
      <article class="job-row" style="display:block">
        <div style="display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap">
          <div><h3>${esc(o.service_type)} · ${esc(o.customer_name)}</h3><p>${esc(o.customer_email)} · ${esc(o.customer_phone)} · ${esc(o.target_role)} · ${esc(o.target_country)}</p><p>Received: ${esc(new Date(o.created_at).toLocaleString())} · Delivery: ${esc(o.delivery_method)}</p></div>
          <div class="row-actions"><span class="status-pill status-${o.payment_status==='confirmed'?'published':'draft'}">Payment: ${esc(label(o.payment_status))}</span><span class="status-pill">Order: ${esc(label(o.order_status))}</span></div>
        </div>
        ${o.job_ad_url?`<p>Job advert: <a href="${esc(o.job_ad_url)}" target="_blank" rel="noopener noreferrer">Open vacancy link</a></p>`:''}
        ${o.instructions?`<p><b>Customer instructions:</b> ${esc(o.instructions)}</p>`:''}
        <div class="row-actions" style="justify-content:flex-start;margin:10px 0">
          ${o.cv_storage_path?'<button class="mini-btn" data-cv="'+esc(o.id)+'">Open private CV</button>':''}
          ${o.delivery_link?`<a class="mini-btn" href="${esc(o.delivery_link)}" target="_blank" rel="noopener noreferrer">Open delivery</a>`:''}
        </div>
        <div class="two-col" style="margin-top:10px">
          <label>Payment status<select data-payment="${esc(o.id)}">${payments.map(v=>'<option value="'+v+'" '+(o.payment_status===v?'selected':'')+'>'+label(v)+'</option>').join('')}</select></label>
          <label>Order status<select data-status="${esc(o.id)}">${statuses.map(v=>'<option value="'+v+'" '+(o.order_status===v?'selected':'')+'>'+label(v)+'</option>').join('')}</select></label>
        </div>
        <label style="display:block;margin-top:10px;font-size:11px;font-weight:800">Admin notes<textarea data-notes="${esc(o.id)}" rows="2" style="width:100%;padding:10px;border:1px solid #dce5ec;border-radius:8px">${esc(o.admin_notes)}</textarea></label>
        <label style="display:block;margin-top:10px;font-size:11px;font-weight:800">Delivery link (optional)<input data-delivery="${esc(o.id)}" type="url" value="${esc(o.delivery_link)}" placeholder="https://..." style="width:100%;padding:10px;border:1px solid #dce5ec;border-radius:8px"></label>
        <button class="mini-btn" data-save="${esc(o.id)}" style="margin-top:10px">Save order updates</button>
      </article>`).join('');
    host.querySelectorAll('[data-save]').forEach(button=>button.addEventListener('click',()=>save(button.dataset.save)));
    host.querySelectorAll('[data-cv]').forEach(button=>button.addEventListener('click',()=>openCv(button.dataset.cv)));
  }
  async function save(id) {
    const payment=$('serviceOrderRows').querySelector('[data-payment="'+id+'"]').value;
    const status=$('serviceOrderRows').querySelector('[data-status="'+id+'"]').value;
    const notes=$('serviceOrderRows').querySelector('[data-notes="'+id+'"]').value;
    const delivery=$('serviceOrderRows').querySelector('[data-delivery="'+id+'"]').value.trim();
    if(delivery && !/^https:\/\//i.test(delivery)){alert('Delivery link must start with https://');return;}
    const {error}=await db.from('service_orders').update({payment_status:payment,order_status:status,admin_notes:notes,delivery_link:delivery}).eq('id',id);
    if(error){alert('Could not save order: '+error.message);return;}
    await refresh();
    alert('Order updated.');
  }
  async function openCv(id) {
    const order=orders.find(item=>item.id===id);
    if(!order?.cv_storage_path)return;
    const {data,error}=await db.storage.from('career-service-cvs').createSignedUrl(order.cv_storage_path,300);
    if(error){alert('Could not open the private CV: '+error.message);return;}
    window.open(data.signedUrl,'_blank','noopener');
  }
  $('refreshServiceOrders').addEventListener('click',refresh);
  db.auth.onAuthStateChange((_event,session)=>{if(session)setTimeout(checkAdmin,0);else panel.hidden=true;});
  async function checkAdmin(){
    const {data,error}=await db.rpc('joblink_is_admin');
    if(error || data!==true){panel.hidden=true;return;}
    panel.hidden=false;
    refresh();
  }
  db.auth.getSession().then(({data})=>{if(data.session)checkAdmin();});
})();
