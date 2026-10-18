/**
 * NextGen Tech Notes — Autonomous AI Agentic Bot Controller
 * Mobile-First, Serverless Persistent OAuth, 1-Click Autopilot & Monetization Vault
 */

const state = {
  activeTab: 'tab-autopilot',
  currentArticle: {
    id: null,
    title: '',
    topic: '',
    keyword: '',
    markdown: '',
    renderedHtml: '',
    schema: {},
    featuredImageUrl: '',
    diagramImageUrl: '',
  },
  trendingPick: null,
  googleConnected: false,
  activeBlogId: '',
  products: [],
  affiliates: [],
};

const el = {
  // Navigation
  tabs: document.querySelectorAll('.nav-tab'),
  mobileTabs: document.querySelectorAll('.mobile-nav-item'),
  panes: document.querySelectorAll('.tab-pane'),
  toastContainer: document.getElementById('toast-container'),

  // Header & OAuth
  googleStatusPill: document.getElementById('google-status-pill'),
  googleIndicator: document.getElementById('google-indicator'),
  googleStatusText: document.getElementById('google-status-text'),
  connectGoogleBtn: document.getElementById('connect-google-btn'),
  oauthRedirectDisplay: document.getElementById('oauth-redirect-display'),
  btnCopyRedirect: document.getElementById('btn-copy-redirect'),
  btnLoginGoogleAlt: document.getElementById('btn-login-google-alt'),

  // Autopilot
  currentTrendingTitle: document.getElementById('current-trending-title'),
  trendingCategory: document.getElementById('trending-category'),
  trendingCpc: document.getElementById('trending-cpc'),
  btnShuffleTopic: document.getElementById('btn-shuffle-topic'),
  autopilotProvider: document.getElementById('autopilot-provider'),
  autopilotCustomTopic: document.getElementById('autopilot-custom-topic'),
  autopilotMonetizeType: document.getElementById('autopilot-monetize-type'),
  autopilotProductSelectGroup: document.getElementById('autopilot-product-select-group'),
  autopilotProductSelect: document.getElementById('autopilot-product-select'),
  autopilotAffiliateSelectGroup: document.getElementById('autopilot-affiliate-select-group'),
  autopilotAffiliateSelect: document.getElementById('autopilot-affiliate-select'),
  autopilotToggleBlogger: document.getElementById('autopilot-toggle-blogger'),
  btnRunAutopilot: document.getElementById('btn-run-autopilot'),
  autopilotSpinner: document.getElementById('autopilot-spinner'),
  autopilotResultCard: document.getElementById('autopilot-result-card'),
  autopilotResultBody: document.getElementById('autopilot-result-body'),
  btnOpenAutopilotInEditor: document.getElementById('btn-open-autopilot-in-editor'),

  // Rewriter
  rewriteBloggerSelect: document.getElementById('rewrite-blogger-select'),
  btnFetchBloggerPosts: document.getElementById('btn-fetch-blogger-posts'),
  rewriteTitle: document.getElementById('rewrite-title'),
  rewriteContent: document.getElementById('rewrite-content'),
  rewriteSpinner: document.getElementById('rewrite-spinner'),
  btnRunRewrite: document.getElementById('btn-run-rewrite'),
  rewriteResultBox: document.getElementById('rewrite-result-box'),
  rewriteActions: document.getElementById('rewrite-actions'),
  btnSendRewrittenToEditor: document.getElementById('btn-send-rewritten-to-editor'),

  // Custom Generator
  genForm: document.getElementById('generator-form'),
  genProvider: document.getElementById('gen-provider'),
  genModel: document.getElementById('gen-model'),
  genTopic: document.getElementById('gen-topic'),
  genKeyword: document.getElementById('gen-keyword'),
  genAudience: document.getElementById('gen-audience'),
  genNotes: document.getElementById('gen-notes'),
  genSpinner: document.getElementById('gen-spinner'),
  genBtn: document.getElementById('btn-run-generate'),
  genSummaryBox: document.getElementById('gen-summary-box'),
  genActions: document.getElementById('gen-actions'),
  btnSendToEditor: document.getElementById('btn-send-to-editor'),

  // Image Studio
  imgTopicInput: document.getElementById('img-topic-input'),
  btnAutoPrompt: document.getElementById('btn-auto-prompt'),
  imgPromptInput: document.getElementById('img-prompt-input'),
  btnGenerateImage: document.getElementById('btn-generate-image'),
  imgSpinner: document.getElementById('img-spinner'),
  imgDisplayContainer: document.getElementById('image-display-container'),
  imgActions: document.getElementById('image-actions'),
  btnInsertImageEditor: document.getElementById('btn-insert-image-editor'),

  // Editor
  editorTitle: document.getElementById('editor-title'),
  markdownEditor: document.getElementById('markdown-editor'),
  wordCountBadge: document.getElementById('word-count-badge'),
  toggleToc: document.getElementById('toggle-toc'),
  toggleEbook: document.getElementById('toggle-ebook'),
  btnRefreshPreview: document.getElementById('btn-refresh-preview'),
  btnSaveDb: document.getElementById('btn-save-db'),
  btnUploadBlogger: document.getElementById('btn-upload-blogger'),
  previewRendered: document.getElementById('preview-content-rendered'),
  previewHtml: document.getElementById('preview-content-html'),
  previewSchema: document.getElementById('preview-content-schema'),
  rawHtmlViewer: document.getElementById('raw-html-viewer'),
  rawSchemaViewer: document.getElementById('raw-schema-viewer'),
  qualityWarningsBanner: document.getElementById('quality-warnings-banner'),
  viewBtns: document.querySelectorAll('.view-btn'),

  // Products & Affiliates
  productForm: document.getElementById('product-form'),
  productsTableContainer: document.getElementById('products-table-container'),
  ebookLivePreview: document.getElementById('ebook-live-preview'),
  affiliateForm: document.getElementById('affiliate-form'),
  affTableContainer: document.getElementById('affiliates-table-container'),

  // Blogger & OAuth
  activeBlogSelector: document.getElementById('active-blog-selector'),
  btnRefreshBlogs: document.getElementById('btn-refresh-blogs'),
  bloggerPostsContainer: document.getElementById('blogger-posts-container'),
};

