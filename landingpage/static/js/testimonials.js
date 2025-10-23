// ======== TOAST =========
function showToast(message, variant='info', ms=3500){
  const stack = document.getElementById('toast-stack');
  if(!stack) return;
  const colors = {
    info:'bg-blue-600', success:'bg-emerald-600', error:'bg-rose-600', warning:'bg-amber-500'
  };
  const el = document.createElement('div');
  el.className = `pointer-events-auto ${colors[variant]||colors.info} text-white rounded-xl shadow-lg px-4 py-3 flex items-center gap-3 w-[min(360px,90vw)] opacity-0 -translate-y-2 transition-all duration-300`;
  el.innerHTML = `<span>${message}</span>`;
  stack.appendChild(el);
  requestAnimationFrame(()=>{ el.classList.remove('opacity-0','-translate-y-2'); el.classList.add('opacity-100','translate-y-0'); });
  setTimeout(()=>{ el.classList.add('opacity-0','-translate-y-2'); setTimeout(()=>el.remove(),300); },ms);
}

// helper escape
function esc(s){
  return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// ======== MAIN =========
document.addEventListener('DOMContentLoaded', function(){
  const EP = window.SPORTPEDIA_ENDPOINTS || {};
  const track   = document.getElementById('t-track');
  const prevBtn = document.getElementById('t-prev');
  const nextBtn = document.getElementById('t-next');
  const filters = document.getElementById('t-filters');

  const createBtn  = document.getElementById('t-share-btn');
  const createWrap = document.getElementById('t-create');
  const createClose= document.getElementById('t-create-close');
  const createForm = document.getElementById('t-create-form');

  const editWrap   = document.getElementById('t-edit');
  const editClose  = document.getElementById('t-edit-close');
  const editForm   = document.getElementById('t-edit-form');
  const editId     = document.getElementById('edit-id');
  const editText   = document.getElementById('edit-text');
  const editCat    = document.getElementById('edit-category');
  const editImg    = document.getElementById('edit-image');

  const csrftoken = document.cookie.match('(^|;)\\s*csrftoken\\s*=\\s*([^;]+)')?.pop() || '';

  const VISIBLE = 3;
  let groupIndex = 0, itemCount = 0, stepWidth = 0;

  function cardHTML(item){
    const img = item.image_url || "/static/images/placeholder.jpg";
    // tampilkan DESKRIPSI (text) sebagai konten utama
    const textHTML = esc(item.text || '').replace(/\n/g,'<br>');
    const owner = item.is_owner ? `
      <div class='mt-3 flex justify-center gap-2'>
        <button
          class='edit-btn bg-amber-500 text-white px-3 py-1 rounded'
          data-id='${item.id}'
          data-text='${(item.text||"").replace(/'/g,"&#39;")}'
          data-category='${item.category}'
        >Edit</button>
        <button class='delete-btn bg-rose-600 text-white px-3 py-1 rounded' data-id='${item.id}'>Delete</button>
      </div>` : '';
    return `<article class='testimonial-card'>
      <img src='${img}' class='w-full h-40 object-cover rounded-xl mb-3' alt='testimonial'>
      <div class='text-center p-2'>
        <p class='text-xs text-gray-500 uppercase tracking-wide'>${item.category}</p>
        <p class='mt-2 text-[15px] leading-relaxed text-gray-800 whitespace-pre-line'>${textHTML}</p>
        <p class='text-xs text-gray-500 mt-2'>— <strong>${esc(item.user)}</strong></p>
        ${owner}
      </div>
    </article>`;
  }

  function computeStepWidth(){
    const first = track.querySelector('.testimonial-card');
    if(!first){ stepWidth = 0; return; }
    const gap = parseFloat(getComputedStyle(track).gap) || 32;
    stepWidth = first.offsetWidth * VISIBLE + gap * (VISIBLE - 1);
  }

  function applyTransform(){
    track.style.transform = `translateX(${-groupIndex * stepWidth}px)`;
  }

  async function loadTestimonials(cat='all'){
    try{
      const url = `${EP.list}?limit=60&category=${encodeURIComponent(cat)}`;
      const res = await fetch(url);
      const json = await res.json();
      itemCount = json.items?.length || 0;

      if(itemCount === 0){
        track.innerHTML = `<p class="text-center w-full text-gray-500">Jadi orang pertama yang memberi testimoni Sportpedia!</p>`;
        prevBtn.classList.add('t-arrow-disabled');
        nextBtn.classList.add('t-arrow-disabled');
        return;
      }

      track.innerHTML = json.items.map(cardHTML).join('');
      computeStepWidth();
      groupIndex = 0;
      applyTransform();

      const maxGroup = Math.max(0, Math.ceil(itemCount / VISIBLE) - 1);
      prevBtn.classList.toggle('t-arrow-disabled', groupIndex <= 0);
      nextBtn.classList.toggle('t-arrow-disabled', groupIndex >= maxGroup);
    }catch(err){
      track.innerHTML = `<p class="text-center w-full text-red-500">Gagal memuat testimoni.</p>`;
    }
  }

  // Navigasi
  prevBtn.addEventListener('click', ()=>{
    if(groupIndex > 0){
      groupIndex--;
      applyTransform();
      const maxGroup = Math.max(0, Math.ceil(itemCount / VISIBLE) - 1);
      prevBtn.classList.toggle('t-arrow-disabled', groupIndex <= 0);
      nextBtn.classList.toggle('t-arrow-disabled', groupIndex >= maxGroup);
    }
  });
  nextBtn.addEventListener('click', ()=>{
    const maxGroup = Math.max(0, Math.ceil(itemCount / VISIBLE) - 1);
    if(groupIndex < maxGroup){
      groupIndex++;
      applyTransform();
      prevBtn.classList.toggle('t-arrow-disabled', groupIndex <= 0);
      nextBtn.classList.toggle('t-arrow-disabled', groupIndex >= maxGroup);
    }
  });
  window.addEventListener('resize', ()=>{
    computeStepWidth();
    applyTransform();
  });

  // Filter
  filters.addEventListener('click', (e)=>{
    if(!e.target.classList.contains('t-chip')) return;
    filters.querySelector('.active')?.classList.remove('active');
    e.target.classList.add('active');
    loadTestimonials(e.target.dataset.cat);
  });

  // load awal
  loadTestimonials('all');

  // ===== Create modal (tengah) =====
  createBtn?.addEventListener('click', ()=> createWrap.classList.remove('hidden'));
  createClose?.addEventListener('click', ()=> createWrap.classList.add('hidden'));
  createForm?.addEventListener('submit', async (e)=>{
    e.preventDefault();
    try{
      const fd = new FormData(createForm);
      // backend masih butuh title -> auto-generate dari awal deskripsi
      const text = (fd.get('text') || '').toString().trim();
      const autoTitle = text ? text.slice(0, 60) : 'Testimonial';
      fd.set('title', autoTitle);

      const res = await fetch(EP.create, {
        method:'POST',
        headers:{'X-CSRFToken': csrftoken},
        body: fd,
        credentials: 'same-origin'
      });
      if(!res.ok) throw new Error(await res.text());
      createWrap.classList.add('hidden');
      createForm.reset();
      const activeCat = document.querySelector('#t-filters .active')?.dataset.cat || 'all';
      await loadTestimonials(activeCat);
      showToast('✅ Testimoni berhasil ditambahkan!','info');
    }catch(err){
      showToast('Gagal menambah testimoni','error');
    }
  });

  // ===== Edit/Delete via delegation =====
  track.addEventListener('click', (e)=>{
    // DELETE
    const del = e.target.closest('.delete-btn');
    if(del){
      const id = del.dataset.id;
      if(!confirm('Hapus testimoni ini?')) return;
      fetch(`${EP.deleteBase}${id}/delete/`, {
        method:'POST', headers:{'X-CSRFToken': csrftoken}
      }).then(r=>{
        if(!r.ok) throw new Error();
        const activeCat = document.querySelector('#t-filters .active')?.dataset.cat || 'all';
        loadTestimonials(activeCat);
        showToast('🗑️ Testimoni dihapus','info');
      }).catch(()=> showToast('Gagal menghapus','error'));
      return;
    }

    // EDIT (open modal + prefill)
    const edit = e.target.closest('.edit-btn');
    if(edit){
      document.getElementById('edit-id').value     = edit.dataset.id;
      document.getElementById('edit-text').value   = edit.dataset.text || '';
      document.getElementById('edit-category').value = edit.dataset.category || 'library';
      const f = document.getElementById('edit-image'); if(f) f.value = '';
      editWrap.classList.remove('hidden');
    }
  });

  // ===== Edit modal submit =====
  editClose?.addEventListener('click', ()=> editWrap.classList.add('hidden'));
  editForm?.addEventListener('submit', async (e)=>{
    e.preventDefault();
    const id = editId.value;
    const fd = new FormData(editForm);
    // backend butuh title -> auto dari text
    const text = (fd.get('text') || '').toString().trim();
    const autoTitle = text ? text.slice(0, 60) : 'Testimonial';
    fd.set('title', autoTitle);

    try{
      const res = await fetch(`${EP.updateBase}${id}/update/`, {
        method:'POST',
        headers:{'X-CSRFToken': csrftoken},
        body: fd,
        credentials: 'same-origin'
      });
      if(!res.ok) throw new Error(await res.text());
      editWrap.classList.add('hidden');
      const activeCat = document.querySelector('#t-filters .active')?.dataset.cat || 'all';
      await loadTestimonials(activeCat);
      showToast('✏️ Testimoni berhasil diupdate','info');
    }catch(err){
      showToast('Gagal update testimoni','error');
    }
  });
});
