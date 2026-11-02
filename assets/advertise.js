(function(){
 const form=document.getElementById('advertiserForm');if(!form)return;
 const box=document.getElementById('adMessage'),btn=document.getElementById('adSubmit');
 const cfg=window.JOBLINK_CONFIG||{};
 function message(t,err){box.hidden=false;box.className='ad-msg'+(err?' error':'');box.textContent=t;}
 form.addEventListener('submit',async e=>{e.preventDefault();if(!window.supabase||!cfg.SUPABASE_URL||!cfg.SUPABASE_ANON_KEY){message('The enquiry form is temporarily unavailable. Please email joblinkafrica@zohomail.com.',true);return}
 const f=new FormData(form),row=Object.fromEntries(f.entries());row.business_name=row.business_name.trim();row.contact_name=row.contact_name.trim();row.email=row.email.trim();row.phone=row.phone.trim();row.website=row.website.trim();row.message=row.message.trim();
 if(row.website&&!/^https:\/\//i.test(row.website)){message('Please enter a website address beginning with https://.',true);return}
 btn.disabled=true;btn.textContent='Sending…';
 try{const client=window.supabase.createClient(cfg.SUPABASE_URL,cfg.SUPABASE_ANON_KEY);const {error}=await client.from('advertiser_requests').insert(row);if(error)throw error;form.reset();message('Thank you. Your advertising enquiry has been received. We will contact you to discuss next steps.')}
 catch(err){message('We could not submit your enquiry. Please email joblinkafrica@zohomail.com. '+(err.message||''),true)}
 finally{btn.disabled=false;btn.textContent='Send advertising enquiry'}
 });
})();