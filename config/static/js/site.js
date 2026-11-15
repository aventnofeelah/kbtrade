(() => {
  const dialog = document.querySelector('#listing-dialog');
  const content = document.querySelector('#dialog-content');
  let lastTrigger = null;

  function setupForm(root) {
    const form = root.querySelector('[data-listing-form]');
    if (!form || form.dataset.initialized) return;
    form.dataset.initialized = 'true';
    const kind = form.elements.kind;
    const category = form.elements.category;
    const categories = JSON.parse(root.querySelector('#listing-categories').textContent);
    const photo = form.elements.image;
    const preview = form.querySelector('.photo-preview');
    const existingPhoto = preview.getAttribute('src');
    let previewUrl = null;
    const toggle = (selector, enabled) => {
      form.querySelectorAll(selector).forEach(group => {
        group.hidden = !enabled;
        group.querySelectorAll('input, select').forEach(field => {
          field.disabled = !enabled;
          field.required = enabled;
        });
      });
    };
    function updateType() {
      const sale = kind.value === 'sale';
      const selected = category.value;
      category.replaceChildren(new Option('Choose a category', ''));
      categories.filter(item => item.section === (sale ? 'market' : 'lostfound')).forEach(item => {
        category.add(new Option(item.name, item.id, false, String(item.id) === selected));
      });
      toggle('[data-sale-fields]', sale);
      toggle('[data-lost-fields]', !sale);
      form.elements.location.required = !sale;
      if (form.elements.status) {
        const status = form.elements.status.value;
        const options = sale ? [['active', 'Available'], ['sold', 'Sold']] : [['open', 'Open'], ['resolved', 'Resolved']];
        form.elements.status.replaceChildren(...options.map(([value, label]) => new Option(label, value, false, value === status)));
      }
    }
    kind.addEventListener('change', updateType);
    updateType();
    photo.addEventListener('change', () => {
      photo.setCustomValidity('');
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      const file = photo.files[0];
      if (file && file.size > 5 * 1024 * 1024) {
        photo.setCustomValidity('Please choose a photo smaller than 5 MB.');
        photo.reportValidity();
        preview.hidden = true;
        return;
      }
      if (file) {
        previewUrl = URL.createObjectURL(file);
        preview.src = previewUrl;
        preview.hidden = false;
        if (form.elements.remove_image) form.elements.remove_image.checked = false;
      } else {
        preview.hidden = !existingPhoto;
        if (existingPhoto) preview.src = existingPhoto;
      }
    });
    if (form.elements.remove_image) {
      form.elements.remove_image.addEventListener('change', event => {
        preview.hidden = event.target.checked || !preview.getAttribute('src');
        if (event.target.checked) photo.value = '';
      });
    }
  }

  setupForm(document);
  document.addEventListener('click', async event => {
    const trigger = event.target.closest('a[data-modal]');
    if (!trigger || !dialog || !dialog.showModal || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    lastTrigger = trigger;
    const url = new URL(trigger.href);
    url.searchParams.set('modal', '1');
    try {
      const response = await fetch(url, {headers: {'X-Requested-With': 'XMLHttpRequest'}});
      if (response.redirected) { window.location.href = response.url; return; }
      if (!response.ok) throw new Error('Unable to load form');
      content.innerHTML = await response.text();
      setupForm(content);
      dialog.showModal();
      document.body.classList.add('modal-open');
    } catch {
      window.location.href = trigger.href;
    }
  });
  dialog?.querySelector('.dialog-close').addEventListener('click', () => dialog.close());
  dialog?.addEventListener('close', () => {
    document.body.classList.remove('modal-open');
    content.replaceChildren();
    lastTrigger?.focus();
  });
  dialog?.addEventListener('click', event => {
    if (event.target === dialog) {
      const bounds = dialog.getBoundingClientRect();
      if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
    }
  });
  content?.addEventListener('submit', async event => {
    const form = event.target.closest('[data-listing-form]');
    if (!form) return;
    event.preventDefault();
    const button = form.querySelector('[type=submit]');
    const label = button.textContent;
    button.disabled = true;
    button.textContent = 'Saving…';
    const url = new URL(form.action);
    url.searchParams.set('modal', '1');
    try {
      const response = await fetch(url, {method: 'POST', body: new FormData(form), headers: {'X-Requested-With': 'XMLHttpRequest'}});
      if (response.redirected) { window.location.href = response.url; return; }
      if (!response.ok) throw new Error('Unable to save');
      content.innerHTML = await response.text();
      setupForm(content);
      // Browsers intentionally do not repopulate file inputs after a server response.
      if (form.elements.image.files.length) {
        const notice = document.createElement('p');
        notice.className = 'notice';
        notice.textContent = 'Please choose your photo again after correcting the fields below.';
        content.prepend(notice);
      }
      const invalid = content.querySelector('.errorlist');
      invalid?.scrollIntoView({block: 'center'});
      content.querySelector('input, select')?.focus();
    } catch {
      let error = form.querySelector('[data-network-error]');
      if (!error) {
        error = document.createElement('p');
        error.dataset.networkError = 'true';
        error.className = 'errorlist';
        error.setAttribute('role', 'alert');
        form.append(error);
      }
      error.textContent = 'Could not confirm the save. Please check My listings before trying again.';
      button.disabled = false;
      button.textContent = label;
    }
  });
})();
