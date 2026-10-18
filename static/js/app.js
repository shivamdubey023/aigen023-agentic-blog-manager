/**
 * NextGen Tech Notes — AI Agentic Hub Frontend Controller
 */

// State
const state = {
  activeTab: 'tab-generator',
  currentArticle: {
    id: null,
    title: '',
    topic: '',
    keyword: '',
    markdown: '',
    renderedHtml: '',
    schema: {},
    featuredImageUrl: '',
  },
  providers: {},
  affiliates: [],
  googleConnected: false,
  activeBlogId: '',
};

// Provider Models Registry
const PROVIDER_MODELS = {
  gemini: ['gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-1.5-flash'],
  groq: ['llama-3.3-70b-versatile', 'deepseek-r1-distill-llama-70b', 'llama-3.1-8b-instant'],
  cohere: ['command-r-plus-08-2024', 'command-r-08-2024'],
  openai: ['gpt-4o', 'gpt-4o-mini'],
  anthropic: ['claude-3-5-sonnet-20241022', 'claude-3-5-haiku-20241022'],
};

// DOM Elements
const el = {
  tabs: document.querySelectorAll('.nav-tab'),
  panes: document.querySelectorAll('.tab-pane'),
  toastContainer: document.getElementById('toast-container'),
  
  // Status
  googleStatusPill: document.getElementById('google-status-pill'),
  googleIndicator: document.getElementById('google-indicator'),
  googleStatusText: document.getElementById('google-status-text'),
  connectGoogleBtn: document.getElementById('connect-google-btn'),

  // Generator
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

  // Rewriter
  rewriteBloggerSelect: document.getElementById('rewrite-blogger-select'),
  btnFetchBloggerPosts: document.getElementById('btn-fetch-blogger-posts'),
  rewriteTitle: document.getElementById('rewrite-title'),
  rewriteContent: document.getElementById('rewrite-content'),
  rewriteProvider: document.getElementById('rewrite-provider'),
  rewriteKeyword: document.getElementById('rewrite-keyword'),
  rewriteSpinner: document.getElementById('rewrite-spinner'),
  btnRunRewrite: document.getElementById('btn-run-rewrite'),
  rewriteResultBox: document.getElementById('rewrite-result-box'),
  rewriteActions: document.getElementById('rewrite-actions'),
  btnSendRewrittenToEditor: document.getElementById('btn-send-rewritten-to-editor'),

  // Image Studio
  imgTopicInput: document.getElementById('img-topic-input'),
  btnAutoPrompt: document.getElementById('btn-auto-prompt'),
  imgPromptInput: document.getElementById('img-prompt-input'),
  imgAspect: document.getElementById('img-aspect'),
  btnGenerateImage: document.getElementById('btn-generate-image'),
  imgSpinner: document.getElementById('img-spinner'),
  imgDisplayContainer: document.getElementById('image-display-container'),
  imgActions: document.getElementById('image-actions'),
  generatedImageUrl: document.getElementById('generated-image-url'),
  btnInsertImageEditor: document.getElementById('btn-insert-image-editor'),

  // Editor
  editorTitle: document.getElementById('editor-title'),
  markdownEditor: document.getElementById('markdown-editor'),
  wordCountBadge: document.getElementById('word-count-badge'),
  toggleToc: document.getElementById('toggle-toc'),
  toggleEbook: document.getElementById('toggle-ebook'),
  selectAffiliate: document.getElementById('select-affiliate'),
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

  // Monetization & Settings
  ebookLivePreview: document.getElementById('ebook-live-preview'),
  affiliateForm: document.getElementById('affiliate-form'),
  affTableContainer: document.getElementById('affiliates-table-container'),
  keysForm: document.getElementById('keys-form'),
  keyGroq: document.getElementById('key-groq'),
  keyGemini: document.getElementById('key-gemini'),
  keyCohere: document.getElementById('key-cohere'),
  keyOpenAI: document.getElementById('key-openai'),
  keyAnthropic: document.getElementById('key-anthropic'),

  // Blogger & Console
  activeBlogSelector: document.getElementById('active-blog-selector'),
  btnRefreshBlogs: document.getElementById('btn-refresh-blogs'),
  bloggerPostsContainer: document.getElementById('blogger-posts-container'),
  btnFetchSc: document.getElementById('btn-fetch-sc'),
  scPeriod: document.getElementById('sc-period'),
  scMetricsContainer: document.getElementById('sc-metrics-container'),
};

