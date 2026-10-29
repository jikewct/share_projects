(function (global) {
  'use strict';
  const instances = new WeakMap();
  let nextId = 0;
  const words = {
    en: {
      skip: 'Skip to content', about: 'About', research: 'Research', publications: 'Publications', experience: 'Experience', contact: 'Contact',
      menu: 'Open navigation', closeMenu: 'Close navigation', subtitle: 'PERSONAL ACADEMIC HOMEPAGE', photo: 'Your photo',
      template: 'Template preview', templateNote: 'Personal details and publications below are placeholders.',
      intro: 'A little about me', interests: 'Research interests', interestsNote: 'The questions and ideas that guide my work.',
      papersNote: 'Explore papers, abstracts, and research resources.', search: 'Search title, author, or venue…', searchLabel: 'Search publications',
      all: 'All papers', conference: 'Conference', journal: 'Journal', preprint: 'Preprint', selected: 'Selected',
      year: 'TBD', abstract: 'Abstract', paper: 'Paper', code: 'Code', project: 'Project', bibtex: 'BibTeX', copy: 'Copy citation', copied: 'Copied',
      copyFailed: 'Unable to copy. Please select the citation text below.', empty: 'No matching publications.', clear: 'Clear filters',
      education: 'Education & appointments', service: 'Academic service', cv: 'Curriculum vitae',
      contactHeading: 'Let’s start a conversation.', contactNote: 'For research discussions and potential collaborations, feel free to get in touch.',
      emailMissing: 'Email address to be added', linksMissing: 'Academic links to be added', footer: 'Personal academic homepage',
      results: n => `${n} ${n === 1 ? 'publication' : 'publications'}`, example: 'Placeholder', backTop: 'Back to top'
    },
    zh: {
      skip: '跳转到正文', about: '个人介绍', research: '研究方向', publications: '论文发表', experience: '学术经历', contact: '联系方式',
      menu: '打开导航菜单', closeMenu: '关闭导航菜单', subtitle: '个人学术主页 · PERSONAL ACADEMIC HOMEPAGE', photo: '照片待添加',
      template: '模板预览', templateNote: '下方个人资料与论文均为占位内容，待替换为真实信息。',
      intro: '关于我', interests: '研究兴趣', interestsNote: '关注的问题，与持续探索的方向。',
      papersNote: '浏览论文、摘要和相关研究资源。', search: '搜索论文标题、作者或发表场所…', searchLabel: '搜索论文',
      all: '全部论文', conference: '会议论文', journal: '期刊论文', preprint: '预印本', selected: '代表作',
      year: '待添加', abstract: '摘要', paper: '论文', code: '代码', project: '项目主页', bibtex: 'BibTeX', copy: '复制引用', copied: '已复制',
      copyFailed: '无法自动复制，请选择下方引用文本手动复制。', empty: '没有找到匹配的论文。', clear: '清除筛选',
      education: '教育与工作经历', service: '学术服务', cv: '个人简历',
      contactHeading: '从一次交流开始。', contactNote: '欢迎就研究问题、学术讨论与潜在合作与我联系。',
      emailMissing: '邮箱地址待添加', linksMissing: '学术链接待添加', footer: '个人学术主页',
      results: n => `共 ${n} 篇论文`, example: '占位内容', backTop: '回到顶部'
    }
  };
  const icons = {
    arrow: '<path d="M7 17 17 7M7 7h10v10"/>',
    mail: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
    search: '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 4 4"/>',
    location: '<path d="M19 10c0 5-7 11-7 11S5 15 5 10a7 7 0 1 1 14 0Z"/><circle cx="12" cy="10" r="2"/>',
    menu: '<path d="M4 7h16M4 12h16M4 17h16"/>',
    book: '<path d="M12 6v15M3 4c4-1 7 0 9 2 2-2 5-3 9-2v15c-4-1-7 0-9 2-2-2-5-3-9-2V4Z"/>',
    file: '<path d="M14 3H5v18h14V8l-5-5Zm0 0v5h5M8 12h8M8 16h6"/>',
    plus: '<path d="M12 5v14M5 12h14"/>', up: '<path d="m6 12 6-6 6 6M12 6v14"/>'
  };
  const icon = name => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${icons[name]}</svg>`;
  const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]);
  function safeURL(value) {
    if (typeof value !== 'string' || !value.trim()) return '';
    try { return ['http:', 'https:', 'file:'].includes(new URL(value, document.baseURI).protocol) ? value : ''; }
    catch { return ''; }
  }

  function mount(target, options = {}) {
    const root = typeof target === 'string' ? document.querySelector(target) : target;
    if (!(root instanceof Element)) throw new TypeError('Homepage.mount 需要有效的容器元素或选择器。');
    const profile = options.profile || {};
    const publications = options.publications || [];
    if (!Array.isArray(publications)) throw new TypeError('publications 必须为数组。');
    instances.get(root)?.destroy();
    const id = `academic-${++nextId}`;
    const controller = new AbortController();
    let language = options.language === 'zh' ? 'zh' : 'en';
    let filter = 'all';
    let query = '';
    const local = value => typeof value === 'object' && value !== null ? (value[language] ?? value.en ?? value.zh ?? '') : (value ?? '');
    const t = () => words[language];
    const sectionId = name => `${id}-${name}`;
    const sectionLink = (name, text, className = '') => `<a class="${className}" href="#${sectionId(name)}" data-section="${name}">${text}</a>`;
    const resourceLink = (url, text, className = '') => safeURL(url) ? `<a class="${className}" href="${esc(safeURL(url))}" target="_blank" rel="noopener noreferrer">${text}${icon('arrow')}</a>` : '';
    const fullName = () => local(profile.name) || (language === 'zh' ? '你的姓名' : 'Your Name');
    const emailLink = () => profile.email && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(profile.email)
      ? `<a class="ah-email" href="mailto:${esc(encodeURIComponent(profile.email))}">${icon('mail')}<span>${esc(profile.email)}</span></a>`
      : `<span class="ah-email ah-muted">${icon('mail')}<span>${t().emailMissing}</span></span>`;
    const profileLinks = () => [resourceLink(profile.scholar, 'Google Scholar', 'ah-profile-link'), resourceLink(profile.github, 'GitHub', 'ah-profile-link'), resourceLink(profile.orcid, 'ORCID', 'ah-profile-link'), resourceLink(profile.cv, t().cv, 'ah-profile-link')].filter(Boolean).join('');

    function renderExperience() {
      const education = profile.education || [];
      const service = profile.service || [];
      if (!education.length && !service.length) return '';
      return `<section class="ah-section" id="${sectionId('experience')}" aria-labelledby="${id}-experience-heading"><div class="ah-section-heading"><span class="ah-section-number">04</span><h2 id="${id}-experience-heading">${t().experience}</h2></div>
        ${education.length ? `<h3 class="ah-subheading">${t().education}</h3><div class="ah-timeline">${education.map(item => `<article><span class="ah-period">${esc(local(item.period))}</span><div><h4>${esc(local(item.title))}</h4><p>${esc(local(item.institution))}</p>${item.description ? `<p class="ah-muted">${esc(local(item.description))}</p>` : ''}</div></article>`).join('')}</div>` : ''}
        ${service.length ? `<div class="ah-service"><h3 class="ah-subheading">${t().service}</h3><ul>${service.map(item => `<li>${esc(local(item))}</li>`).join('')}</ul></div>` : ''}</section>`;
    }

    function render() {
      const links = profileLinks();
      const photo = safeURL(profile.photo);
      root.innerHTML = `<div class="academic-homepage" lang="${language === 'zh' ? 'zh-CN' : 'en'}" id="${sectionId('top')}">
        ${sectionLink('about', t().skip, 'ah-skip')}
        <header class="ah-header"><div class="ah-container ah-header-inner">${sectionLink('top', `<span class="ah-monogram">${esc(profile.initials || 'YN')}<i></i></span><span class="ah-brand-label">${esc(fullName())}</span>`, 'ah-brand')}
          <div class="ah-header-right"><nav class="ah-nav" id="${id}-nav" aria-label="${language === 'zh' ? '主导航' : 'Main navigation'}">${['about', 'research', 'publications', ...(profile.education?.length || profile.service?.length ? ['experience'] : [])].map(name => sectionLink(name, t()[name])).join('')}</nav>
          <div class="ah-language" role="group" aria-label="Language / 语言"><button type="button" data-language="en" aria-pressed="${language === 'en'}">EN</button><span>/</span><button type="button" data-language="zh" aria-pressed="${language === 'zh'}">中文</button></div><button type="button" class="ah-menu" aria-label="${t().menu}" aria-expanded="false" aria-controls="${id}-nav">${icon('menu')}</button></div>
        </div></header>
        <div class="ah-container ah-layout"><aside class="ah-profile" aria-label="${language === 'zh' ? '个人资料' : 'Profile'}"><div class="ah-portrait">${photo ? `<img src="${esc(photo)}" alt="${esc(fullName())}" width="260" height="300">` : `<span class="ah-portrait-initials" aria-hidden="true">${esc(profile.initials || 'YN')}</span><span class="ah-portrait-caption">${t().photo}</span>`}<span class="ah-portrait-corner" aria-hidden="true">+</span></div>
          <h2 class="ah-profile-name">${esc(fullName())}</h2><p class="ah-profile-role">${esc(local(profile.role))}</p><p class="ah-institution">${esc(local(profile.institution))}</p>${profile.location ? `<p class="ah-location">${icon('location')}${esc(local(profile.location))}</p>` : ''}<div class="ah-profile-divider"></div><div class="ah-profile-links">${emailLink()}${links || `<span class="ah-links-pending">${t().linksMissing}</span>`}</div><div class="ah-profile-foot"><span class="ah-small-dot"></span>${language === 'zh' ? '个人学术主页' : 'Academic portfolio'}</div>
        </aside><main class="ah-main">
          ${options.isTemplate ? `<div class="ah-template-note"><span>${t().template}</span>${t().templateNote}</div>` : ''}
          <section class="ah-intro" id="${sectionId('about')}" aria-labelledby="${id}-name"><div class="ah-kicker">${t().subtitle}</div><h1 id="${id}-name">${esc(fullName())}<span class="ah-name-dot">.</span></h1>${profile.alternateName ? `<p class="ah-alternate-name">${esc(local(profile.alternateName))}</p>` : ''}<p class="ah-tagline">${esc(local(profile.tagline))}</p><div class="ah-about-heading"><span class="ah-section-number">01</span><h2>${t().intro}</h2></div><div class="ah-biography">${(profile.biography || []).map(paragraph => `<p>${esc(local(paragraph))}</p>`).join('')}</div><div class="ah-intro-links">${sectionLink('publications', `${t().publications} ${icon('arrow')}`, 'ah-primary-link')}${resourceLink(profile.cv, `${icon('file')}${t().cv}`, 'ah-secondary-link')}${sectionLink('contact', `${icon('mail')}${t().contact}`, 'ah-secondary-link')}</div></section>
          <section class="ah-section ah-research" id="${sectionId('research')}" aria-labelledby="${id}-research-heading"><div class="ah-section-heading"><span class="ah-section-number">02</span><h2 id="${id}-research-heading">${t().interests}</h2></div><p class="ah-section-description">${t().interestsNote}</p><div class="ah-research-grid">${(profile.research || []).map((item, index) => `<article><span class="ah-research-index">0${index + 1}</span><h3>${esc(local(item.title))}</h3><p>${esc(local(item.description))}</p></article>`).join('')}</div></section>
          <section class="ah-section ah-publications" id="${sectionId('publications')}" aria-labelledby="${id}-publications-heading"><div class="ah-section-heading"><span class="ah-section-number">03</span><h2 id="${id}-publications-heading">${t().publications}</h2><span class="ah-total">${publications.length}</span></div><p class="ah-section-description">${t().papersNote}</p><label class="ah-search">${icon('search')}<span class="ah-sr-only">${t().searchLabel}</span><input type="search" placeholder="${t().search}" value="${esc(query)}" autocomplete="off" data-search></label><div class="ah-publication-toolbar"><div class="ah-filters" role="group" aria-label="${language === 'zh' ? '论文类型筛选' : 'Filter by publication type'}">${['all', 'conference', 'journal', 'preprint'].map(type => `<button type="button" data-filter="${type}" aria-pressed="${filter === type}">${t()[type]}</button>`).join('')}</div><span class="ah-results-count" data-count role="status" aria-live="polite"></span></div><div data-publication-list></div></section>
          ${renderExperience()}
          <section class="ah-contact" id="${sectionId('contact')}" aria-labelledby="${id}-contact-heading"><span class="ah-kicker">${t().contact.toUpperCase()}</span><h2 id="${id}-contact-heading">${t().contactHeading}</h2><p>${esc(local(profile.contactNote) || t().contactNote)}</p>${emailLink()}<span class="ah-contact-decoration" aria-hidden="true">↗</span></section>
        </main></div><footer class="ah-container ah-footer"><span>© ${new Date().getFullYear()} ${esc(fullName())}<i>·</i>${t().footer}</span>${sectionLink('top', `${t().backTop}${icon('up')}`)}</footer>
      </div>`;
      renderPublications();
    }

    function renderPublications() {
      const normalizedQuery = query.toLocaleLowerCase().trim();
      const filtered = publications.map((paper, index) => ({ paper, index })).filter(({ paper }) => {
        const searchable = [paper.title, paper.venue, ...(paper.authors || []).map(author => typeof author === 'string' ? author : author.name)].flatMap(value => typeof value === 'object' && value !== null ? Object.values(value) : [value]).join(' ').toLocaleLowerCase();
        return (filter === 'all' || paper.type === filter) && searchable.includes(normalizedQuery);
      }).sort((a, b) => (Number(b.paper.year) || 0) - (Number(a.paper.year) || 0));
      const scope = root.querySelector('.academic-homepage');
      scope.querySelector('[data-count]').textContent = t().results(filtered.length);
      scope.querySelectorAll('[data-filter]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.filter === filter)));
      const groups = new Map();
      filtered.forEach(item => { const year = item.paper.year || t().year; if (!groups.has(year)) groups.set(year, []); groups.get(year).push(item); });
      scope.querySelector('[data-publication-list]').innerHTML = filtered.length ? Array.from(groups, ([year, entries]) => `<div class="ah-publication-year"><h3>${esc(year)}</h3><div>${entries.map(({ paper, index }) => {
        const authors = (paper.authors || []).map(author => { const name = typeof author === 'string' ? author : local(author.name); return typeof author === 'object' && author.isMe ? `<strong>${esc(name)}</strong>` : esc(name); }).join(', ');
        const links = [resourceLink(paper.paper, t().paper), resourceLink(paper.code, t().code), resourceLink(paper.project, t().project)].join('');
        return `<article class="ah-paper"><div class="ah-paper-top"><span class="ah-paper-type">${esc(t()[paper.type] || paper.type || t().publications)}</span>${paper.selected ? `<span class="ah-selected">${t().selected}</span>` : ''}${paper.placeholder ? `<span class="ah-placeholder">${t().example}</span>` : ''}</div><h4>${esc(local(paper.title))}</h4><p class="ah-authors">${authors}</p><p class="ah-venue">${esc(local(paper.venue))}${paper.note ? `<span> · ${esc(local(paper.note))}</span>` : ''}</p>${links ? `<div class="ah-paper-links">${links}</div>` : ''}${paper.abstract ? `<details class="ah-abstract"><summary>${t().abstract}${icon('plus')}</summary><p>${esc(local(paper.abstract))}</p></details>` : ''}${paper.bibtex ? `<details class="ah-bibtex"><summary>${t().bibtex}${icon('plus')}</summary><button type="button" data-copy="${index}">${t().copy}</button><span class="ah-copy-status" role="status" data-copy-status="${index}"></span><pre>${esc(paper.bibtex)}</pre></details>` : ''}</article>`;
      }).join('')}</div></div>`).join('') : `<div class="ah-empty">${icon('book')}<p>${t().empty}</p><button type="button" data-clear>${t().clear}</button></div>`;
    }

    function closeMenu() {
      const menu = root.querySelector('.ah-menu');
      root.querySelector('.ah-nav').classList.remove('is-open');
      menu.setAttribute('aria-expanded', 'false'); menu.setAttribute('aria-label', t().menu);
    }
    root.addEventListener('click', async event => {
      const control = event.target.closest('a, button');
      if (!control || !root.contains(control)) return;
      if (control.hasAttribute('data-language')) {
        if (language === control.dataset.language) return;
        language = control.dataset.language; render();
        root.querySelector(`[data-language="${language}"]`).focus({ preventScroll: true });
        if (options.syncDocument) updateDocument();
        if (typeof options.onLanguageChange === 'function') options.onLanguageChange(language);
      } else if (control.hasAttribute('data-section')) {
        event.preventDefault(); closeMenu();
        const destination = control.dataset.section === 'top' ? root.querySelector('.academic-homepage') : root.querySelector(`#${sectionId(control.dataset.section)}`);
        if (!destination) return;
        destination.tabIndex = -1; destination.focus({ preventScroll: true });
        destination.scrollIntoView({ behavior: global.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' });
      } else if (control.matches('.ah-menu')) {
        const open = control.getAttribute('aria-expanded') !== 'true';
        root.querySelector('.ah-nav').classList.toggle('is-open', open);
        control.setAttribute('aria-expanded', String(open)); control.setAttribute('aria-label', open ? t().closeMenu : t().menu);
      } else if (control.hasAttribute('data-filter')) { filter = control.dataset.filter; renderPublications(); }
      else if (control.hasAttribute('data-clear')) {
        filter = 'all'; query = ''; const search = root.querySelector('[data-search]'); search.value = ''; renderPublications(); search.focus();
      } else if (control.hasAttribute('data-copy')) {
        const status = root.querySelector(`[data-copy-status="${control.dataset.copy}"]`);
        try { await navigator.clipboard.writeText(publications[Number(control.dataset.copy)].bibtex); if (status.isConnected) status.textContent = t().copied; }
        catch { if (status.isConnected) status.textContent = t().copyFailed; }
      }
    }, { signal: controller.signal });
    root.addEventListener('input', event => { if (event.target.matches('[data-search]')) { query = event.target.value; renderPublications(); } }, { signal: controller.signal });
    root.addEventListener('keydown', event => { if (event.key === 'Escape' && root.querySelector('.ah-menu').getAttribute('aria-expanded') === 'true') { closeMenu(); root.querySelector('.ah-menu').focus(); } }, { signal: controller.signal });
    function updateDocument() {
      document.documentElement.lang = language === 'zh' ? 'zh-CN' : 'en';
      document.title = `${fullName()} — ${t().footer}`;
      const description = document.querySelector('meta[name="description"]');
      if (description) description.content = `${fullName()}. ${local(profile.role)}. ${local(profile.institution)}. ${local(profile.tagline)}`;
    }
    render(); if (options.syncDocument) updateDocument();
    const instance = { destroy() { if (instances.get(root) !== instance) return; controller.abort(); root.replaceChildren(); instances.delete(root); } };
    instances.set(root, instance); return instance;
  }
  global.Homepage = Object.freeze({ mount });
})(window);
