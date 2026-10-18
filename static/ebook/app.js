(() => {
  const CATALOG_CACHE_KEY = 'nextgen-ebook-catalog-v1';
  const SAVED_BOOKS_KEY = 'nextgen-ebook-saved-v1';
  const grid = document.getElementById('book-grid');
  const search = document.getElementById('book-search');
  const emptyState = document.getElementById('empty-state');
  const offlineBanner = document.getElementById('offline-banner');
  const installDialog = document.getElementById('install-dialog');
  const installInstructions = document.getElementById('install-instructions');
  const toast = document.getElementById('toast');
  let catalog = [];
  let installPrompt = null;
  let toastTimeout = 0;

  function readSavedBooks() {
    try {
      const values = JSON.parse(localStorage.getItem(SAVED_BOOKS_KEY) || '[]');
      return new Set(Array.isArray(values) ? values.map(String) : []);
    } catch {
      return new Set();
    }
  }

  function writeSavedBooks(saved) {
    try {
      localStorage.setItem(SAVED_BOOKS_KEY, JSON.stringify([...saved]));
      return true;
    } catch {
      showToast('This browser could not save your library on this device.');
      return false;
    }
  }

  function showToast(message) {
    toast.textContent = message;
    toast.classList.add('visible');
    window.clearTimeout(toastTimeout);
    toastTimeout = window.setTimeout(() => toast.classList.remove('visible'), 3000);
  }

  function makeBookCard(book, saved) {
    const card = document.createElement('article');
    card.className = 'book-card';

    const art = document.createElement('div');
    art.className = 'book-art';
    art.setAttribute('aria-hidden', 'true');
    const badge = document.createElement('span');
    badge.className = 'book-badge';
    badge.textContent = book.badge || 'Digital guide';
    const miniBook = document.createElement('div');
    miniBook.className = 'mini-book';
    const brand = document.createElement('span');
    brand.className = 'mini-brand';
    brand.textContent = 'NEXTGEN TECH NOTES';
    const coverTitle = document.createElement('strong');
    coverTitle.textContent = book.title;
    const imprint = document.createElement('small');
    imprint.textContent = 'PRACTICAL DEVELOPER GUIDE';
    miniBook.append(brand, coverTitle, imprint);
    art.append(badge, miniBook);

    const info = document.createElement('div');
    info.className = 'book-info';
    const title = document.createElement('h3');
    title.className = 'book-title';
    title.textContent = book.title;
    const description = document.createElement('p');
    description.className = 'book-description';
    description.textContent = book.description || 'A practical digital guide from NextGen Tech Notes.';
    const price = document.createElement('p');
    price.className = 'book-price';
    price.textContent = book.price || 'View current price';

    const actions = document.createElement('div');
    actions.className = 'book-actions';
    const buy = document.createElement('a');
    buy.className = 'button button-primary';
    buy.href = book.url;
    buy.target = '_blank';
    buy.rel = 'noopener noreferrer';
    buy.textContent = 'View & get the book ↗';
    buy.setAttribute('aria-label', `Open seller checkout for ${book.title}`);

    const save = document.createElement('button');
    save.className = 'button save-button';
    save.type = 'button';
    save.setAttribute('aria-pressed', String(saved.has(String(book.id))));
    save.textContent = saved.has(String(book.id)) ? '✓ Saved' : '＋ Save';
    save.addEventListener('click', () => {
      const current = readSavedBooks();
      const id = String(book.id);
      if (current.has(id)) {
        current.delete(id);
        save.setAttribute('aria-pressed', 'false');
        save.textContent = '＋ Save';
        showToast('Removed from your saved books.');
      } else {
        current.add(id);
        save.setAttribute('aria-pressed', 'true');
        save.textContent = '✓ Saved';
        showToast('Saved on this device.');
      }
      writeSavedBooks(current);
    });
    actions.append(buy, save);
    info.append(title, description, price, actions);
    card.append(art, info);
    return card;
  }

  function renderCatalog() {
    const query = (search.value || '').trim().toLocaleLowerCase();
    const saved = readSavedBooks();
    const filtered = catalog.filter((book) => {
      const searchable = `${book.title} ${book.description} ${book.badge}`.toLocaleLowerCase();
      return searchable.includes(query);
    });
    grid.replaceChildren(...filtered.map((book) => makeBookCard(book, saved)));
    emptyState.hidden = filtered.length > 0;
  }

  function validCatalog(payload) {
    if (!payload || !Array.isArray(payload.products)) return [];
    return payload.products.filter((book) =>
      book && Number.isInteger(book.id) && typeof book.title === 'string' &&
      typeof book.url === 'string' && book.url.startsWith('https://')
    );
  }

  async function loadCatalog() {
    try {
      const response = await fetch('/api/ebook/catalog', { cache: 'no-store' });
      if (!response.ok) throw new Error(`Catalog request failed (${response.status}).`);
      const books = validCatalog(await response.json());
      catalog = books;
      try {
        localStorage.setItem(CATALOG_CACHE_KEY, JSON.stringify(books));
      } catch {
        // The service worker also caches the successful catalog response.
      }
    } catch {
      try {
        catalog = validCatalog({ products: JSON.parse(localStorage.getItem(CATALOG_CACHE_KEY) || '[]') });
      } catch {
        catalog = [];
      }
      offlineBanner.hidden = !navigator.onLine || catalog.length === 0;
      if (!catalog.length) {
        grid.replaceChildren();
        emptyState.hidden = false;
        emptyState.querySelector('h3').textContent = 'Library unavailable';
        emptyState.querySelector('p').textContent = 'Connect to the internet once to load the book catalog.';
        return;
      }
    }
    renderCatalog();
  }

  function isAppleMobile() {
    return /iPhone|iPad|iPod/i.test(navigator.userAgent) ||
      (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  }

  function isRunningInstalled() {
    return window.matchMedia('(display-mode: standalone)').matches || navigator.standalone === true;
  }

  function openInstallHelp() {
    const apple = isAppleMobile();
    installInstructions.replaceChildren();
    const intro = document.createElement('p');
    intro.className = 'section-subtitle';
    intro.textContent = apple
      ? 'Install from Safari to add NextGen Books to your Home Screen.'
      : 'Add NextGen Books to your Home Screen for a dedicated app icon and an offline-ready catalog.';
    const steps = document.createElement('ol');
    steps.className = 'install-steps';
    const text = apple
      ? ['Open this page in Safari.', 'Tap the Share button at the bottom of the screen.', 'Choose “Add to Home Screen”, then tap Add.']
      : ['Open the browser menu (⋮) or use the Install app button when offered.', 'Choose “Install app” or “Add to Home screen”.', 'Confirm. The app icon will appear with your other apps.'];
    text.forEach((step) => {
      const item = document.createElement('li');
      item.textContent = step;
      steps.appendChild(item);
    });
    installInstructions.append(intro, steps);
    if (!installDialog.open) installDialog.showModal();
  }

  async function installApp() {
    if (!installPrompt) {
      openInstallHelp();
      return;
    }
    installPrompt.prompt();
    await installPrompt.userChoice;
    installPrompt = null;
    document.querySelectorAll('.install-button').forEach((button) => {
      button.textContent = 'How to install';
    });
  }

  search.addEventListener('input', renderCatalog);
  document.querySelectorAll('.install-button').forEach((button) => {
    button.addEventListener('click', installApp);
  });
  document.getElementById('close-install-dialog').addEventListener('click', () => installDialog.close());
  document.getElementById('done-install-dialog').addEventListener('click', () => installDialog.close());
  installDialog.addEventListener('click', (event) => {
    if (event.target === installDialog) installDialog.close();
  });
  document.getElementById('current-year').textContent = new Date().getFullYear();
  if (isRunningInstalled()) {
    document.querySelectorAll('.install-button').forEach((button) => {
      button.hidden = true;
    });
  }

  window.addEventListener('beforeinstallprompt', (event) => {
    event.preventDefault();
    installPrompt = event;
    if (!isRunningInstalled()) {
      document.querySelectorAll('.install-button').forEach((button) => {
        button.textContent = 'Install app';
      });
    }
  });
  window.addEventListener('appinstalled', () => {
    installPrompt = null;
    document.querySelectorAll('.install-button').forEach((button) => {
      button.hidden = true;
    });
    showToast('NextGen Books was added to your device.');
  });
  window.addEventListener('online', () => {
    offlineBanner.hidden = true;
    loadCatalog();
  });
  window.addEventListener('offline', () => {
    if (catalog.length) offlineBanner.hidden = false;
  });

  if ('serviceWorker' in navigator && window.isSecureContext) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/ebook/service-worker.js', { scope: '/ebook/' }).catch(() => {
        showToast('Offline caching is unavailable in this browser session.');
      });
    });
  }

  loadCatalog();
})();
