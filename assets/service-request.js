/* Public career-service request form. Uses only the Supabase publishable/anon key. */
(() => {
  const $ = id => document.getElementById(id);
  const config = window.JOBLINK_CONFIG || {};
  const form = $('serviceRequestForm');
  const message = $('formMessage');
  const submit = $('submitRequest');
  if (!form) return;
  const validConfig = window.supabase && config.SUPABASE_URL && config.SUPABASE_ANON_KEY &&
    !String(config.SUPABASE_URL).includes('PASTE_') && !String(config.SUPABASE_ANON_KEY).includes('PASTE_');
  if (!validConfig) {
    message.className = 'warning';
    message.textContent = 'The service request form is temporarily unavailable. Please try again later.';
    submit.disabled = true;
    return;
  }
  const client = window.supabase.createClient(config.SUPABASE_URL, config.SUPABASE_ANON_KEY);
  const allowedTypes = new Set(['application/pdf','application/msword','application/vnd.openxmlformats-officedocument.wordprocessingml.document']);
  form.addEventListener('submit', async event => {
    event.preventDefault();
    message.textContent = '';
    message.className = '';
    const file = $('cvFile').files[0] || null;
    if (file && (file.size > 5 * 1024 * 1024 || !allowedTypes.has(file.type))) {
      message.className = 'warning';
      message.textContent = 'Please upload a PDF or Word document no larger than 5 MB.';
      return;
    }
    const jobUrl = $('jobAdUrl').value.trim();
    if (jobUrl && !/^https:\/\//i.test(jobUrl)) {
      message.className = 'warning';
      message.textContent = 'Please use a secure https:// link for the job advert.';
      return;
    }
    submit.disabled = true;
    submit.textContent = 'Submitting request…';
    let storagePath = null;
    try {
      if (file) {
        const extension = file.name.toLowerCase().split('.').pop();
        storagePath = crypto.randomUUID() + '/cv.' + extension;
        const upload = await client.storage.from('career-service-cvs').upload(storagePath, file, {
          cacheControl: '0', upsert: false, contentType: file.type
        });
        if (upload.error) throw new Error('The CV file could not be uploaded. Please try again or submit the form without an attachment.');
      }
      const order = {
        customer_name: $('customerName').value.trim(),
        customer_email: $('customerEmail').value.trim(),
        customer_phone: $('customerPhone').value.trim(),
        service_type: $('serviceType').value,
        target_role: $('targetRole').value.trim(),
        target_country: $('targetCountry').value.trim() || 'Not specified',
        job_ad_url: jobUrl,
        instructions: $('instructions').value.trim(),
        delivery_method: $('deliveryMethod').value,
        cv_storage_path: storagePath,
        payment_status: 'pending',
        order_status: 'awaiting_payment'
      };
      const result = await client.from('service_orders').insert(order);
      if (result.error) throw result.error;
      form.reset();
      message.className = 'notice-success';
      message.textContent = 'Your service request has been received. We will contact you using the details you provided to confirm the service, payment instructions and delivery arrangements. No payment has been taken.';
      message.scrollIntoView({behavior:'smooth',block:'center'});
    } catch (error) {
      message.className = 'warning';
      message.textContent = error.message || 'We could not submit your request. Please check your details and try again.';
    } finally {
      submit.disabled = false;
      submit.textContent = 'Submit service request →';
    }
  });
})();