// Notifications
function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${type === 'success' ? '✓' : type === 'error' ? '⚠' : 'ℹ'}</span> <span>${message}</span>`;
  el.toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Local Storage Key Management
function getStoredKey(provider) {
  return localStorage.getItem(`api_key_${provider}`) || '';
}

function setStoredKey(provider, key) {
  if (key) localStorage.setItem(`api_key_${provider}`, key.trim());
}

// Initialize Tabs
function initTabs() {
  el.tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const target = tab.dataset.tab;
      el.tabs.forEach(t => t.classList.remove('active'));
      el.panes.forEach(p => p.classList.remove('active'));
      tab.classList.add('active');
      document.getElementById(target).classList.add('active');
      state.activeTab = target;
      if (target === 'tab-editor') renderPreview();
    });
  });
}

// Update Model Dropdown when provider changes
function updateModelDropdown(selectEl, provider) {
  const models = PROVIDER_MODELS[provider] || [];
  selectEl.innerHTML = '';
  models.forEach(m => {
    const opt = document.createElement('option');
    opt.value = m;
    opt.textContent = m;
    selectEl.appendChild(opt);
  });
}

// Load Settings from LocalStorage
function loadSettings() {
  el.keyGroq.value = getStoredKey('groq');
  el.keyGemini.value = getStoredKey('gemini');
  el.keyCohere.value = getStoredKey('cohere');
  el.keyOpenAI.value = getStoredKey('openai');
  el.keyAnthropic.value = getStoredKey('anthropic');
}

// Save Settings Form
el.keysForm.addEventListener('submit', (e) => {
  e.preventDefault();
  setStoredKey('groq', el.keyGroq.value);
  setStoredKey('gemini', el.keyGemini.value);
  setStoredKey('cohere', el.keyCohere.value);
  setStoredKey('openai', el.keyOpenAI.value);
  setStoredKey('anthropic', el.keyAnthropic.value);
  showToast('API keys saved locally in browser!', 'success');
});

// Provider selection listeners
el.genProvider.addEventListener('change', (e) => {
  updateModelDropdown(el.genModel, e.target.value);
});

// Generator Logic
el.genForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const provider = el.genProvider.value;
  const model = el.genModel.value;
  const topic = el.genTopic.value.trim();
  const keyword = el.genKeyword.value.trim();
  const audience = el.genAudience.value;
  const notes = el.genNotes.value.trim();
  const apiKey = getStoredKey(provider);

  el.genSpinner.classList.remove('hidden');
  el.genBtn.disabled = true;
  el.genSummaryBox.innerHTML = '<div class="empty-state"><div class="btn-spinner"></div><p style="margin-top:12px;">Crafting technical tutorial with code examples, tracebacks, and verification checklists...</p></div>';

  try {
    const res = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        provider,
        model,
        api_key: apiKey,
        topic,
        primary_keyword: keyword,
        audience,
        notes,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Generation failed');

    state.currentArticle.title = data.title;
    state.currentArticle.markdown = data.markdown;
    state.currentArticle.topic = topic;
    state.currentArticle.keyword = keyword;

    let warningHtml = '';
    if (data.warnings && data.warnings.length > 0) {
      warningHtml = `<div class="warnings-banner" style="margin-top:12px; border-radius:6px;"><strong>AdSense Review Checklist:</strong><ul>${data.warnings.map(w => `<li>${w}</li>`).join('')}</ul></div>`;
    }

    el.genSummaryBox.innerHTML = `
      <div style="padding: 10px 0;">
        <h3 style="color:#ffffff; margin-bottom:8px;">${data.title}</h3>
        <p style="color:#94a3b8; font-size:14px; margin-bottom:8px;"><strong>Word Count:</strong> <span class="badge green">${data.word_count} words</span></p>
        <p style="color:#cbd5e1; font-size:14px; margin-bottom:12px;">Article successfully drafted with reproducible sections and structured headers.</p>
        ${warningHtml}
      </div>
    `;
    el.genActions.classList.remove('hidden');
    showToast('Tutorial generated successfully!', 'success');
  } catch (err) {
    el.genSummaryBox.innerHTML = `<div class="empty-state" style="color:var(--color-danger);"><p>Error: ${err.message}</p></div>`;
    showToast(err.message, 'error');
  } finally {
    el.genSpinner.classList.add('hidden');
    el.genBtn.disabled = false;
  }
});

el.btnSendToEditor.addEventListener('click', () => {
  el.editorTitle.value = state.currentArticle.title;
  el.markdownEditor.value = state.currentArticle.markdown;
  switchTab('tab-editor');
  renderPreview();
});

// Blog Rewriter Logic
el.btnRunRewrite.addEventListener('submit', (e) => e.preventDefault());
el.btnRunRewrite.addEventListener('click', async () => {
  const title = el.rewriteTitle.value.trim();
  const content = el.rewriteContent.value.trim();
  const provider = el.rewriteProvider.value;
  const keyword = el.rewriteKeyword.value.trim();
  const apiKey = getStoredKey(provider);

  if (!title || !content) {
    showToast('Please provide both title and content to rewrite', 'error');
    return;
  }

  el.rewriteSpinner.classList.remove('hidden');
  el.btnRunRewrite.disabled = true;
  el.rewriteResultBox.innerHTML = '<div class="empty-state"><div class="btn-spinner"></div><p style="margin-top:12px;">Rewriting and expanding for AdSense quality score and organic ranking...</p></div>';

  try {
    const res = await fetch('/api/rewrite', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        provider,
        api_key: apiKey,
        original_title: title,
        original_content: content,
        primary_keyword: keyword,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Rewrite failed');

    state.currentArticle.title = data.title;
    state.currentArticle.markdown = data.markdown;
    state.currentArticle.topic = title;
    state.currentArticle.keyword = keyword;

    el.rewriteResultBox.innerHTML = `
      <div style="padding: 10px 0;">
        <h3 style="color:#ffffff; margin-bottom:8px;">${data.title}</h3>
        <p style="color:#94a3b8; font-size:14px; margin-bottom:8px;"><strong>Expanded Word Count:</strong> <span class="badge green">${data.word_count} words</span></p>
        <p style="color:#cbd5e1; font-size:14px;">Post transformed into high-authority guide with reproducible steps and FAQs.</p>
      </div>
    `;
    el.rewriteActions.classList.remove('hidden');
    showToast('Post rewritten for AdSense compliance!', 'success');
  } catch (err) {
    el.rewriteResultBox.innerHTML = `<div class="empty-state" style="color:var(--color-danger);"><p>Error: ${err.message}</p></div>`;
    showToast(err.message, 'error');
  } finally {
    el.rewriteSpinner.classList.add('hidden');
    el.btnRunRewrite.disabled = false;
  }
});

el.btnSendRewrittenToEditor.addEventListener('click', () => {
  el.editorTitle.value = state.currentArticle.title;
  el.markdownEditor.value = state.currentArticle.markdown;
  switchTab('tab-editor');
  renderPreview();
});

// Image Studio Logic
el.btnAutoPrompt.addEventListener('click', () => {
  const topic = el.imgTopicInput.value.trim();
  if (!topic) {
    showToast('Enter a topic first to generate prompt', 'error');
    return;
  }
  el.imgPromptInput.value = `Modern minimalist 3D isometric tech banner about ${topic}, sleek dark theme, vibrant neon accents, futuristic glassmorphism interface, clean cybersecurity and software development aesthetics, ultra-high resolution 8k render`;
});

el.btnGenerateImage.addEventListener('click', async () => {
  const prompt = el.imgPromptInput.value.trim();
  const topic = el.imgTopicInput.value.trim();
  if (!prompt && !topic) {
    showToast('Please provide a prompt or topic', 'error');
    return;
  }

  el.imgSpinner.classList.remove('hidden');
  el.btnGenerateImage.disabled = true;

  try {
    const res = await fetch('/api/generate-image', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt, topic }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error('Image generation failed');

    state.currentArticle.featuredImageUrl = data.image_url;
    el.imgDisplayContainer.className = 'image-display-container';
    el.imgDisplayContainer.innerHTML = `<img src="${data.image_url}" alt="${prompt}" />`;
    el.generatedImageUrl.value = data.image_url;
    el.imgActions.classList.remove('hidden');
    showToast('Free AI cover generated!', 'success');
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    el.imgSpinner.classList.add('hidden');
    el.btnGenerateImage.disabled = false;
  }
});

el.btnInsertImageEditor.addEventListener('click', () => {
  if (state.currentArticle.featuredImageUrl) {
    switchTab('tab-editor');
    renderPreview();
    showToast('Cover image attached to article!', 'success');
  }
});

// Live Preview & Render Logic
async function renderPreview() {
  const title = el.editorTitle.value.trim();
  const markdownText = el.markdownEditor.value;
  const includeToc = el.toggleToc.checked;
  const includeEbook = el.toggleEbook.checked;
  const affiliateId = el.selectAffiliate.value ? parseInt(el.selectAffiliate.value) : null;
  const featuredImageUrl = state.currentArticle.featuredImageUrl || null;

  // Update Word Count
  const words = (markdownText.match(/\b[\w'-]+\b/g) || []).length;
  el.wordCountBadge.textContent = `${words} words`;

  if (!markdownText.trim()) {
    el.previewRendered.innerHTML = '<p class="text-muted">Type markdown on the left to see live rendered HTML.</p>';
    el.rawHtmlViewer.value = '';
    el.rawSchemaViewer.textContent = '';
    return;
  }

  try {
    const res = await fetch('/api/render', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        markdown_text: markdownText,
        title: title || 'Untitled Article',
        include_toc: includeToc,
        include_ebook: includeEbook,
        affiliate_id: affiliateId,
        featured_image_url: featuredImageUrl,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error('Render failed');

    state.currentArticle.renderedHtml = data.rendered_html;
    state.currentArticle.schema = data.schema;

    el.previewRendered.innerHTML = data.rendered_html;
    el.rawHtmlViewer.value = data.rendered_html;
    el.rawSchemaViewer.textContent = JSON.stringify(data.schema, null, 2);

    if (data.warnings && data.warnings.length > 0) {
      el.qualityWarningsBanner.classList.remove('hidden');
      el.qualityWarningsBanner.innerHTML = `<strong>Editorial & AdSense Checklist:</strong><ul>${data.warnings.map(w => `<li>${w}</li>`).join('')}</ul>`;
    } else {
      el.qualityWarningsBanner.classList.add('hidden');
    }
  } catch (err) {
    console.error(err);
  }
}

el.btnRefreshPreview.addEventListener('click', renderPreview);
el.markdownEditor.addEventListener('input', debounce(renderPreview, 600));
el.editorTitle.addEventListener('input', debounce(renderPreview, 600));
el.toggleToc.addEventListener('change', renderPreview);
el.toggleEbook.addEventListener('change', renderPreview);
el.selectAffiliate.addEventListener('change', renderPreview);

// Save Draft to SQLite
el.btnSaveDb.addEventListener('click', async () => {
  const title = el.editorTitle.value.trim();
  const markdown_body = el.markdownEditor.value.trim();
  if (!title || !markdown_body) {
    showToast('Provide title and markdown to save draft', 'error');
    return;
  }

  try {
    const res = await fetch('/api/articles', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        topic: state.currentArticle.topic || title,
        title,
        markdown_body,
        rendered_html: state.currentArticle.renderedHtml,
        schema_json: state.currentArticle.schema,
        article_id: state.currentArticle.id,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Save failed');
    state.currentArticle.id = data.id;
    showToast(`Saved draft #${data.id} to SQLite repository`, 'success');
  } catch (err) {
    showToast(err.message, 'error');
  }
});