function showToast(message, type = 'info') {
  if (!el.toastContainer) return;
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${type === 'success' ? '✓' : type === 'error' ? '⚠' : 'ℹ'}</span> <span>${message}</span>`;
  el.toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 4500);
}

// Persistent Auth Headers for Serverless Invocations
function getAuthHeaders(extraHeaders = {}) {
  const headers = { 'Content-Type': 'application/json', ...extraHeaders };
  const token = localStorage.getItem('google_api_token');
  const user = localStorage.getItem('google_user');
  if (token) headers['X-Google-Token'] = token;
  if (user) headers['X-Google-User'] = user;
  return headers;
}

const PROVIDER_MODELS = {
  groq: ['openai/gpt-oss-120b', 'openai/gpt-oss-20b', 'qwen/qwen3.8-27b'],
  gemini: ['gemini-3.8-flash', 'gemini-flash-latest', 'gemini-pro-latest'],
  cohere: ['command-r-08-2024', 'command-r-plus-08-2024'],
  openai: ['gpt-4o', 'gpt-4o-mini'],
  anthropic: ['claude-3-5-sonnet-20241022', 'claude-3-5-haiku-20241022'],
};

if (el.genProvider) {
  el.genProvider.addEventListener('change', (e) => {
    const models = PROVIDER_MODELS[e.target.value] || [];
    el.genModel.innerHTML = '';
    models.forEach(m => {
      const opt = document.createElement('option');
      opt.value = m;
      opt.textContent = m;
      el.genModel.appendChild(opt);
    });
  });
}

// Tab Navigation
function switchTab(tabId) {
  el.tabs.forEach(t => t.classList.toggle('active', t.dataset.tab === tabId));
  el.mobileTabs.forEach(t => t.classList.toggle('active', t.dataset.tab === tabId));
  el.panes.forEach(p => p.classList.toggle('active', p.id === tabId));
  state.activeTab = tabId;
  if (tabId === 'tab-editor') renderPreview();
}

el.tabs.forEach(tab => tab.addEventListener('click', () => switchTab(tab.dataset.tab)));
el.mobileTabs.forEach(tab => tab.addEventListener('click', () => switchTab(tab.dataset.tab)));

// Monetization Selector in Autopilot
if (el.autopilotMonetizeType) {
  el.autopilotMonetizeType.addEventListener('change', (e) => {
    const val = e.target.value;
    if (val === 'product') {
      el.autopilotProductSelectGroup.classList.remove('hidden');
      el.autopilotAffiliateSelectGroup.classList.add('hidden');
    } else if (val === 'affiliate') {
      el.autopilotProductSelectGroup.classList.add('hidden');
      el.autopilotAffiliateSelectGroup.classList.remove('hidden');
    } else {
      el.autopilotProductSelectGroup.classList.add('hidden');
      el.autopilotAffiliateSelectGroup.classList.add('hidden');
    }
  });
}

// Trending Topics & Autopilot
async function loadTrendingTopics() {
  try {
    const res = await fetch('/api/trending');
    const data = await res.json();
    if (data.random_suggestion) {
      applyTrendingPick(data.random_suggestion);
    }
  } catch (err) {
    console.error('Failed to load trending topics', err);
  }
}

function applyTrendingPick(pick) {
  state.trendingPick = pick;
  if (el.currentTrendingTitle) el.currentTrendingTitle.textContent = pick.topic;
  if (el.trendingCategory) el.trendingCategory.textContent = pick.category || 'Tech';
  if (el.trendingCpc) el.trendingCpc.textContent = `${pick.cpc_tier || 'High'} AdSense CPC`;
}

if (el.btnShuffleTopic) {
  el.btnShuffleTopic.addEventListener('click', async () => {
    try {
      const res = await fetch('/api/trending');
      const data = await res.json();
      if (data.random_suggestion) {
        applyTrendingPick(data.random_suggestion);
        showToast('New trending topic selected!', 'info');
      }
    } catch (err) {
      showToast(err.message, 'error');
    }
  });
}

// 1-Click Autopilot Generator
if (el.btnRunAutopilot) {
  el.btnRunAutopilot.addEventListener('click', async () => {
    const customTopic = el.autopilotCustomTopic.value.trim();
    const topic = customTopic || (state.trendingPick ? state.trendingPick.topic : '');
    const keyword = state.trendingPick ? state.trendingPick.keyword : topic;
    const provider = el.autopilotProvider.value;
    const monetizeType = el.autopilotMonetizeType ? el.autopilotMonetizeType.value : 'none';
    const includeProduct = monetizeType === 'product';
    const productId = includeProduct && el.autopilotProductSelect.value ? parseInt(el.autopilotProductSelect.value, 10) : null;
    const includeAffiliate = monetizeType === 'affiliate';
    const affiliateId = includeAffiliate && el.autopilotAffiliateSelect.value ? parseInt(el.autopilotAffiliateSelect.value, 10) : null;
    const uploadBlogger = el.autopilotToggleBlogger.checked;
    const blogId = el.activeBlogSelector ? el.activeBlogSelector.value : '';

    if (uploadBlogger && !state.googleConnected) {
      showToast('Google Blogger not connected. Article will be generated and saved in local draft storage.', 'info');
    }

    el.autopilotSpinner.classList.remove('hidden');
    el.btnRunAutopilot.disabled = true;

    try {
      showToast('⚡ Researching topic & generating 1,500+ word humanized guide...', 'info');
      const res = await fetch('/api/autopilot', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          topic,
          primary_keyword: keyword,
          provider,
          include_product: includeProduct,
          product_id: productId,
          include_affiliate: includeAffiliate,
          affiliate_id: affiliateId,
          upload_to_blogger: uploadBlogger && state.googleConnected && Boolean(blogId),
          blog_id: blogId,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Autopilot generation failed');

      state.currentArticle.id = data.article_id;
      state.currentArticle.title = data.title;
      state.currentArticle.topic = data.topic;
      state.currentArticle.keyword = data.keyword;
      state.currentArticle.markdown = data.markdown;
      state.currentArticle.renderedHtml = data.rendered_html;
      state.currentArticle.featuredImageUrl = data.image_url;
      state.currentArticle.diagramImageUrl = data.diagram_url;

      el.autopilotResultBody.innerHTML = `
        <div style="display:flex; flex-direction:column; gap:14px;">
          <div style="display:grid; grid-template-columns: 1fr 1fr; gap:12px;">
            <div>
              <span style="font-size:12px; color:#94a3b8; display:block; margin-bottom:4px;">Cover Banner</span>
              <img src="${data.image_url}" alt="Cover" style="width:100%; max-height:160px; object-fit:cover; border-radius:8px;" />
            </div>
            <div>
              <span style="font-size:12px; color:#94a3b8; display:block; margin-bottom:4px;">Architecture Diagram</span>
              <img src="${data.diagram_url}" alt="Diagram" style="width:100%; max-height:160px; object-fit:cover; border-radius:8px;" />
            </div>
          </div>
          <h3 style="color:#ffffff; margin:4px 0 0 0; font-size:18px;">${data.title}</h3>
          <div style="display:flex; gap:10px; flex-wrap:wrap;">
            <span class="badge green">✓ ${data.word_count} Humanized Words</span>
            <span class="badge blue">Draft #${data.article_id} Saved</span>
            ${includeProduct ? `<span class="badge purple">Product Attached</span>` : `<span class="badge yellow">AdSense Pure Mode</span>`}
            ${data.blogger_result ? `<span class="badge green">✓ Uploaded to Blogger Drafts!</span>` : ''}
          </div>
        </div>
      `;
      el.autopilotResultCard.classList.remove('hidden');
      showToast('1,500+ word masterclass with dual illustrations ready!', 'success');
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      el.autopilotSpinner.classList.add('hidden');
      el.btnRunAutopilot.disabled = false;
    }
  });
}

if (el.btnOpenAutopilotInEditor) {
  el.btnOpenAutopilotInEditor.addEventListener('click', () => {
    loadArticleIntoEditor(state.currentArticle);
    switchTab('tab-editor');
  });
}

// Rewriter (Fix Low-Value Content)
if (el.btnRunRewrite) {
  el.btnRunRewrite.addEventListener('click', async () => {
    const title = el.rewriteTitle.value.trim();
    const content = el.rewriteContent.value.trim();
    if (!title || !content) {
      showToast('Please provide both title and original content.', 'error');
      return;
    }

    el.rewriteSpinner.classList.remove('hidden');
    el.btnRunRewrite.disabled = true;

    try {
      showToast('Transforming thin content into 1,500+ word humanized guide...', 'info');
      const res = await fetch('/api/rewrite', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          provider: 'groq',
          original_title: title,
          original_content: content,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Rewrite failed');

      state.currentArticle.title = data.title;
      state.currentArticle.markdown = data.markdown;

      el.rewriteResultBox.innerHTML = `
        <div>
          <h3 style="color:#34d399; margin-top:0;">Expansion Complete!</h3>
          <p style="font-size:14px; color:#cbd5e1;">Generated <strong>${data.word_count} words</strong> with complete production code, troubleshooting tracebacks, and structured FAQs.</p>
          <div style="background:#0f172a; padding:12px; border-radius:8px; max-height:220px; overflow-y:auto; font-family:monospace; font-size:12px; color:#94a3b8; white-space:pre-wrap;">
            ${data.markdown.slice(0, 1000)}...
          </div>
        </div>
      `;
      el.rewriteActions.classList.remove('hidden');
      showToast('Post expanded to AdSense masterclass level!', 'success');
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      el.rewriteSpinner.classList.add('hidden');
      el.btnRunRewrite.disabled = false;
    }
  });
}

if (el.btnSendRewrittenToEditor) {
  el.btnSendRewrittenToEditor.addEventListener('click', () => {
    loadArticleIntoEditor(state.currentArticle);
    switchTab('tab-editor');
  });
}

// Custom Generator
if (el.genForm) {
  el.genForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const provider = el.genProvider.value;
    const model = el.genModel.value;
    const topic = el.genTopic.value.trim();
    const keyword = el.genKeyword.value.trim();
    const audience = el.genAudience.value;
    const notes = el.genNotes.value.trim();

    el.genSpinner.classList.remove('hidden');
    el.genBtn.disabled = true;

    try {
      showToast('Generating technical tutorial with verified real code...', 'info');
      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ provider, model, topic, primary_keyword: keyword, audience, notes }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Generation failed');

      state.currentArticle.title = data.title;
      state.currentArticle.markdown = data.markdown;

      el.genSummaryBox.innerHTML = `
        <div>
          <h3 style="color:#38bdf8; margin-top:0;">${data.title}</h3>
          <p style="font-size:14px; color:#cbd5e1;">Generated <strong>${data.word_count} words</strong>. Verified syntax-valid code & traceback troubleshooting included.</p>
        </div>
      `;
      el.genActions.classList.remove('hidden');
      showToast('Tutorial generated successfully!', 'success');
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      el.genSpinner.classList.add('hidden');
      el.genBtn.disabled = false;
    }
  });
}

if (el.btnSendToEditor) {
  el.btnSendToEditor.addEventListener('click', () => {
    loadArticleIntoEditor(state.currentArticle);
    switchTab('tab-editor');
  });
}

// Editor & Live Rendering
function loadArticleIntoEditor(article) {
  el.editorTitle.value = article.title || '';
  el.markdownEditor.value = article.markdown || '';
  renderPreview();
}

async function renderPreview() {
  const title = el.editorTitle.value.trim();
  const markdown = el.markdownEditor.value.trim();
  if (!markdown) {
    el.previewRendered.innerHTML = '<p class="text-muted">Type markdown on the left to see live rendered HTML.</p>';
    el.wordCountBadge.textContent = '0 words';
    return;
  }

  const words = markdown.split(/\s+/).filter(Boolean).length;
  el.wordCountBadge.textContent = `${words} words`;

  try {
    const res = await fetch('/api/render', {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        markdown_text: markdown,
        title: title || 'Draft',
        include_toc: el.toggleToc.checked,
        include_product: el.toggleEbook.checked,
        featured_image_url: state.currentArticle.featuredImageUrl || null,
        section_image_url: state.currentArticle.diagramImageUrl || null,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Rendering failed');

    state.currentArticle.renderedHtml = data.rendered_html;
    state.currentArticle.schema = data.schema;

    el.previewRendered.innerHTML = data.rendered_html;
    el.rawHtmlViewer.value = data.rendered_html;
    el.rawSchemaViewer.textContent = JSON.stringify(data.schema, null, 2);

    if (data.warnings && data.warnings.length > 0) {
      el.qualityWarningsBanner.innerHTML = `<strong>AdSense Quality Checklist:</strong><ul>${data.warnings.map(w => `<li>${w}</li>`).join('')}</ul>`;
      el.qualityWarningsBanner.classList.remove('hidden');
    } else {
      el.qualityWarningsBanner.classList.add('hidden');
    }
  } catch (err) {
    console.error('Render preview error', err);
  }
}

if (el.btnRefreshPreview) el.btnRefreshPreview.addEventListener('click', renderPreview);
if (el.markdownEditor) el.markdownEditor.addEventListener('input', debounce(renderPreview, 600));
if (el.toggleToc) el.toggleToc.addEventListener('change', renderPreview);
if (el.toggleEbook) el.toggleEbook.addEventListener('change', renderPreview);

// Save Draft to Local DB
if (el.btnSaveDb) {
  el.btnSaveDb.addEventListener('click', async () => {
    const title = el.editorTitle.value.trim();
    const markdown = el.markdownEditor.value.trim();
    if (!title || !markdown) {
      showToast('Title and content are required to save draft.', 'error');
      return;
    }
    try {
      const res = await fetch('/api/articles', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          topic: state.currentArticle.topic || title,
          primary_keyword: state.currentArticle.keyword || title,
          title,
          markdown_body: markdown,
          rendered_html: state.currentArticle.renderedHtml,
          schema_json: state.currentArticle.schema,
          article_id: state.currentArticle.id,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Save failed');
      state.currentArticle.id = data.id;
      showToast(`Draft #${data.id} saved in database!`, 'success');
    } catch (err) {
      showToast(err.message, 'error');
    }
  });
}

