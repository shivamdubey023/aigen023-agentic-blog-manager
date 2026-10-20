/**
 * NextGen Tech Notes — Autonomous AI Agentic Bot Controller
 * Mobile-First, Serverless Persistent OAuth, 1-Click Autopilot & Monetization Vault
 */

const state = {
  activeTab: 'tab-autopilot',
  currentArticle: {
    id: null,
    title: '',
    metaDescription: '',
    topic: '',
    keyword: '',
    markdown: '',
    renderedHtml: '',
    schema: {},
    featuredImageUrl: '',
    diagramImageUrl: '',
    bloggerPostId: '',
    bloggerBlogId: '',
  },
  selectedStockImage: null,
  trendingPick: null,
  googleConnected: false,
  activeBlogId: '',
  products: [],
  affiliates: [],
  qualityReviewFresh: false,
  bloggerPosts: [],
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
  autopilotCustomKeyword: document.getElementById('autopilot-custom-keyword'),
  btnUseTopic: document.getElementById('btn-use-topic'),
  autopilotMonetizeType: document.getElementById('autopilot-monetize-type'),
  autopilotProductSelectGroup: document.getElementById('autopilot-product-select-group'),
  autopilotProductSelect: document.getElementById('autopilot-product-select'),
  autopilotAffiliateSelectGroup: document.getElementById('autopilot-affiliate-select-group'),
  autopilotAffiliateSelect: document.getElementById('autopilot-affiliate-select'),
  btnRunAutopilot: document.getElementById('btn-run-autopilot'),
  autopilotModel: document.getElementById('autopilot-model'),
  providerStatus: document.getElementById('provider-status'),
  autopilotSpinner: document.getElementById('autopilot-spinner'),
  autopilotResultCard: document.getElementById('autopilot-result-card'),
  autopilotResultBody: document.getElementById('autopilot-result-body'),
  btnOpenAutopilotInEditor: document.getElementById('btn-open-autopilot-in-editor'),

  // Rewriter
  rewriteBloggerSelect: document.getElementById('rewrite-blogger-select'),
  btnFetchBloggerPosts: document.getElementById('btn-fetch-blogger-posts'),
  rewriteTitle: document.getElementById('rewrite-title'),
  rewriteContent: document.getElementById('rewrite-content'),
  rewriteProvider: document.getElementById('rewrite-provider'),
  rewriteModel: document.getElementById('rewrite-model'),
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
  imageSearchProvider: document.getElementById('image-search-provider'),
  imageSearchQuery: document.getElementById('image-search-query'),
  imageProviderStatus: document.getElementById('image-provider-status'),
  stockImageResults: document.getElementById('stock-image-results'),
  btnSearchStock: document.getElementById('btn-search-stock'),
  imgSpinner: document.getElementById('img-spinner'),
  imgDisplayContainer: document.getElementById('image-display-container'),
  imgActions: document.getElementById('image-actions'),
  btnInsertImageEditor: document.getElementById('btn-insert-image-editor'),

  // Editor
  editorTitle: document.getElementById('editor-title'),
  editorMetaDescription: document.getElementById('editor-meta-description'),
  markdownEditor: document.getElementById('markdown-editor'),
  wordCountBadge: document.getElementById('word-count-badge'),
  toggleToc: document.getElementById('toggle-toc'),
  toggleEbook: document.getElementById('toggle-ebook'),
  btnRefreshPreview: document.getElementById('btn-refresh-preview'),
  btnSaveDb: document.getElementById('btn-save-db'),
  btnUploadBlogger: document.getElementById('btn-upload-blogger'),
  btnDeleteLocal: document.getElementById('btn-delete-local-copy'),
  previewRendered: document.getElementById('preview-content-rendered'),
  previewHtml: document.getElementById('preview-content-html'),
  previewSchema: document.getElementById('preview-content-schema'),
  rawHtmlViewer: document.getElementById('raw-html-viewer'),
  rawSchemaViewer: document.getElementById('raw-schema-viewer'),
  qualityWarningsBanner: document.getElementById('quality-warnings-banner'),
  qualitySourceNotes: document.getElementById('quality-source-notes'),
  qualityReviewNotes: document.getElementById('quality-review-notes'),
  qualityReviewStatus: document.getElementById('quality-review-status'),
  qualityReviewCounts: document.getElementById('quality-review-counts'),
  qualityReviewFindings: document.getElementById('quality-review-findings'),
  qualityReportHistory: document.getElementById('quality-report-history'),
  qualityRevisionHistory: document.getElementById('quality-revision-history'),
  btnQualityCheck: document.getElementById('btn-quality-check'),
  btnQualityApprove: document.getElementById('btn-quality-approve'),
  btnQualityRequestChanges: document.getElementById('btn-quality-request-changes'),
  btnQualityHistory: document.getElementById('btn-quality-history'),
  btnQualityRevisions: document.getElementById('btn-quality-revisions'),
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
  btnSyncNavigation: document.getElementById('btn-sync-navigation'),
  bloggerPostsContainer: document.getElementById('blogger-posts-container'),
  oauthConnectionHelp: document.getElementById('oauth-connection-help'),
  bloggerNavigationPreview: document.getElementById('blogger-navigation-preview'),
  btnPreviewNavigation: document.getElementById('btn-preview-navigation'),
  internalLinkSearch: document.getElementById('internal-link-search'),
  internalLinkSelect: document.getElementById('editor-internal-link'),
  internalLinkPreview: document.getElementById('internal-link-preview'),
  btnInsertInternalLink: document.getElementById('btn-insert-internal-link'),
  diagramCaption: document.getElementById('diagram-caption'),
  diagramSteps: document.getElementById('diagram-steps'),
  btnInsertDiagram: document.getElementById('btn-insert-diagram'),
  imageAlt: document.getElementById('article-image-alt'),
  imageCaption: document.getElementById('article-image-caption'),
  btnInsertFeaturedImage: document.getElementById('btn-insert-featured-image'),
  vaultProductCount: document.getElementById('vault-product-count'),
  vaultAffiliateCount: document.getElementById('vault-affiliate-count'),
  vaultProductsCount: document.getElementById('vault-products-count'),
  vaultAffiliatesCount: document.getElementById('vault-affiliates-count'),
};

try {
  ['google_api_token', 'google_user'].forEach((key) => localStorage.removeItem(key));
} catch (err) {
  console.warn('Could not clear legacy Google token storage.', err);
}
try {
  ['blogger_token', 'blogger_user'].forEach((key) => {
    document.cookie = `${key}=; Max-Age=0; path=/; SameSite=Lax`;
  });
} catch (err) {
  console.warn('Could not clear legacy Google token cookies.', err);
}