// Upload to Blogger
el.btnUploadBlogger.addEventListener('click', async () => {
  if (!state.googleConnected) {
    showToast('Google account not connected. Click "Google Login" in header.', 'error');
    return;
  }
  const blogId = el.activeBlogSelector.value;
  if (!blogId) {
    showToast('Please select a target Blogger blog first.', 'error');
    return;
  }
  const title = el.editorTitle.value.trim();
  const rendered_html = state.currentArticle.renderedHtml;
  if (!title || !rendered_html) {
    showToast('Article must be rendered before uploading to Blogger.', 'error');
    return;
  }

  try {
    showToast('Uploading draft to Blogger...', 'info');
    const res = await fetch('/api/blogger/draft', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        blog_id: blogId,
        title,
        rendered_html,
        article_id: state.currentArticle.id,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Blogger upload failed');
    showToast(`Draft created on Blogger! Post ID: ${data.post_id}`, 'success');
  } catch (err) {
    showToast(err.message, 'error');
  }
});

// Preview View Toggles
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

// Google OAuth Status & Connect
async function checkOAuthStatus() {
  try {
    const res = await fetch('/api/oauth/status');
    const data = await res.json();
    state.googleConnected = data.connected;
    if (data.connected) {
      el.googleIndicator.className = 'indicator green';
      el.googleStatusText.textContent = `Blogger: ${data.user.email || 'Connected'}`;
      el.connectGoogleBtn.textContent = 'Connected ✓';
      el.connectGoogleBtn.disabled = true;
      loadBloggerBlogs();
    } else {
      el.googleIndicator.className = 'indicator red';
      el.googleStatusText.textContent = 'Blogger: Disconnected';
      el.connectGoogleBtn.disabled = false;
    }
  } catch (err) {
    console.error('OAuth status check failed', err);
  }
}

el.connectGoogleBtn.addEventListener('click', async () => {
  try {
    const res = await fetch('/api/oauth/url');
    const data = await res.json();
    if (data.url) {
      window.location.href = data.url;
    }
  } catch (err) {
    showToast('Could not initiate Google login: ' + err.message, 'error');
  }
});

async function loadBloggerBlogs() {
  try {
    const res = await fetch('/api/blogger/blogs');
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
    }
  } catch (err) {
    console.error('Failed to load Blogger blogs', err);
  }
}