// Upload Draft to Blogger
if (el.btnUploadBlogger) {
  el.btnUploadBlogger.addEventListener('click', async () => {
    if (!state.googleConnected) {
      showToast('Please connect your Google account in the Blogger tab first.', 'error');
      switchTab('tab-blogger');
      return;
    }
    const blogId = el.activeBlogSelector ? el.activeBlogSelector.value : '';
    if (!blogId) {
      showToast('Select an active Blogger blog in the Blogger tab.', 'error');
      switchTab('tab-blogger');
      return;
    }
    const title = el.editorTitle.value.trim();
    const html = state.currentArticle.renderedHtml || el.rawHtmlViewer.value;
    if (!title || !html) {
      showToast('Title and rendered HTML are required to create Blogger draft.', 'error');
      return;
    }

    try {
      showToast('Publishing draft to Blogger...', 'info');
      const res = await fetch('/api/blogger/draft', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          blog_id: blogId,
          title,
          rendered_html: html,
          article_id: state.currentArticle.id,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Blogger upload failed');
      showToast('Successfully published draft to Blogger!', 'success');
      loadBloggerPosts(blogId);
    } catch (err) {
      showToast(err.message, 'error');
    }
  });
}

// Free Image Studio
if (el.btnAutoPrompt) {
  el.btnAutoPrompt.addEventListener('click', () => {
    const topic = el.imgTopicInput.value.trim();
    if (!topic) {
      showToast('Enter a topic first.', 'error');
      return;
    }
    el.imgPromptInput.value = `Modern minimalist 3D isometric tech banner about ${topic}, sleek dark theme, vibrant neon accents, futuristic glassmorphism, 8k render, no text, no logo`;
  });
}

if (el.btnGenerateImage) {
  el.btnGenerateImage.addEventListener('click', async () => {
    const prompt = el.imgPromptInput.value.trim();
    const topic = el.imgTopicInput.value.trim();
    el.imgSpinner.classList.remove('hidden');
    el.btnGenerateImage.disabled = true;

    try {
      showToast('Generating permanent free AI cover image...', 'info');
      const res = await fetch('/api/generate-image', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ prompt, topic }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Image generation failed');

      el.imgDisplayContainer.innerHTML = `<img src="${data.image_url}" alt="Cover" style="width:100%; border-radius:10px; box-shadow:0 10px 25px rgba(0,0,0,0.5);" />`;
      el.imgActions.classList.remove('hidden');
      state.currentArticle.featuredImageUrl = data.image_url;
      showToast('High-resolution cover generated!', 'success');
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      el.imgSpinner.classList.add('hidden');
      el.btnGenerateImage.disabled = false;
    }
  });
}

if (el.btnInsertImageEditor) {
  el.btnInsertImageEditor.addEventListener('click', () => {
    renderPreview();
    switchTab('tab-editor');
    showToast('Cover attached to current article!', 'success');
  });
}

// Product Management (Instamojo / Books)
async function loadProducts() {
  try {
    const res = await fetch('/api/products');
    const data = await res.json();
    state.products = Array.isArray(data) ? data : [];
    renderProductsTable();
    populateProductSelects();
  } catch (err) {
    console.error('Failed to load products', err);
  }
}

function renderProductsTable() {
  if (!el.productsTableContainer) return;
  if (state.products.length === 0) {
    el.productsTableContainer.innerHTML = '<p class="text-muted" style="font-size:13px;">No products added yet.</p>';
    return;
  }
  let html = '<div style="display:flex; flex-direction:column; gap:8px;">';
  state.products.forEach(p => {
    html += `
      <div style="display:flex; justify-content:space-between; align-items:center; background:#111827; padding:10px 14px; border-radius:8px; border:1px solid #1f2937;">
        <div>
          <strong style="color:#ffffff; font-size:14px;">${p.title}</strong>
          <span style="color:#34d399; font-size:13px; margin-left:8px;">${p.price || ''}</span>
          <p style="margin:2px 0 0 0; color:#94a3b8; font-size:12px;">${p.url}</p>
        </div>
        <button class="btn btn-secondary btn-sm" onclick="deleteProductItem(${p.id})">Delete</button>
      </div>
    `;
  });
  html += '</div>';
  el.productsTableContainer.innerHTML = html;

  // Render live preview for the first product
  if (state.products.length > 0 && el.ebookLivePreview) {
    const prod = state.products[0];
    el.ebookLivePreview.innerHTML = `
      <div style="padding:18px; border:2px solid #4f46e5; border-radius:12px; background:linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%); color:#ffffff;">
        <span style="display:inline-block; padding:3px 10px; font-size:11px; font-weight:700; background:#fbbf24; color:#000; border-radius:12px; margin-bottom:8px;">${prod.badge || '★ Recommended Guide'}</span>
        <h4 style="margin:0 0 6px 0; font-size:17px; color:#fff;">${prod.title}</h4>
        <p style="margin:0 0 10px 0; font-size:13px; color:#cbd5e1;">${prod.description || 'Fast-track developer guide.'}</p>
        <div style="display:flex; align-items:center; justify-content:space-between;">
          <span style="font-size:18px; font-weight:800; color:#34d399;">${prod.price || 'Special'}</span>
          <a href="${prod.url}" target="_blank" class="btn btn-primary btn-sm">Get on Instamojo &rarr;</a>
        </div>
      </div>
    `;
  }
}

function populateProductSelects() {
  if (!el.autopilotProductSelect) return;
  el.autopilotProductSelect.innerHTML = '<option value="">-- Choose Product --</option>';
  state.products.forEach(p => {
    const opt = document.createElement('option');
    opt.value = p.id;
    opt.textContent = `${p.title} (${p.price || ''})`;
    el.autopilotProductSelect.appendChild(opt);
  });
  if (state.products.length > 0) {
    el.autopilotProductSelect.value = state.products[0].id;
  }
}

if (el.productForm) {
  el.productForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const title = document.getElementById('prod-title').value.trim();
    const url = document.getElementById('prod-url').value.trim();
    const price = document.getElementById('prod-price').value.trim();
    const description = document.getElementById('prod-desc').value.trim();

    try {
      const res = await fetch('/api/products', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ title, url, price, description }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to save product');
      showToast('Product saved in vault!', 'success');
      el.productForm.reset();
      loadProducts();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });
}