function showToast(message, type = 'info') {
  if (!el.toastContainer) return;
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${type === 'success' ? '✓' : type === 'error' ? '⚠' : 'ℹ'}</span> <span>${escapeHtml(message)}</span>`;
  el.toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 4500);
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  })[char]);
}

function safeHttpsUrl(value) {
  try {
    const url = new URL(String(value));
    return url.protocol === 'https:' ? url.href : '';
  } catch {
    return '';
  }
}

function safeReviewSourceUrl(value) {
  try {
    const url = new URL(String(value), window.location.origin);
    return ['https:', 'http:'].includes(url.protocol) && !url.username && !url.password ? url.href : '';
  } catch {
    return '';
  }
}

// Google tokens never enter the browser; API requests use same-origin routes.
function getAuthHeaders(extraHeaders = {}) {
  return { 'Content-Type': 'application/json', ...extraHeaders };
}

const PROVIDER_MODELS = {
  groq: ['openai/gpt-oss-120b', 'openai/gpt-oss-20b', 'qwen/qwen3.8-27b'],
  gemini: ['gemini-3.8-flash', 'gemini-flash-latest', 'gemini-pro-latest'],
  cohere: ['command-r-08-2024', 'command-r-plus-08-2024'],
  openai: ['gpt-4o', 'gpt-4o-mini'],
  anthropic: ['claude-3-5-sonnet-20241022', 'claude-3-5-haiku-20241022'],
};

function setModelOptions(provider, select) {
  if (!select) return;
  select.innerHTML = '';
  const placeholder = document.createElement('option');
  placeholder.value = '';
  placeholder.textContent = provider ? 'Choose a model' : 'Choose a provider first';
  placeholder.disabled = true;
  placeholder.selected = true;
  select.appendChild(placeholder);
  (PROVIDER_MODELS[provider] || []).forEach((model) => {
    const option = document.createElement('option');
    option.value = model;
    option.textContent = model;
    select.appendChild(option);
  });
}

if (el.genProvider) {
  el.genProvider.addEventListener('change', () => setModelOptions(el.genProvider.value, el.genModel));
}
if (el.rewriteProvider) {
  el.rewriteProvider.addEventListener('change', () => setModelOptions(el.rewriteProvider.value, el.rewriteModel));
}
if (el.autopilotProvider) {
  el.autopilotProvider.addEventListener('change', () => setModelOptions(el.autopilotProvider.value, el.autopilotModel));
}

async function loadProviderStatus() {
  if (!el.providerStatus) return;
  try {
    const response = await fetch('/api/providers');
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Could not load provider configuration.');
    const configured = data.configured || {};
    [el.autopilotProvider, el.genProvider, el.rewriteProvider].filter(Boolean).forEach((select) => {
      Array.from(select.options).forEach((option) => {
        if (!option.value) return;
        const label = option.dataset.label || option.textContent;
        option.dataset.label = label;
        const available = configured[option.value] === true;
        option.disabled = !available;
        option.textContent = `${label} — ${available ? 'configured' : 'not configured'}`;
      });
    });
    const ready = Object.entries(configured).filter(([, available]) => available).map(([name]) => name);
    el.providerStatus.textContent = ready.length
      ? `Configured providers: ${ready.join(', ')}. Keys remain server-side.`
      : 'No AI provider is configured on the server. Add a provider key in Vercel environment variables; manual editing remains available.';
  } catch (error) {
    el.providerStatus.textContent = 'Provider configuration could not be checked. The server will report a clear error if generation is attempted.';
  }
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
function applyTrendingPick(pick) {
  state.trendingPick = pick;
  if (el.currentTrendingTitle) el.currentTrendingTitle.textContent = pick.topic;
  if (el.trendingCategory) el.trendingCategory.textContent = pick.category || 'Tech';
  if (el.trendingCpc) el.trendingCpc.textContent = 'Curated idea · no search metrics verified';
}

if (el.btnShuffleTopic) {
  el.btnShuffleTopic.addEventListener('click', async () => {
    try {
      const res = await fetch('/api/trending');
      const data = await res.json();
      if (data.random_suggestion) {
        applyTrendingPick(data.random_suggestion);
        showToast('Idea suggested. Choose “Use this idea” before generating.', 'info');
      }
    } catch (err) {
      showToast(err.message, 'error');
    }
  });
}

if (el.btnUseTopic) {
  el.btnUseTopic.addEventListener('click', () => {
    if (!state.trendingPick) {
      showToast('Request a topic idea first, then choose it here.', 'info');
      return;
    }
    el.autopilotCustomTopic.value = state.trendingPick.topic;
    el.autopilotCustomKeyword.value = state.trendingPick.keyword || '';
    el.autopilotCustomTopic.focus();
  });
}

// User-directed article generation
if (el.btnRunAutopilot) {
  el.btnRunAutopilot.addEventListener('click', async () => {
    const topic = el.autopilotCustomTopic.value.trim();
    const keyword = el.autopilotCustomKeyword.value.trim() || topic;
    const provider = el.autopilotProvider.value;
    if (topic.length < 2) {
      showToast('Enter a topic or explicitly choose a suggested idea before generating.', 'error');
      el.autopilotCustomTopic.focus();
      return;
    }
    if (!provider) {
      showToast('Choose an AI provider before generating.', 'error');
      el.autopilotProvider.focus();
      return;
    }
    const model = el.autopilotModel.value;
    if (!model) {
      showToast('Choose a model for the selected provider.', 'error');
      el.autopilotModel.focus();
      return;
    }
    const monetizeType = el.autopilotMonetizeType ? el.autopilotMonetizeType.value : 'none';
    const includeProduct = monetizeType === 'product';
    const productId = includeProduct && el.autopilotProductSelect.value ? parseInt(el.autopilotProductSelect.value, 10) : null;
    const includeAffiliate = monetizeType === 'affiliate';
    const affiliateId = includeAffiliate && el.autopilotAffiliateSelect.value ? parseInt(el.autopilotAffiliateSelect.value, 10) : null;
    if (includeProduct && !productId) {
      showToast('Choose the relevant product to include, or select a post without a product.', 'error');
      el.autopilotProductSelect.focus();
      return;
    }
    if (includeAffiliate && !affiliateId) {
      showToast('Choose the relevant affiliate link to include, or select a post without one.', 'error');
      el.autopilotAffiliateSelect.focus();
      return;
    }
    el.autopilotSpinner.classList.remove('hidden');
    el.btnRunAutopilot.disabled = true;

    try {
      showToast('Generating a draft for your selected topic...', 'info');
      const res = await fetch('/api/autopilot', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          topic,
          primary_keyword: keyword,
          provider,
          model,
          include_product: includeProduct,
          product_id: productId,
          include_affiliate: includeAffiliate,
          affiliate_id: affiliateId,
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
      state.currentArticle.featuredImageUrl = '';
      state.currentArticle.diagramImageUrl = '';
      state.currentArticle.bloggerPostId = '';
      state.currentArticle.bloggerBlogId = '';

      el.autopilotResultBody.innerHTML = `
        <div style="display:flex; flex-direction:column; gap:14px;">
          <h3 style="color:#ffffff; margin:4px 0 0 0; font-size:18px;">${escapeHtml(data.title)}</h3>
          <div style="display:flex; gap:10px; flex-wrap:wrap;">
            <span class="badge green">${data.word_count} words</span>
            <span class="badge blue">Draft #${data.article_id} Saved</span>
            ${includeProduct ? `<span class="badge purple">Product attached</span>` : ''}
          </div>
          <p class="section-desc">Review and edit the saved draft before creating a Blogger draft. Add an image only if useful.</p>
        </div>
      `;
      el.autopilotResultCard.classList.remove('hidden');
      showToast('Selected-topic draft generated and saved locally for review.', 'success');
      updateLocalDeleteButton();
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
    const provider = el.rewriteProvider.value;
    const model = el.rewriteModel.value;

    if (!title || !content) {
      showToast('Please provide both title and original content.', 'error');
      return;
    }
    if (!provider || !model) {
      showToast('Choose a configured AI provider and model before rewriting.', 'error');
      return;
    }

    el.rewriteSpinner.classList.remove('hidden');
    el.btnRunRewrite.disabled = true;

    try {
      showToast('Generating editorial suggestions for the selected content...', 'info');
      const res = await fetch('/api/rewrite', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          provider,
          model,
          original_title: title,
          original_content: content,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Rewrite failed');

      state.currentArticle = {
        id: null,
        title: data.title,
        metaDescription: '',
        topic: title,
        keyword: title,
        markdown: data.markdown,
        renderedHtml: '',
        schema: {},
        featuredImageUrl: '',
        diagramImageUrl: '',
        bloggerPostId: '',
        bloggerBlogId: '',
      };
      updateLocalDeleteButton();

      el.rewriteResultBox.innerHTML = `
        <div>
          <h3 style="color:#34d399; margin-top:0;">Expansion Complete!</h3>
          <p style="font-size:14px; color:#cbd5e1;">Generated <strong>${data.word_count} words</strong>. Review code examples, references, and factual claims before use.</p>
          <div style="background:#0f172a; padding:12px; border-radius:8px; max-height:220px; overflow-y:auto; font-family:monospace; font-size:12px; color:#94a3b8; white-space:pre-wrap;">
            ${escapeHtml(data.markdown.slice(0, 1000))}...
          </div>
        </div>
      `;
      el.rewriteActions.classList.remove('hidden');
      showToast('Editorial draft generated. Review it before saving or publishing.', 'success');
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

    if (!topic) {
      showToast('Enter a topic before generating.', 'error');
      el.genTopic.focus();
      return;
    }
    if (!provider) {
      showToast('Choose an AI provider before generating.', 'error');
      el.genProvider.focus();
      return;
    }

    el.genSpinner.classList.remove('hidden');
    el.genBtn.disabled = true;

    try {
      showToast('Generating a draft for your selected topic...', 'info');
      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ provider, model, topic, primary_keyword: keyword, audience, notes }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Generation failed');

      state.currentArticle = {
        id: null,
        title: data.title,
        metaDescription: '',
        topic,
        keyword: keyword || topic,
        markdown: data.markdown,
        renderedHtml: '',
        schema: {},
        featuredImageUrl: '',
        diagramImageUrl: '',
        bloggerPostId: '',
        bloggerBlogId: '',
      };
      updateLocalDeleteButton();

      el.genSummaryBox.innerHTML = `
        <div>
          <h3 style="color:#38bdf8; margin-top:0;">${escapeHtml(data.title)}</h3>
          <p style="font-size:14px; color:#cbd5e1;">Generated <strong>${data.word_count} words</strong>. Review the code, references, and factual claims before use.</p>
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
  state.currentArticle = {
    ...state.currentArticle,
    id: article.id ?? state.currentArticle.id,
    title: article.title || '',
    metaDescription: article.meta_description || article.metaDescription || '',
    topic: article.topic || state.currentArticle.topic,
    keyword: article.keyword || article.primary_keyword || state.currentArticle.keyword,
    markdown: article.markdown || article.markdown_body || '',
    bloggerPostId: article.bloggerPostId || article.blogger_post_id || '',
    bloggerBlogId: article.bloggerBlogId || article.blogger_blog_id || '',
  };
  el.editorTitle.value = article.title || '';
  el.editorMetaDescription.value = state.currentArticle.metaDescription;
  el.markdownEditor.value = state.currentArticle.markdown;
  resetQualityReview('Draft changed or loaded; run checks before recording a review.');
  updateLocalDeleteButton();
  renderPreview();
}