async function loadBloggerPosts(blogId) {
  try {
    const res = await fetch(`/api/blogger/posts?blog_id=${blogId}&limit=20`);
    const data = await res.json();
    if (data.posts && data.posts.length > 0) {
      el.rewriteBloggerSelect.innerHTML = '<option value="">-- Choose Post to Rewrite --</option>';
      let tableHtml = '<table style="width:100%; border-collapse:collapse; font-size:13px;"><thead><tr style="border-bottom:1px solid var(--border-subtle); color:#94a3b8;"><th style="padding:6px; text-align:left;">Title</th><th style="padding:6px; text-align:left;">Status</th><th style="padding:6px; text-align:right;">Action</th></tr></thead><tbody>';
      
      data.posts.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.id;
        opt.textContent = p.title;
        opt.dataset.content = p.content || '';
        opt.dataset.title = p.title;
        el.rewriteBloggerSelect.appendChild(opt);

        tableHtml += `<tr style="border-bottom:1px solid var(--border-subtle);"><td style="padding:8px 6px;">${p.title}</td><td style="padding:8px 6px;"><span class="badge ${p.status === 'LIVE' ? 'green' : 'yellow'}">${p.status}</span></td><td style="padding:8px 6px; text-align:right;"><button class="btn btn-secondary btn-sm" onclick="selectPostForRewrite('${p.id}')">Rewrite</button></td></tr>`;
      });
      tableHtml += '</tbody></table>';
      el.bloggerPostsContainer.innerHTML = tableHtml;
    } else {
      el.bloggerPostsContainer.innerHTML = '<p class="text-muted">No posts found on this Blogger blog.</p>';
    }
  } catch (err) {
    el.bloggerPostsContainer.innerHTML = `<p style="color:var(--color-danger);">${err.message}</p>`;
  }
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