window.deleteProductItem = async function(id) {
  if (!confirm('Remove this product?')) return;
  try {
    const res = await fetch(`/api/products/${id}`, { method: 'DELETE', headers: getAuthHeaders() });
    if (!res.ok) throw new Error('Failed to delete product');
    showToast('Product removed.', 'info');
    loadProducts();
  } catch (err) {
    showToast(err.message, 'error');
  }
};

// Affiliates Management
async function loadAffiliates() {
  try {
    const res = await fetch('/api/affiliates');
    const data = await res.json();
    state.affiliates = Array.isArray(data) ? data : [];
    renderAffiliatesTable();
    populateAffiliateSelects();
  } catch (err) {
    console.error('Failed to load affiliates', err);
  }
}

function renderAffiliatesTable() {
  if (!el.affTableContainer) return;
  if (state.affiliates.length === 0) {
    el.affTableContainer.innerHTML = '<p class="text-muted" style="font-size:13px;">No affiliate links stored yet.</p>';
    return;
  }
  let html = '<div style="display:flex; flex-direction:column; gap:8px;">';
  state.affiliates.forEach(a => {
    html += `
      <div style="display:flex; justify-content:space-between; align-items:center; background:#111827; padding:10px 14px; border-radius:8px; border:1px solid #1f2937;">
        <div>
          <strong style="color:#ffffff; font-size:14px;">${a.product_name}</strong>
          <p style="margin:2px 0 0 0; color:#94a3b8; font-size:12px;">${a.tracking_url}</p>
        </div>
        <button class="btn btn-secondary btn-sm" onclick="deleteAffiliateItem(${a.id})">Delete</button>
      </div>
    `;
  });
  html += '</div>';
  el.affTableContainer.innerHTML = html;
}