function resetQualityReview(message = 'Draft changed — run checks again.') {
  state.qualityReviewFresh = false;
  if (el.qualityReviewStatus) {
    el.qualityReviewStatus.textContent = message;
    el.qualityReviewStatus.className = 'badge yellow';
  }
  if (el.btnQualityApprove) el.btnQualityApprove.disabled = true;
  if (el.btnQualityRequestChanges) el.btnQualityRequestChanges.disabled = true;
}

function renderQualityReport(report) {
  const counts = report.finding_counts || {};
  const total = Object.values(counts).reduce((sum, value) => sum + Number(value || 0), 0);
  el.qualityReviewCounts.textContent = `${total} review finding${total === 1 ? '' : 's'} · High ${counts.high || 0} · Medium ${counts.medium || 0} · Low ${counts.low || 0} · Info ${counts.info || 0}. No overall score.`;
  if (!report.findings?.length) {
    el.qualityReviewFindings.innerHTML = '<p class="text-muted">No heuristic findings this pass. This does not establish originality, factual accuracy, citation validity, or publication readiness.</p>';
  } else {
    el.qualityReviewFindings.innerHTML = report.findings.map((finding) => {
      const sourceUrl = safeReviewSourceUrl(finding.source_url || '');
      const sourceLink = sourceUrl
        ? `<p><a href="${escapeHtml(sourceUrl)}" target="_blank" rel="noopener noreferrer">Inspect comparison source</a></p>`
        : '';
      const excerpt = finding.excerpt
        ? `<blockquote>${escapeHtml(finding.excerpt)}</blockquote>`
        : '';
      return `<article class="quality-finding" data-severity="${escapeHtml(finding.severity)}">
        <h3>${escapeHtml(finding.severity.toUpperCase())} · ${escapeHtml(finding.category)}: ${escapeHtml(finding.title)}</h3>
        ${excerpt}
        <p><strong>Evidence:</strong> ${escapeHtml(finding.evidence)}</p>
        <p><strong>Recommended action:</strong> ${escapeHtml(finding.recommendation)}</p>
        ${sourceLink}
      </article>`;
    }).join('');
  }
  const limitations = (report.limitations || []).map((item) => escapeHtml(item)).join(' ');
  if (limitations) {
    el.qualityReviewFindings.insertAdjacentHTML('beforeend', `<p class="section-desc">${limitations}</p>`);
  }
  const sources = report.source_material_reviewed || [];
  if (sources.length) {
    const sourceItems = sources.map((source) => {
      const safeUrl = safeReviewSourceUrl(source.url || '');
      const link = safeUrl
        ? `<a href="${escapeHtml(safeUrl)}" target="_blank" rel="noopener noreferrer">${escapeHtml(source.title || source.url)}</a>`
        : escapeHtml(source.title || 'Provided excerpt');
      return `<li><strong>${link}</strong><p>${escapeHtml(source.excerpt)}</p></li>`;
    }).join('');
    el.qualityReviewFindings.insertAdjacentHTML(
      'beforeend',
      `<div class="quality-finding"><h3>Source excerpts supplied for this review</h3><ul>${sourceItems}</ul></div>`,
    );
  }
}

function parseQualitySources() {
  const raw = el.qualitySourceNotes.value.trim();
  if (!raw) return [];
  return raw.split(/\r?\n/).filter(Boolean).map((line, index) => {
    const separator = line.indexOf('|');
    if (separator < 1 || !line.slice(separator + 1).trim()) {
      throw new Error(`Source line ${index + 1} must use: URL | relevant excerpt.`);
    }
    return {
      url: line.slice(0, separator).trim(),
      excerpt: line.slice(separator + 1).trim(),
    };
  });
}

