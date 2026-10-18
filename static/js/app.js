/**
 * NextGen Tech Notes — Autonomous AI Agentic Bot Controller
 * Mobile-First, Server-Side AI Execution, 1-Click Autopilot
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
  },
  trendingPick: null,
  googleConnected: false,
  activeBlogId: '',
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
  autopilotToggleEbook: document.getElementById('autopilot-toggle-ebook'),
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

  // Monetization & Blogger
  ebookLivePreview: document.getElementById('ebook-live-preview'),
  affiliateForm: document.getElementById('affiliate-form'),
  affTableContainer: document.getElementById('affiliates-table-container'),
  activeBlogSelector: document.getElementById('active-blog-selector'),
  btnRefreshBlogs: document.getElementById('btn-refresh-blogs'),
  bloggerPostsContainer: document.getElementById('blogger-posts-container'),
};

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

// Tab Switching
function switchTab(tabId) {
  el.tabs.forEach(t => t.classList.toggle('active', t.dataset.tab === tabId));
  el.mobileTabs.forEach(t => t.classList.toggle('active', t.dataset.tab === tabId));
  el.panes.forEach(p => p.classList.toggle('active', p.id === tabId));
  state.activeTab = tabId;
  if (tabId === 'tab-editor') renderPreview();
}

el.tabs.forEach(tab => tab.addEventListener('click', () => switchTab(tab.dataset.tab)));
el.mobileTabs.forEach(tab => tab.addEventListener('click', () => switchTab(tab.dataset.tab)));

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
  el.currentTrendingTitle.textContent = pick.topic;
  el.trendingCategory.textContent = pick.category || 'Tech';
  el.trendingCpc.textContent = `${pick.cpc_tier || 'High'} AdSense CPC`;
}

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

// 1-Click Autopilot Generator
el.btnRunAutopilot.addEventListener('click', async () => {
  const customTopic = el.autopilotCustomTopic.value.trim();
  const topic = customTopic || (state.trendingPick ? state.trendingPick.topic : '');
  const keyword = state.trendingPick ? state.trendingPick.keyword : topic;
  const provider = el.autopilotProvider.value;
  const includeEbook = el.autopilotToggleEbook.checked;
  const uploadBlogger = el.autopilotToggleBlogger.checked;
  const blogId = el.activeBlogSelector.value;

  if (uploadBlogger && !state.googleConnected) {
    showToast('Google account not connected yet. Will generate draft locally.', 'info');
  }

  el.autopilotSpinner.classList.remove('hidden');
  el.btnRunAutopilot.disabled = true;

  try {
    showToast('1. Researching topic & writing humanized 1,500+ word tutorial...', 'info');
    const res = await fetch('/api/autopilot', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        topic,
        primary_keyword: keyword,
        provider,
        include_ebook: includeEbook,
        upload_to_blogger: uploadBlogger && state.googleConnected,
        blog_id: blogId,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Autopilot failed');

    state.currentArticle.id = data.article_id;
    state.currentArticle.title = data.title;
    state.currentArticle.topic = data.topic;
    state.currentArticle.keyword = data.keyword;
    state.currentArticle.markdown = data.markdown;
    state.currentArticle.renderedHtml = data.rendered_html;
    state.currentArticle.featuredImageUrl = data.image_url;

    el.autopilotResultBody.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:12px;">
        <img src="${data.image_url}" alt="Cover" style="width:100%; max-height:220px; object-fit:cover; border-radius:8px;" />
        <h3 style="color:#ffffff; margin:0;">${data.title}</h3>
        <div style="display:flex; gap:10px; flex-wrap:wrap;">
          <span class="badge green">${data.word_count} Humanized Words</span>
          <span class="badge blue">Draft #${data.article_id} Saved</span>
          <span class="badge purple">Instamojo eBook Attached</span>
          ${data.blogger_result ? `<span class="badge green">Uploaded to Blogger!</span>` : ''}
        </div>
      </div>
    `;
    el.autopilotResultCard.classList.remove('hidden');
    showToast('Complete tutorial & permanent image created!', 'success');
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    el.autopilotSpinner.classList.add('hidden');
    el.btnRunAutopilot.disabled = false;
  }
});

el.btnOpenAutopilotInEditor.addEventListener('click', () => {
  el.editorTitle.value = state.currentArticle.title;
  el.markdownEditor.value = state.currentArticle.markdown;
  switchTab('tab-editor');
  renderPreview();
});

// AdSense Content Rewriter
el.btnRunRewrite.addEventListener('click', async () => {
  const title = el.rewriteTitle.value.trim();
  const content = el.rewriteContent.value.trim();

  if (!title || !content) {
    showToast('Provide title and content to rewrite', 'error');
    return;
  }

  el.rewriteSpinner.classList.remove('hidden');
  el.btnRunRewrite.disabled = true;
  el.rewriteResultBox.innerHTML = '<div class="empty-state"><div class="btn-spinner"></div><p style="margin-top:12px;">Expanding thin content with real code, tracebacks, and humanized depth...</p></div>';

  try {
    const res = await fetch('/api/rewrite', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        original_title: title,
        original_content: content,
        provider: 'groq',
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Rewrite failed');

    state.currentArticle.title = data.title;
    state.currentArticle.markdown = data.markdown;
    state.currentArticle.topic = title;

    el.rewriteResultBox.innerHTML = `
      <div style="padding:10px 0;">
        <h3 style="color:#ffffff; margin-bottom:8px;">${data.title}</h3>
        <span class="badge green">${data.word_count} words (AdSense Ready)</span>
        <p style="color:#cbd5e1; font-size:14px; margin-top:8px;">Low-value content eliminated. Expanded with real reproducible code and troubleshooting.</p>
      </div>
    `;
    el.rewriteActions.classList.remove('hidden');
    showToast('Post rewritten and AdSense boosted!', 'success');
  } catch (err) {
    el.rewriteResultBox.innerHTML = `<p style="color:var(--color-danger);">${err.message}</p>`;
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

// Live Preview & Render
async function renderPreview() {
  const title = el.editorTitle.value.trim();
  const markdownText = el.markdownEditor.value;
  const includeToc = el.toggleToc.checked;
  const includeEbook = el.toggleEbook.checked;

  const words = (markdownText.match(/\b[\w'-]+\b/g) || []).length;
  el.wordCountBadge.textContent = `${words} words`;

  if (!markdownText.trim()) {
    el.previewRendered.innerHTML = '<p class="text-muted">Type markdown on the left to see live rendered HTML.</p>';
    return;
  }

  try {
    const res = await fetch('/api/render', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        markdown_text: markdownText,
        title: title || 'Untitled Tutorial',
        include_toc: includeToc,
        include_ebook: includeEbook,
        featured_image_url: state.currentArticle.featuredImageUrl || null,
      }),
    });
    const data = await res.json();
    if (!res.ok) return;

    state.currentArticle.renderedHtml = data.rendered_html;
    state.currentArticle.schema = data.schema;
    el.previewRendered.innerHTML = data.rendered_html;
    el.rawHtmlViewer.value = data.rendered_html;
    el.rawSchemaViewer.textContent = JSON.stringify(data.schema, null, 2);

    if (data.warnings && data.warnings.length > 0) {
      el.qualityWarningsBanner.classList.remove('hidden');
      el.qualityWarningsBanner.innerHTML = `<strong>AdSense Quality Checklist:</strong><ul>${data.warnings.map(w => `<li>${w}</li>`).join('')}</ul>`;
    } else {
      el.qualityWarningsBanner.classList.add('hidden');
    }
  } catch (err) {
    console.error(err);
  }
}

el.btnRefreshPreview.addEventListener('click', renderPreview);
el.markdownEditor.addEventListener('input', debounce(renderPreview, 500));
el.editorTitle.addEventListener('input', debounce(renderPreview, 500));
el.toggleToc.addEventListener('change', renderPreview);
el.toggleEbook.addEventListener('change', renderPreview);

// Save to Database
el.btnSaveDb.addEventListener('click', async () => {
  const title = el.editorTitle.value.trim();
  const markdown_body = el.markdownEditor.value.trim();
  if (!title || !markdown_body) {
    showToast('Provide title and markdown', 'error');
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
    showToast(`Draft #${data.id} saved to repository!`, 'success');
  } catch (err) {
    showToast(err.message, 'error');
  }
});

// Upload to Blogger
el.btnUploadBlogger.addEventListener('click', async () => {
  if (!state.googleConnected) {
    showToast('Google account not connected yet.', 'error');
    return;
  }
  const blogId = el.activeBlogSelector.value;
  if (!blogId) {
    showToast('Select a Blogger blog first.', 'error');
    return;
  }
  const title = el.editorTitle.value.trim();
  const rendered_html = state.currentArticle.renderedHtml;
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
    if (!res.ok) throw new Error(data.detail || 'Upload failed');
    showToast(`Blogger draft created! Post ID: ${data.post_id}`, 'success');
  } catch (err) {
    showToast(err.message, 'error');
  }
});

// Preview Toggles
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

// Google OAuth Setup & Error 400 Diagnosis
async function checkOAuthStatus() {
  try {
    const res = await fetch('/api/oauth/status');
    const data = await res.json();
    state.googleConnected = data.connected;

    if (data.configured_redirect_uri) {
      el.oauthRedirectDisplay.value = data.configured_redirect_uri;
    }

    if (data.connected) {
      el.googleIndicator.className = 'indicator green';
      el.googleStatusText.textContent = `Blogger: ${data.user.email || 'Online'}`;
      el.connectGoogleBtn.textContent = 'Connected ✓';
      loadBloggerBlogs();
    } else {
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
    if (data.redirect_uri) {
      el.oauthRedirectDisplay.value = data.redirect_uri;
    }
    if (data.url) {
      window.location.href = data.url;
    }
  } catch (err) {
    showToast('Login failed: ' + err.message, 'error');
  }
}

el.connectGoogleBtn.addEventListener('click', triggerGoogleLogin);
el.btnLoginGoogleAlt.addEventListener('click', triggerGoogleLogin);

el.btnCopyRedirect.addEventListener('click', () => {
  navigator.clipboard.writeText(el.oauthRedirectDisplay.value);
  showToast('Copied Redirect URI to clipboard!', 'success');
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
    console.error(err);
  }
}

async function loadBloggerPosts(blogId) {
  try {
    const res = await fetch(`/api/blogger/posts?blog_id=${blogId}&limit=20`);
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

// Render eBook Preview
function renderLiveEbookPreview() {
  el.ebookLivePreview.innerHTML = `
    <div style="padding:20px; border:2px solid #4f46e5; border-radius:12px; background:linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%); color:#ffffff;">
      <span style="display:inline-block; padding:3px 10px; font-size:11px; font-weight:700; background:#fbbf24; color:#000; border-radius:12px; margin-bottom:8px;">★ Recommended Guide</span>
      <h4 style="margin:0 0 6px 0; font-size:18px; color:#fff;">Code to Career — The Python Fresher to Job-Ready Developer</h4>
      <p style="margin:0 0 10px 0; font-size:13px; color:#cbd5e1;">Step-by-step interview roadmap, hands-on production code, and architecture recipes.</p>
      <div style="display:flex; align-items:center; justify-content:space-between;">
        <span style="font-size:20px; font-weight:800; color:#34d399;">₹499</span>
        <a href="https://codetocareer52.myinstamojo.com/product/code-to-career" target="_blank" class="btn btn-primary btn-sm">Get on Instamojo &rarr;</a>
      </div>
    </div>
  `;
}

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

// Startup
window.addEventListener('DOMContentLoaded', () => {
  loadTrendingTopics();
  checkOAuthStatus();
  renderLiveEbookPreview();

  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('oauth_success')) {
    showToast('Google account connected successfully!', 'success');
    window.history.replaceState({}, document.title, window.location.pathname);
  }
});