function populateAffiliateSelects() {
  if (!el.autopilotAffiliateSelect) return;
  el.autopilotAffiliateSelect.innerHTML = '<option value="">-- Choose Affiliate Link --</option>';
  state.affiliates.forEach(a => {
    const opt = document.createElement('option');
    opt.value = a.id;
    opt.textContent = a.product_name;
    el.autopilotAffiliateSelect.appendChild(opt);
  });
}

if (el.affiliateForm) {
  el.affiliateForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('aff-name').value.trim();
    const url = document.getElementById('aff-url').value.trim();
    const keywords = (document.getElementById('aff-keywords').value || '').split(',').map(k => k.trim()).filter(Boolean);

    try {
      const res = await fetch('/api/affiliates', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          product_name: name,
          tracking_url: url,
          keywords,
          disclosure: 'We may receive a commission for purchases made through this link at no additional cost to you.',
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to save affiliate');
      showToast('Affiliate entry saved!', 'success');
      el.affiliateForm.reset();
      loadAffiliates();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });
}

window.deleteAffiliateItem = async function(id) {
  if (!confirm('Remove this affiliate link?')) return;
  try {
    const res = await fetch(`/api/affiliates/${id}`, { method: 'DELETE', headers: getAuthHeaders() });
    if (!res.ok) throw new Error('Failed to delete affiliate');
    showToast('Affiliate removed.', 'info');
    loadAffiliates();
  } catch (err) {
    showToast(err.message, 'error');
  }
};