async function runArticleQualityReview() {
  if (!state.currentArticle.id) await saveCurrentArticle();
  const sources = parseQualitySources();
  const response = await fetch(`/api/articles/${state.currentArticle.id}/quality-check`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ sources }),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || 'Quality review failed.');
  renderQualityReport(data.report);
  state.qualityReviewFresh = true;
  el.qualityReviewStatus.textContent = 'Fresh review · not an automatic publication decision';
  el.qualityReviewStatus.className = 'badge green';
  el.btnQualityApprove.disabled = false;
  el.btnQualityRequestChanges.disabled = false;
}

if (el.btnQualityCheck) {
  el.btnQualityCheck.addEventListener('click', async () => {
    el.btnQualityCheck.disabled = true;
    el.qualityReviewStatus.textContent = 'Saving draft and checking…';
    try {
      await saveCurrentArticle();
      await runArticleQualityReview();
      showToast('Quality report saved. Similarity flags require human interpretation.', 'success');
    } catch (err) {
      resetQualityReview(err.message);
      showToast(err.message, 'error');
    } finally {
      el.btnQualityCheck.disabled = false;
    }
  });
}

async function recordQualityDecision(decision) {
  if (!state.currentArticle.id || !state.qualityReviewFresh) {
    throw new Error('Save the current draft and run a fresh quality review first.');
  }
  if (decision === 'APPROVED' && !window.confirm('Confirm that you reviewed this draft and approve it for the next human-controlled workflow. This does not publish it.')) return;
  const response = await fetch(`/api/articles/${state.currentArticle.id}/review`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      decision,
      notes: el.qualityReviewNotes.value.trim(),
      confirmed: decision === 'APPROVED',
    }),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || 'Could not save the review decision.');
  el.qualityReviewStatus.textContent = decision === 'APPROVED' ? 'Human approved · not published' : 'Changes requested';
  el.qualityReviewStatus.className = decision === 'APPROVED' ? 'badge green' : 'badge yellow';
  showToast(decision === 'APPROVED' ? 'Review decision saved; no post was published.' : 'Changes-requested decision saved.', 'success');
}

if (el.btnQualityApprove) {
  el.btnQualityApprove.addEventListener('click', () => {
    recordQualityDecision('APPROVED').catch((err) => showToast(err.message, 'error'));
  });
}
if (el.btnQualityRequestChanges) {
  el.btnQualityRequestChanges.addEventListener('click', () => {
    recordQualityDecision('CHANGES_REQUESTED').catch((err) => showToast(err.message, 'error'));
  });
}

if (el.btnQualityHistory) {
  el.btnQualityHistory.addEventListener('click', async () => {
    const articleId = state.currentArticle.id;
    if (!articleId) {
      showToast('Save the draft before loading quality report history.', 'error');
      return;
    }
    try {
      const response = await fetch(`/api/articles/${articleId}/quality-reports`, { headers: getAuthHeaders() });
      const reports = await response.json();
      if (!response.ok) throw new Error(reports.detail || 'Could not load saved quality reports.');
      el.qualityReportHistory.innerHTML = reports.map((item, index) => `
        <div class="quality-revision">
          <span>Report ${escapeHtml(item.id)} · ${escapeHtml(item.created_at)} · ${item.is_current ? 'Current content' : 'Stale content'}</span>
          <button class="btn btn-secondary btn-sm" type="button" data-quality-report="${index}">View report</button>
        </div>`).join('') || '<p class="text-muted">No saved quality reports.</p>';
      el.qualityReportHistory.classList.remove('hidden');
      el.qualityReportHistory.querySelectorAll('[data-quality-report]').forEach((button) => {
        button.addEventListener('click', () => {
          const item = reports[Number(button.dataset.qualityReport)];
          renderQualityReport(item.report);
          state.qualityReviewFresh = Boolean(item.is_current);
          el.btnQualityApprove.disabled = !state.qualityReviewFresh;
          el.btnQualityRequestChanges.disabled = !state.qualityReviewFresh;
          el.qualityReviewStatus.textContent = item.is_current
            ? 'Saved report · current content'
            : 'Saved report · draft has since changed; recheck required';
          el.qualityReviewStatus.className = item.is_current ? 'badge green' : 'badge yellow';
        });
      });
    } catch (err) {
      showToast(err.message, 'error');
    }
  });
}

if (el.btnQualityRevisions) {
  el.btnQualityRevisions.addEventListener('click', async () => {
    const articleId = state.currentArticle.id;
    if (!articleId) {
      showToast('Save the draft before loading revision history.', 'error');
      return;
    }
    try {
      const response = await fetch(`/api/articles/${articleId}/revisions`, { headers: getAuthHeaders() });
      const revisions = await response.json();
      if (!response.ok) throw new Error(revisions.detail || 'Could not load revision history.');
      el.qualityRevisionHistory.innerHTML = revisions.map((revision) => `
        <div class="quality-revision">
          <span>Revision ${revision.revision_number} · ${escapeHtml(revision.title)} · ${escapeHtml(revision.created_at)}</span>
          <button class="btn btn-secondary btn-sm" type="button" data-revision="${revision.revision_number}">Restore to editor</button>
        </div>`).join('') || '<p class="text-muted">No saved revisions.</p>';
      el.qualityRevisionHistory.classList.remove('hidden');
      el.qualityRevisionHistory.querySelectorAll('[data-revision]').forEach((button, index) => {
        button.addEventListener('click', () => {
          if ((el.editorTitle.value || el.markdownEditor.value) && !window.confirm('Load this saved revision into the editor? Unsaved changes will be replaced.')) return;
          const revision = revisions[index];
          loadArticleIntoEditor({
            id: articleId,
            title: revision.title,
            meta_description: revision.meta_description,
            markdown_body: revision.markdown_body,
          });
          showToast(`Revision ${revision.revision_number} loaded. Save it as a new revision after editing.`, 'info');
        });
      });
    } catch (err) {
      showToast(err.message, 'error');
    }
  });
}

function updateLocalDeleteButton() {
  if (!el.btnDeleteLocal) return;
  const canDelete = Boolean(state.currentArticle.id && state.currentArticle.bloggerPostId);
  el.btnDeleteLocal.classList.toggle('hidden', !canDelete);
}

async function renderPreview() {
  const title = el.editorTitle.value.trim();
  const markdown = el.markdownEditor.value.trim();
  if (!markdown) {
    el.previewRendered.innerHTML = '<p class="text-muted">Type markdown on the left to see live rendered HTML.</p>';
    el.wordCountBadge.textContent = '0 words';
    return false;
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
        meta_description: el.editorMetaDescription.value.trim(),
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
      el.qualityWarningsBanner.innerHTML = `<strong>Article review warnings:</strong><ul>${data.warnings.map(w => `<li>${escapeHtml(w)}</li>`).join('')}</ul>`;
      el.qualityWarningsBanner.classList.remove('hidden');
    } else {
      el.qualityWarningsBanner.classList.add('hidden');
    }
    return true;
  } catch (err) {
    console.error('Render preview error', err);
    return false;
  }
}