el.rewriteBloggerSelect.addEventListener('change', (e) => {
  const opt = e.target.selectedOptions[0];
  if (opt && opt.value) {
    el.rewriteTitle.value = opt.dataset.title;
    el.rewriteContent.value = opt.dataset.content;
  }
});

// Search Console Insights
el.btnFetchSc.addEventListener('click', async () => {
  const days = el.scPeriod.value;
  el.scMetricsContainer.innerHTML = '<div class="empty-state"><div class="btn-spinner"></div><p style="margin-top:10px;">Querying Google Search Console API...</p></div>';
  try {
    const res = await fetch(`/api/search-console?days=${days}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Search Console query failed');
    const rows = data.rows || [];
    if (rows.length === 0) {
      el.scMetricsContainer.innerHTML = '<p class="text-muted">Search Console returned 0 rows for this property & period. Verify property ownership at https://aigen023.blogspot.com/.</p>';
      return;
    }
    let html = `<div style="margin-bottom:12px; display:flex; gap:16px;"><span class="badge blue">Total Queries: ${rows.length}</span></div>`;
    html += '<table style="width:100%; border-collapse:collapse; font-size:13px;"><thead><tr style="border-bottom:1px solid var(--border-subtle); color:#94a3b8;"><th style="padding:6px; text-align:left;">Query</th><th style="padding:6px; text-align:center;">Clicks</th><th style="padding:6px; text-align:center;">Impressions</th><th style="padding:6px; text-align:center;">Pos</th></tr></thead><tbody>';
    rows.slice(0, 15).forEach(r => {
      const q = r.keys && r.keys.length > 1 ? r.keys[1] : (r.keys ? r.keys[0] : '');
      html += `<tr style="border-bottom:1px solid var(--border-subtle);"><td style="padding:6px;">${q}</td><td style="padding:6px; text-align:center;">${r.clicks}</td><td style="padding:6px; text-align:center;">${r.impressions}</td><td style="padding:6px; text-align:center;">${r.position.toFixed(1)}</td></tr>`;
    });
    html += '</tbody></table>';
    el.scMetricsContainer.innerHTML = html;
  } catch (err) {
    el.scMetricsContainer.innerHTML = `<p style="color:var(--color-danger);">${err.message}</p>`;
  }
});

// Render eBook Preview in Monetization Tab
function renderLiveEbookPreview() {
  const title = document.getElementById('ebook-title-cfg').value;
  const url = document.getElementById('ebook-url-cfg').value;
  const price = document.getElementById('ebook-price-cfg').value;

  el.ebookLivePreview.innerHTML = `
    <div style="padding: 20px; border: 2px solid #4f46e5; border-radius: 12px; background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%); color: #ffffff;">
      <span style="display:inline-block; padding: 3px 10px; font-size: 11px; font-weight: 700; background: #fbbf24; color: #000; border-radius: 12px; margin-bottom: 8px;">★ Recommended Resource</span>
      <h4 style="margin: 0 0 6px 0; font-size: 18px; color: #fff;">${title}</h4>
      <p style="margin: 0 0 10px 0; font-size: 13px; color: #cbd5e1;">Complete roadmap, interview questions, and real production projects.</p>
      <div style="display: flex; align-items: center; justify-content: space-between;">
        <span style="font-size: 20px; font-weight: 800; color: #34d399;">${price}</span>
        <a href="${url}" target="_blank" class="btn btn-primary btn-sm">Get on Instamojo &rarr;</a>
      </div>
    </div>
  `;
}

// Affiliate Link Functions
async function loadAffiliates() {
  try {
    const res = await fetch('/api/affiliates');
    const data = await res.json();
    state.affiliates = data;

    // Populate dropdown in editor
    el.selectAffiliate.innerHTML = '<option value="">No Affiliate Box</option>';
    data.forEach(a => {
      const opt = document.createElement('option');
      opt.value = a.id;
      opt.textContent = `${a.product_name} (#${a.id})`;
      el.selectAffiliate.appendChild(opt);
    });

    // Populate table in monetization tab
    if (data.length === 0) {
      el.affTableContainer.innerHTML = '<p class="text-muted">No affiliate links saved yet.</p>';
    } else {
      let html = '<table style="width:100%; border-collapse:collapse; font-size:13px;"><thead><tr style="border-bottom:1px solid var(--border-subtle); color:#94a3b8;"><th style="padding:6px; text-align:left;">Product</th><th style="padding:6px; text-align:left;">URL</th></tr></thead><tbody>';
      data.forEach(a => {
        html += `<tr style="border-bottom:1px solid var(--border-subtle);"><td style="padding:6px; font-weight:600;">${a.product_name}</td><td style="padding:6px;"><a href="${a.tracking_url}" target="_blank" style="color:var(--color-accent);">${a.tracking_url.slice(0, 30)}...</a></td></tr>`;
      });
      html += '</tbody></table>';
      el.affTableContainer.innerHTML = html;
    }
  } catch (err) {
    console.error('Failed to load affiliates', err);
  }
}

el.affiliateForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const product_name = document.getElementById('aff-name').value.trim();
  const tracking_url = document.getElementById('aff-url').value.trim();
  const keywords = document.getElementById('aff-keywords').value.split(',').map(k => k.trim()).filter(Boolean);
  const disclosure = document.getElementById('aff-disclosure').value.trim();

  try {
    const res = await fetch('/api/affiliates', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ product_name, tracking_url, keywords, disclosure }),
    });
    if (!res.ok) throw new Error('Could not save affiliate entry');
    showToast('Affiliate entry saved!', 'success');
    el.affiliateForm.reset();
    loadAffiliates();
  } catch (err) {
    showToast(err.message, 'error');
  }
});

// Tab Switch Helper
function switchTab(tabId) {
  const tabBtn = document.querySelector(`.nav-tab[data-tab="${tabId}"]`);
  if (tabBtn) tabBtn.click();
}

// Debounce Utility
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

// Bootstrapping
window.addEventListener('DOMContentLoaded', () => {
  initTabs();
  loadSettings();
  checkOAuthStatus();
  loadAffiliates();
  renderLiveEbookPreview();

  // If redirected with oauth_success
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('oauth_success')) {
    showToast('Google account connected successfully!', 'success');
    window.history.replaceState({}, document.title, window.location.pathname);
  }
});