// Google OAuth Setup & Error 400 Diagnosis
async function checkOAuthStatus() {
  // Check local token first
  const localToken = localStorage.getItem('google_api_token');
  const localUser = localStorage.getItem('google_user');
  if (localToken && localUser) {
    try {
      const user = JSON.parse(localUser);
      el.googleIndicator.className = 'indicator green';
      el.googleStatusText.textContent = `Blogger: ${user.email || 'Online'}`;
      el.connectGoogleBtn.textContent = 'Connected ✓';
      state.googleConnected = true;
    } catch (e) {}
  }

  try {
    const res = await fetch('/api/oauth/status', { headers: getAuthHeaders() });
    const data = await res.json();
    state.googleConnected = data.connected;

    if (data.configured_redirect_uri && el.oauthRedirectDisplay) {
      el.oauthRedirectDisplay.value = data.configured_redirect_uri;
    }

    if (data.connected) {
      el.googleIndicator.className = 'indicator green';
      el.googleStatusText.textContent = `Blogger: ${data.user.email || 'Online'}`;
      el.connectGoogleBtn.textContent = 'Connected ✓';
      loadBloggerBlogs();
    } else if (!localToken) {
      el.googleIndicator.className = 'indicator red';
      el.googleStatusText.textContent = 'Blogger: Offline';
    }
  } catch (err) {
    console.error('OAuth status check failed', err);
  }
}