if (el.btnRefreshPreview) el.btnRefreshPreview.addEventListener('click', renderPreview);
if (el.markdownEditor) {
  el.markdownEditor.addEventListener('input', debounce(renderPreview, 600));
  el.markdownEditor.addEventListener('input', () => resetQualityReview());
}
if (el.editorTitle) el.editorTitle.addEventListener('input', () => resetQualityReview());
if (el.editorMetaDescription) el.editorMetaDescription.addEventListener('input', () => resetQualityReview());
if (el.toggleToc) el.toggleToc.addEventListener('change', renderPreview);
if (el.toggleEbook) el.toggleEbook.addEventListener('change', renderPreview);

async function saveCurrentArticle() {
  const title = el.editorTitle.value.trim();
  const markdown = el.markdownEditor.value.trim();
  if (!title || !markdown) throw new Error('Title and content are required to save the draft.');
  if (!await renderPreview()) throw new Error('Could not render the current article; it was not saved.');
  const response = await fetch('/api/articles', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      topic: state.currentArticle.topic || title,
      primary_keyword: state.currentArticle.keyword || title,
      title,
      meta_description: el.editorMetaDescription.value.trim(),
      markdown_body: markdown,
      rendered_html: state.currentArticle.renderedHtml,
      schema_json: state.currentArticle.schema,
      article_id: state.currentArticle.id,
    }),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || 'Save failed.');
  state.currentArticle.id = data.id;
  state.currentArticle.title = title;
  state.currentArticle.markdown = markdown;
  updateLocalDeleteButton();
  return data.id;
}