async function triggerGoogleLogin() {
  try {
    const res = await fetch('/api/oauth/url');
    const data = await res.json();
    if (data.redirect_uri && el.oauthRedirectDisplay) {
      el.oauthRedirectDisplay.value = data.redirect_uri;
    }
    if (data.url) {
      window.location.href = data.url;
    }
  } catch (err) {
    showToast('Login failed: ' + err.message, 'error');
  }
}

if (el.connectGoogleBtn) el.connectGoogleBtn.addEventListener('click', triggerGoogleLogin);
if (el.btnLoginGoogleAlt) el.btnLoginGoogleAlt.addEventListener('click', triggerGoogleLogin);

if (el.btnCopyRedirect) {
  el.btnCopyRedirect.addEventListener('click', () => {
    navigator.clipboard.writeText(el.oauthRedirectDisplay.value);
    showToast('Copied Redirect URI to clipboard!', 'success');
  });
}

// Blogger Blogs & Posts Loader
async function loadBloggerBlogs() {
  try {
    const res = await fetch('/api/blogger/blogs', { headers: getAuthHeaders() });
    const data = await res.json();
    if (data.blogs && data.blogs.length > 0) {
      el.activeBlogSelector.innerHTML = '';
      el.rewriteBloggerSelect.innerHTML = '<option value="">-- Choose Post to Rewrite --</option>';
      data.blogs.forEach(b => {
        const opt = document.createElement('option');
        opt.value = b.id;
        opt.textContent = `${b.name} (${b.url})`;
        el.activeBlogSelector.appendChild(opt);
      });
      state.activeBlogId = data.blogs[0].id;
      loadBloggerPosts(state.activeBlogId);
    } else {
      showToast('No Blogger blogs found for this Google account.', 'error');
    }
  } catch (err) {
    console.error('Failed to load Blogger blogs:', err);
  }
}

async function loadBloggerPosts(blogId) {
  if (!blogId) return;
  try {
    const res = await fetch(`/api/blogger/posts?blog_id=${blogId}&limit=30`, { headers: getAuthHeaders() });
    const data = await res.json();
    if (data.posts && data.posts.length > 0) {
      el.rewriteBloggerSelect.innerHTML = '<option value="">-- Choose Post to Rewrite --</option>';
      let tableHtml = '<table style="width:100%; border-collapse:collapse; font-size:13px;"><thead><tr style="border-bottom:1px solid var(--border-subtle); color:#94a3b8;"><th style="padding:6px; text-align:left;">Title</th><th style="padding:6px; text-align:right;">Action</th></tr></thead><tbody>';
      
      data.posts.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.id;
        opt.textContent = p.title;
        opt.dataset.content = p.content || '';
        opt.dataset.title = p.title;
        el.rewriteBloggerSelect.appendChild(opt);

        tableHtml += `<tr style="border-bottom:1px solid var(--border-subtle);"><td style="padding:8px 6px;">${p.title}</td><td style="padding:8px 6px; text-align:right;"><button class="btn btn-secondary btn-sm" onclick="selectPostForRewrite('${p.id}')">Rewrite</button></td></tr>`;
      });
      tableHtml += '</tbody></table>';
      el.bloggerPostsContainer.innerHTML = tableHtml;
    } else {
      el.bloggerPostsContainer.innerHTML = '<p class="text-muted">No posts found in this blog.</p>';
    }
  } catch (err) {
    el.bloggerPostsContainer.innerHTML = `<p style="color:var(--color-danger);">${err.message}</p>`;
  }
}

// WIRED: "Load Posts" button click listener
if (el.btnFetchBloggerPosts) {
  el.btnFetchBloggerPosts.addEventListener('click', async () => {
    if (!state.googleConnected && !localStorage.getItem('google_api_token')) {
      showToast('Please connect your Google Blogger account first.', 'error');
      switchTab('tab-blogger');
      return;
    }
    showToast('Fetching latest posts from your Blogger blog...', 'info');
    await loadBloggerBlogs();
    showToast('Blogger posts loaded into dropdown!', 'success');
  });
}

if (el.btnRefreshBlogs) {
  el.btnRefreshBlogs.addEventListener('click', async () => {
    showToast('Refreshing blog list...', 'info');
    await loadBloggerBlogs();
  });
}

window.selectPostForRewrite = function(postId) {
  const opt = el.rewriteBloggerSelect.querySelector(`option[value="${postId}"]`);
  if (opt) {
    el.rewriteTitle.value = opt.dataset.title;
    el.rewriteContent.value = opt.dataset.content;
    switchTab('tab-rewriter');
    showToast(`Loaded "${opt.dataset.title}" into Rewriter`, 'info');
  }
};

if (el.rewriteBloggerSelect) {
  el.rewriteBloggerSelect.addEventListener('change', (e) => {
    const opt = e.target.selectedOptions[0];
    if (opt && opt.value) {
      el.rewriteTitle.value = opt.dataset.title;
      el.rewriteContent.value = opt.dataset.content;
    }
  });
}

// View Toggles (Rendered, HTML, Schema)
el.viewBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    el.viewBtns.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const view = btn.dataset.view;
    el.previewRendered.classList.toggle('hidden', view !== 'rendered');
    el.previewHtml.classList.toggle('hidden', view !== 'html');
    el.previewSchema.classList.toggle('hidden', view !== 'schema');
  });
});

function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// Startup Initialization
window.addEventListener('DOMContentLoaded', () => {
  loadTrendingTopics();
  checkOAuthStatus();
  loadProducts();
  loadAffiliates();

  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('oauth_success')) {
    showToast('Google Blogger connected successfully!', 'success');
    window.history.replaceState({}, document.title, window.location.pathname);
    setTimeout(checkOAuthStatus, 500);
  }
});