// Save Draft to Local DB
if (el.btnSaveDb) {
  el.btnSaveDb.addEventListener('click', async () => {
    try {
      const articleId = await saveCurrentArticle();
      showToast(`Draft #${articleId} saved in database!`, 'success');
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
    if (!title) {
      showToast('Enter an article title before creating a Blogger draft.', 'error');
      return;
    }
    if (!window.confirm(`Create a Blogger draft for "${title}" in the selected blog? This will not publish it.`)) return;

    try {
      const articleId = await saveCurrentArticle();
      const currentHtml = state.currentArticle.renderedHtml;
      showToast('Creating the confirmed Blogger draft...', 'info');
      const res = await fetch('/api/blogger/draft', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          blog_id: blogId,
          title,
          rendered_html: currentHtml,
          article_id: articleId,
          confirmed: true,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Blogger upload failed');
      state.currentArticle.bloggerPostId = data.post_id;
      state.currentArticle.bloggerBlogId = blogId;
      updateLocalDeleteButton();
      showToast('Blogger draft created; it has not been published.', 'success');
      loadBloggerPosts(blogId);
    } catch (err) {
      showToast(err.message, 'error');
    }
  });
}

if (el.btnDeleteLocal) {
  el.btnDeleteLocal.addEventListener('click', async () => {
    const articleId = state.currentArticle.id;
    if (!articleId || !state.currentArticle.bloggerPostId) {
      showToast('Only a locally saved article linked to a confirmed Blogger draft can be removed.', 'error');
      return;
    }
    const confirmed = window.confirm('Delete this article from local storage? Its Blogger draft will remain unchanged.');
    if (!confirmed) return;
    try {
      const response = await fetch(`/api/articles/${articleId}?confirmed=true`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Could not delete local article.');
      state.currentArticle.id = null;
      state.currentArticle.bloggerPostId = '';
      state.currentArticle.bloggerBlogId = '';
      updateLocalDeleteButton();
      showToast('Local copy deleted. The Blogger draft was not changed.', 'success');
    } catch (err) {
      showToast(err.message, 'error');
    }
  });
}

async function loadImageProviderStatus() {
  if (!el.imageProviderStatus || !el.imageSearchProvider) return;
  try {
    const response = await fetch('/api/images/providers');
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Could not check image provider configuration.');
    const configured = data.configured || {};
    for (const option of el.imageSearchProvider.options) {
      if (!option.value) continue;
      const ready = Boolean(configured[option.value]);
      option.disabled = !ready;
      option.textContent = `${option.value === 'pexels' ? 'Pexels' : 'Unsplash'}${ready ? '' : ' (not configured)'}`;
    }
    const names = Object.keys(configured).filter((name) => configured[name]);
    el.imageProviderStatus.textContent = names.length
      ? `Configured: ${names.map((name) => name[0].toUpperCase() + name.slice(1)).join(', ')}. Keys remain server-side.`
      : 'No stock image API keys are configured. Add PEXELS_API_KEY or UNSPLASH_ACCESS_KEY in Vercel settings, or keep the article image-free.';
  } catch (err) {
    el.imageProviderStatus.textContent = `Image provider status unavailable: ${err.message}`;
  }
}

function renderStockImageResults(images) {
  el.stockImageResults.replaceChildren();
  el.imgDisplayContainer.replaceChildren();
  el.imgDisplayContainer.classList.add('hidden');
  state.selectedStockImage = null;
  el.imgActions.classList.add('hidden');
  if (!images.length) {
    el.stockImageResults.textContent = 'No photos found for this search. Try a broader phrase.';
    el.stockImageResults.className = 'image-display-empty';
    return;
  }
  el.stockImageResults.className = 'stock-image-grid';
  images.forEach((image) => {
    const card = document.createElement('article');
    card.className = 'stock-image-card';
    const preview = document.createElement('img');
    preview.src = image.thumbnail_url;
    preview.alt = image.alt_text || 'Stock photo result';
    preview.loading = 'lazy';
    preview.referrerPolicy = 'no-referrer';
    const attribution = document.createElement('p');
    attribution.textContent = `Photo by ${image.photographer} · ${image.provider}`;
    const select = document.createElement('button');
    select.type = 'button';
    select.className = 'btn btn-secondary btn-sm';
    select.textContent = 'Select this photo';
    select.addEventListener('click', () => {
      state.selectedStockImage = image;
      if (el.imageAlt) el.imageAlt.value = image.alt_text || '';
      if (el.imageCaption) el.imageCaption.value = '';
      el.imgDisplayContainer.replaceChildren();
      const selected = document.createElement('img');
      selected.src = image.image_url;
      selected.alt = image.alt_text || 'Selected stock photo';
      selected.loading = 'lazy';
      selected.referrerPolicy = 'no-referrer';
      selected.style.cssText = 'width:100%; border-radius:10px;';
      el.imgDisplayContainer.appendChild(selected);
      el.imgDisplayContainer.classList.remove('hidden');
      el.imgActions.classList.remove('hidden');
    });
    card.append(preview, attribution, select);
    el.stockImageResults.appendChild(card);
  });
}

if (el.btnSearchStock) {
  loadImageProviderStatus();
  el.btnSearchStock.addEventListener('click', async () => {
    const provider = el.imageSearchProvider.value;
    const query = el.imageSearchQuery.value.trim();
    if (!provider || query.length < 2) {
      showToast('Choose a configured source and enter a search phrase.', 'error');
      return;
    }
    el.imgSpinner.classList.remove('hidden');
    el.btnSearchStock.disabled = true;
    try {
      const response = await fetch('/api/images/search', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ provider, query }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Stock image search failed.');
      renderStockImageResults(data.images || []);
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      el.imgSpinner.classList.add('hidden');
      el.btnSearchStock.disabled = false;
    }
  });
}

function escapeMarkdownLabel(value) {
  return String(value).replace(/([\\[\]])/g, '\\$1').replace(/\r?\n/g, ' ').trim();
}

async function insertArticleImage(featured = false) {
  const image = state.selectedStockImage;
  if (!image) {
    showToast('Select a stock photo before inserting it.', 'error');
    return;
  }
  const alt = (el.imageAlt?.value || image.alt_text || '').trim();
  if (!alt) {
    showToast('Add descriptive alternative text before inserting the image.', 'error');
    el.imageAlt?.focus();
    return;
  }
  const provider = image.provider === 'pexels' ? 'Pexels' : 'Unsplash';
  const caption = (el.imageCaption?.value || '').trim();
  const captionPart = caption ? ` "${caption.replace(/(["\\])/g, '\\$1')}"` : '';
  const snippet = `![${escapeMarkdownLabel(alt)}](<${image.image_url}>${captionPart})\n\nPhoto by [${escapeMarkdownLabel(image.photographer)}](<${image.photographer_url}>) on [${provider}](<${image.source_url}>).\n\n`;
  const editor = el.markdownEditor;
  if (featured) {
    const titleMatch = editor.value.match(/^# [^\r\n]*\r?\n/);
    const offset = titleMatch ? titleMatch[0].length : 0;
    const prefix = offset && editor.value.slice(offset, offset + 1) !== '\n' ? '\n' : '';
    editor.setRangeText(`${prefix}\n${snippet}`, offset, offset, 'end');
  } else {
    editor.setRangeText(snippet, editor.selectionStart, editor.selectionEnd, 'end');
  }
  editor.focus();
  state.currentArticle.markdown = editor.value;
  resetQualityReview();
  await renderPreview();
  switchTab('tab-editor');
  showToast(`${provider} photo inserted with its alt text and source attribution. Save the draft to keep it.`, 'success');
}

if (el.btnInsertImageEditor) {
  el.btnInsertImageEditor.addEventListener('click', () => insertArticleImage(false));
}
if (el.btnInsertFeaturedImage) {
  el.btnInsertFeaturedImage.addEventListener('click', () => insertArticleImage(true));
}

if (el.btnInsertDiagram) {
  el.btnInsertDiagram.addEventListener('click', async () => {
    const caption = (el.diagramCaption.value || '').trim() || 'Process flow';
    const steps = (el.diagramSteps.value || '').trim();
    if (!steps) {
      showToast('Describe the real process steps before inserting a diagram.', 'error');
      el.diagramSteps.focus();
      return;
    }
    const safeTitle = caption.replace(/["\r\n]/g, ' ').trim();
    const diagram = `\`\`\`diagram title="${safeTitle}"\n${steps}\n\`\`\`\n\n`;
    el.markdownEditor.setRangeText(
      diagram,
      el.markdownEditor.selectionStart,
      el.markdownEditor.selectionEnd,
      'end',
    );
    el.markdownEditor.focus();
    state.currentArticle.markdown = el.markdownEditor.value;
    resetQualityReview();
    await renderPreview();
    showToast('Editable diagram specification inserted; inspect the SVG preview before saving.', 'success');
  });
}

function populateInternalLinkSuggestions(query = '') {
  if (!el.internalLinkSelect) return;
  const normalizedQuery = query.trim().toLocaleLowerCase();
  const livePosts = state.bloggerPosts.filter((post) => (
    post.status === 'LIVE'
    && safeHttpsUrl(post.url)
    && String(post.title || '').toLocaleLowerCase().includes(normalizedQuery)
  ));
  el.internalLinkSelect.replaceChildren();
  const placeholder = document.createElement('option');
  placeholder.value = '';
  placeholder.textContent = livePosts.length
    ? 'Choose a published article'
    : (state.googleConnected ? 'No matching published posts with a public URL' : 'Connect Blogger and load live posts');
  el.internalLinkSelect.appendChild(placeholder);
  livePosts.forEach((post) => {
    const option = document.createElement('option');
    option.value = String(post.id);
    const url = safeHttpsUrl(post.url);
    option.textContent = `${post.title} — ${url}`;
    option.dataset.title = post.title;
    option.dataset.url = url;
    el.internalLinkSelect.appendChild(option);
  });
  updateInternalLinkPreview();
}

function updateInternalLinkPreview() {
  if (!el.internalLinkPreview || !el.internalLinkSelect) return;
  const selected = el.internalLinkSelect.selectedOptions[0];
  const title = selected?.dataset.title || '';
  const url = safeHttpsUrl(selected?.dataset.url || '');
  el.internalLinkPreview.textContent = title && url
    ? `Link preview: ${title} → ${url}`
    : 'Select a published post to preview its destination URL.';
}

if (el.internalLinkSearch) {
  el.internalLinkSearch.addEventListener('input', () => populateInternalLinkSuggestions(el.internalLinkSearch.value));
}
if (el.internalLinkSelect) {
  el.internalLinkSelect.addEventListener('change', updateInternalLinkPreview);
}
if (el.btnInsertInternalLink) {
  el.btnInsertInternalLink.addEventListener('click', () => {
    const option = el.internalLinkSelect.selectedOptions[0];
    const url = safeHttpsUrl(option?.dataset.url || '');
    const title = option?.dataset.title?.trim() || '';
    if (!url || !title) {
      showToast('Choose a real published Blogger post with a public HTTPS URL.', 'error');
      return;
    }
    const link = `[${escapeMarkdownLabel(title)}](<${url}>)`;
    el.markdownEditor.setRangeText(link, el.markdownEditor.selectionStart, el.markdownEditor.selectionEnd, 'end');
    el.markdownEditor.focus();
    state.currentArticle.markdown = el.markdownEditor.value;
    resetQualityReview();
    renderPreview();
    showToast('Contextual link inserted to the selected live post. Save the draft to keep it.', 'success');
  });
}

if (el.btnSyncNavigation) {
  el.btnSyncNavigation.addEventListener('click', async () => {
    const blogId = el.activeBlogSelector ? el.activeBlogSelector.value : '';
    if (!state.googleConnected) {
      showToast('Connect your Google account before syncing live post navigation.', 'error');
      return;
    }
    if (!blogId) {
      showToast('Select a Blogger blog first.', 'error');
      return;
    }
    const confirmed = window.confirm(
      'This will update the HTML of LIVE posts in chronological order to add previous/next links. Draft posts are not edited. Continue?'
    );
    if (!confirmed) return;
    el.btnSyncNavigation.disabled = true;
    try {
      const response = await fetch('/api/blogger/navigation/sync', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ blog_id: blogId, confirmed: true }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Could not synchronize navigation.');
      const skipped = (data.skipped_missing_published_date || []).length;
      const failures = (data.errors || []).length;
      const summary = `Navigation sync: ${data.updated} updated, ${data.unchanged} unchanged, ${skipped} missing dates, ${failures} failed.`;
      showToast(summary, failures ? 'error' : 'success');
      if (failures) console.error('Blogger navigation sync errors', data.errors);
      await loadBloggerPosts(blogId);
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      el.btnSyncNavigation.disabled = false;
    }
  });
}

// Product Management (Instamojo / Books)
async function loadProducts() {
  try {
    const res = await fetch('/api/products');
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Products could not be loaded.');
    state.products = Array.isArray(data) ? data : [];
    renderProductsTable();
    populateProductSelects();
  } catch (err) {
    console.error('Failed to load products', err);
    if (el.productsTableContainer) el.productsTableContainer.innerHTML = `<p class="vault-empty" role="alert">${escapeHtml(err.message)}</p>`;
  }
}

function renderProductsTable() {
  if (!el.productsTableContainer) return;
  if (el.vaultProductCount) el.vaultProductCount.textContent = String(state.products.length);
  if (el.vaultProductsCount) el.vaultProductsCount.textContent = String(state.products.length);
  if (state.products.length === 0) {
    el.productsTableContainer.innerHTML = '<p class="vault-empty">No products yet. Add a guide above to build your catalog.</p>';
    if (el.ebookLivePreview) el.ebookLivePreview.innerHTML = '<p class="vault-empty">Your selected product preview will appear here.</p>';
    return;
  }
  let html = '<div class="vault-product-list">';
  state.products.forEach(p => {
    html += `
      <article class="vault-item">
        <div class="vault-item-copy">
          <strong class="vault-item-title">${escapeHtml(p.title)}</strong>
          <span class="vault-item-meta">${escapeHtml(p.url)}</span>
          ${p.price ? `<span class="vault-item-price">${escapeHtml(p.price)}</span>` : ''}
        </div>
        <button class="btn btn-secondary btn-sm" type="button" onclick="deleteProductItem(${Number(p.id)})" aria-label="Delete ${escapeHtml(p.title)}">Remove</button>
      </article>
    `;
  });
  html += '</div>';
  el.productsTableContainer.innerHTML = html;

  // Render live preview for the first product
  if (state.products.length > 0 && el.ebookLivePreview) {
    const prod = state.products[0];
    const productUrl = safeHttpsUrl(prod.url);
    const checkoutAction = productUrl
      ? `<a href="${escapeHtml(productUrl)}" target="_blank" rel="noopener noreferrer" class="btn btn-primary btn-sm">Get on Instamojo &rarr;</a>`
      : '<span class="btn btn-primary btn-sm" aria-disabled="true">Checkout URL unavailable</span>';
    el.ebookLivePreview.innerHTML = `
      <div class="vault-preview-card">
        <span class="badge yellow">${escapeHtml(prod.badge || 'Recommended guide')}</span>
        <h4>${escapeHtml(prod.title)}</h4>
        <p>${escapeHtml(prod.description || 'Digital guide')}</p>
        <div class="vault-preview-card-footer">
          <span class="vault-preview-price">${escapeHtml(prod.price || 'View details')}</span>
          ${checkoutAction}
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
    if (!res.ok) throw new Error(data.detail || 'Affiliate recommendations could not be loaded.');
    state.affiliates = Array.isArray(data) ? data : [];
    renderAffiliatesTable();
    populateAffiliateSelects();
  } catch (err) {
    console.error('Failed to load affiliates', err);
    if (el.affTableContainer) el.affTableContainer.innerHTML = `<p class="vault-empty" role="alert">${escapeHtml(err.message)}</p>`;
  }
}

function renderAffiliatesTable() {
  if (!el.affTableContainer) return;
  if (el.vaultAffiliateCount) el.vaultAffiliateCount.textContent = String(state.affiliates.length);
  if (el.vaultAffiliatesCount) el.vaultAffiliatesCount.textContent = String(state.affiliates.length);
  if (state.affiliates.length === 0) {
    el.affTableContainer.innerHTML = '<p class="vault-empty">No affiliate recommendations yet. Add a relevant link above.</p>';
    return;
  }
  let html = '<div class="vault-affiliate-list">';
  state.affiliates.forEach(a => {
    html += `
      <article class="vault-item">
        <div class="vault-item-copy">
          <strong class="vault-item-title">${escapeHtml(a.product_name)}</strong>
          <span class="vault-item-meta">${escapeHtml(a.tracking_url)}</span>
          <span class="vault-item-meta">Disclosure included · ${escapeHtml((a.trigger_keywords_list || []).join(', ') || 'No trigger keywords')}</span>
        </div>
        <button class="btn btn-secondary btn-sm" type="button" onclick="deleteAffiliateItem(${Number(a.id)})" aria-label="Delete ${escapeHtml(a.product_name)}">Remove</button>
      </article>
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
  try {
    const res = await fetch('/api/oauth/status', { headers: getAuthHeaders() });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Google connection status could not be checked.');
    state.googleConnected = data.connected;

    if (data.configured_redirect_uri && el.oauthRedirectDisplay) {
      el.oauthRedirectDisplay.value = data.configured_redirect_uri;
    }

    if (data.connected) {
      el.googleIndicator.className = 'indicator green';
      el.googleStatusText.textContent = `Google: ${data.user?.email || 'Connected'}`;
      el.connectGoogleBtn.textContent = 'Connected ✓';
      if (el.oauthConnectionHelp) {
        el.oauthConnectionHelp.textContent = 'Google API connected. Blogger and Search Console access use the saved server-side OAuth credentials.';
      }
      await loadBloggerBlogs();
    } else {
      el.googleIndicator.className = 'indicator red';
      const reconnectRequired = data.connection_state === 'reconnect_required';
      el.googleStatusText.textContent = reconnectRequired ? 'Google: Reconnect required' : 'Google: Not connected';
      el.connectGoogleBtn.textContent = reconnectRequired ? 'Reconnect Google' : 'Connect Google';
      if (el.oauthConnectionHelp) {
        el.oauthConnectionHelp.textContent = reconnectRequired
          ? 'A saved Google credential is incomplete or invalid. Reconnect Google. On Vercel, credentials must be stored in durable shared storage to remain available between server instances.'
          : data.configured
          ? 'OAuth client is configured, but Google has not been connected yet. Use the exact callback URL below in the Google OAuth client.'
          : 'Google OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET on the server, then add the exact callback URL below to the Google OAuth client.';
      }
    }
    return Boolean(data.connected);
  } catch (err) {
    console.error('OAuth status check failed', err);
    state.googleConnected = false;
    if (el.googleIndicator) el.googleIndicator.className = 'indicator red';
    if (el.googleStatusText) el.googleStatusText.textContent = 'Google: Status unavailable';
    if (el.oauthConnectionHelp) el.oauthConnectionHelp.textContent = err.message;
    return false;
  }
}

async function triggerGoogleLogin() {
  try {
    const res = await fetch('/api/oauth/url');
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Could not start Google OAuth.');
    if (data.redirect_uri && el.oauthRedirectDisplay) {
      el.oauthRedirectDisplay.value = data.redirect_uri;
    }
    if (data.url) {
      const authorizationUrl = new URL(data.url);
      if (authorizationUrl.origin !== 'https://accounts.google.com') {
        throw new Error('Google returned an unexpected authorization URL.');
      }
      window.location.assign(authorizationUrl.href);
      return;
    }
    throw new Error('Google OAuth did not return an authorization URL.');
  } catch (err) {
    if (el.oauthConnectionHelp) el.oauthConnectionHelp.textContent = err.message;
    showToast('Google connection could not start: ' + err.message, 'error');
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
    if (!res.ok) throw new Error(data.detail || 'Could not load Blogger blogs.');
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
      if (el.activeBlogSelector) el.activeBlogSelector.value = state.activeBlogId;
      await loadBloggerPosts(state.activeBlogId);
      return true;
    } else {
      if (el.activeBlogSelector) {
        el.activeBlogSelector.innerHTML = '<option value="">No Blogger blogs available to this account</option>';
      }
      if (el.oauthConnectionHelp) {
        el.oauthConnectionHelp.textContent = 'Google is connected, but this account returned no Blogger blogs. Check that the Blogger API is enabled and this Google account has access to the blog.';
      }
      return false;
    }
  } catch (err) {
    if (el.oauthConnectionHelp) el.oauthConnectionHelp.textContent = err.message;
    showToast(`Google is connected, but Blogger blogs could not load: ${err.message}`, 'error');
    return false;
  }
}

async function loadBloggerPosts(blogId) {
  if (!blogId) return false;
  try {
    const res = await fetch(`/api/blogger/posts?blog_id=${encodeURIComponent(blogId)}&limit=100`, { headers: getAuthHeaders() });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Could not load Blogger posts.');
    state.bloggerPosts = Array.isArray(data.posts) ? data.posts : [];
    populateInternalLinkSuggestions(el.internalLinkSearch?.value || '');
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

        tableHtml += `<tr style="border-bottom:1px solid var(--border-subtle);"><td style="padding:8px 6px;">${escapeHtml(p.title)}</td><td style="padding:8px 6px; text-align:right;"><button class="btn btn-secondary btn-sm" data-post-id="${escapeHtml(p.id)}">Rewrite</button></td></tr>`;
      });
      tableHtml += '</tbody></table>';
      el.bloggerPostsContainer.innerHTML = tableHtml;
      el.bloggerPostsContainer.querySelectorAll('[data-post-id]').forEach(button => {
        button.addEventListener('click', () => selectPostForRewrite(button.dataset.postId));
      });
      return true;
    } else {
      el.bloggerPostsContainer.innerHTML = '<p class="text-muted">No posts found in this blog.</p>';
      return true;
    }
  } catch (err) {
    el.bloggerPostsContainer.innerHTML = `<p style="color:var(--color-danger);">${escapeHtml(err.message)}</p>`;
    showToast(`Blogger connected, but posts could not load: ${err.message}`, 'error');
    return false;
  }
}

// WIRED: "Load Posts" button click listener
if (el.btnFetchBloggerPosts) {
  el.btnFetchBloggerPosts.addEventListener('click', async () => {
    if (!state.googleConnected) {
      showToast('Please connect your Google Blogger account first.', 'error');
      switchTab('tab-blogger');
      return;
    }
    showToast('Fetching latest posts from your Blogger blog...', 'info');
    const loaded = await loadBloggerBlogs();
    if (loaded) showToast('Blogger posts loaded into dropdown!', 'success');
  });
}

if (el.btnRefreshBlogs) {
  el.btnRefreshBlogs.addEventListener('click', async () => {
    showToast('Refreshing blog list...', 'info');
    if (await loadBloggerBlogs()) showToast('Blogger blogs refreshed.', 'success');
  });
}

if (el.activeBlogSelector) {
  el.activeBlogSelector.addEventListener('change', async () => {
    state.activeBlogId = el.activeBlogSelector.value;
    if (state.activeBlogId) {
      await loadBloggerPosts(state.activeBlogId);
      if (el.bloggerNavigationPreview) el.bloggerNavigationPreview.classList.add('hidden');
    }
  });
}

if (el.btnPreviewNavigation) {
  el.btnPreviewNavigation.addEventListener('click', async () => {
    const blogId = el.activeBlogSelector?.value || '';
    if (!blogId) {
      showToast('Connect Google and select a Blogger blog first.', 'error');
      return;
    }
    el.btnPreviewNavigation.disabled = true;
    el.btnPreviewNavigation.textContent = 'Loading live sequence…';
    try {
      const response = await fetch(`/api/blogger/navigation/preview?blog_id=${encodeURIComponent(blogId)}`, {
        headers: getAuthHeaders(),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Could not preview the live post sequence.');
      const posts = Array.isArray(data.posts) ? data.posts : [];
      if (!posts.length) {
        el.bloggerNavigationPreview.innerHTML = '<p class="navigation-preview-item">No published posts with valid publication dates were returned.</p>';
      } else {
        el.bloggerNavigationPreview.innerHTML = posts.map((post, index) => {
          const navTarget = (label, target, edge) => {
            if (!target?.title) return `${label}: ${edge}`;
            const url = safeHttpsUrl(target.url);
            return url
              ? `${label}: <a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(target.title)}</a>`
              : `${label}: ${escapeHtml(target.title)} (public URL unavailable; no link)`;
          };
          const previous = navTarget('Previous', post.previous, 'none (first post)');
          const next = navTarget('Next', post.next, 'none (latest post)');
          const missingUrl = !safeHttpsUrl(post.url) ? '<br>This post has no public URL and will not be linked.' : '';
          return `<div class="navigation-preview-item"><strong>${index + 1}. ${escapeHtml(post.title)}</strong><br>${previous}<br>${next}${missingUrl}</div>`;
        }).join('');
      }
      const skipped = data.skipped_missing_published_date || [];
      if (skipped.length) {
        el.bloggerNavigationPreview.insertAdjacentHTML(
          'beforeend',
          `<p class="navigation-preview-item">${skipped.length} LIVE post(s) were skipped because their published date was missing or invalid.</p>`,
        );
      }
      el.bloggerNavigationPreview.classList.remove('hidden');
    } catch (err) {
      el.bloggerNavigationPreview.innerHTML = `<p class="navigation-preview-item">${escapeHtml(err.message)}</p>`;
      el.bloggerNavigationPreview.classList.remove('hidden');
      showToast(err.message, 'error');
    } finally {
      el.btnPreviewNavigation.disabled = false;
      el.btnPreviewNavigation.textContent = 'Preview live sequence';
    }
  });
}

window.selectPostForRewrite = function(postId) {
  const opt = Array.from(el.rewriteBloggerSelect.options).find(option => option.value === String(postId));
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

async function startApplication() {
  loadProviderStatus();
  const connected = await checkOAuthStatus();
  loadProducts();
  loadAffiliates();

  const urlParams = new URLSearchParams(window.location.search);
  const oauthError = urlParams.get('oauth_error');
  if (oauthError) {
    const messages = {
      consent_not_completed: 'Google authorization was cancelled or denied. Try connecting again and approve Blogger access.',
      configuration_missing: 'Google OAuth credentials are missing on the server. Configure the client ID and secret.',
      connection_failed: 'Google authorization returned, but the server could not save or validate the connection. Check the callback URL, server logs, and persistent storage, then reconnect.',
    };
    showToast(messages[oauthError] || 'Google authorization failed. Restart the connection from the Blogger tab.', 'error');
    if (el.oauthConnectionHelp) el.oauthConnectionHelp.textContent = messages[oauthError] || 'Google authorization failed. Restart the connection from the Blogger tab.';
    window.history.replaceState({}, document.title, window.location.pathname);
  } else if (urlParams.get('oauth_success')) {
    if (connected) {
      showToast('Google connected; Blogger API access is ready.', 'success');
    } else {
      showToast('Google returned from authorization, but a valid saved token is not available. Reconnect and check server-side storage.', 'error');
    }
    window.history.replaceState({}, document.title, window.location.pathname);
  }
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
  void startApplication();
});
