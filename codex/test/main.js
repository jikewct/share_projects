/* 所有内容都是占位资料。替换后设置 isTemplate: false，并删除论文 placeholder 标记。
 * 双语字段支持 { en: 'English', zh: '中文' }，也可直接使用字符串。
 */
const academicProfile = {
  language: 'en',
  syncDocument: true,
  isTemplate: true,
  profile: {
    name: { en: 'Your Name', zh: '你的姓名' },
    alternateName: { en: '你的姓名', zh: 'Your Name' },
    initials: 'YN',
    role: { en: 'Your position / title', zh: '你的职位 / 学位' },
    institution: { en: 'Department · University / Institute', zh: '院系 · 大学 / 研究机构' },
    location: { en: 'City, Country', zh: '城市，国家' },
    tagline: { en: 'Research, curiosity, and the ideas in between.', zh: '以好奇心为起点，在研究中探索新的可能。' },
    photo: '',       // 例如 './assets/profile.jpg'
    email: '',      // 你的真实邮箱
    cv: '',         // 例如 './assets/cv.pdf'
    scholar: '',    // 你的 Google Scholar 主页
    github: '',     // 你的 GitHub 主页
    orcid: '',      // 你的 ORCID 主页
    biography: [
      { en: 'Introduce yourself here: your current position, department, and institution. You can also mention your academic background and the people or groups you work with.', zh: '在这里介绍自己：目前的职位、所在院系和机构，也可以写下你的学术背景，以及合作的导师或研究团队。' },
      { en: 'Describe the central questions of your research, the methods you use, and what motivates your work. This space is also a good place to highlight your broader research goals.', zh: '在这里介绍你的研究：关注哪些核心问题、采用什么方法，以及研究的动机与长期目标。' }
    ],
    research: [
      { title: { en: 'Research area one', zh: '研究方向一' }, description: { en: 'Add a short description of your first research interest and the questions you explore.', zh: '简要介绍你的第一个研究方向，以及希望探索的问题。' } },
      { title: { en: 'Research area two', zh: '研究方向二' }, description: { en: 'Describe another topic, method, or application that is central to your work.', zh: '介绍另一个关注的研究主题、方法或应用场景。' } },
      { title: { en: 'Research area three', zh: '研究方向三' }, description: { en: 'Share a related direction or an emerging question you are interested in.', zh: '介绍相关的研究方向，或你正在关注的新问题。' } }
    ],
    education: [
      { period: { en: 'Year — Present', zh: '年份 — 至今' }, title: { en: 'Current position / degree', zh: '当前职位 / 在读学位' }, institution: { en: 'Your university or research institute', zh: '你的大学或研究机构' }, description: { en: 'Department, research group, or advisor (optional).', zh: '院系、研究团队或导师（可选）。' } },
      { period: { en: 'Year — Year', zh: '年份 — 年份' }, title: { en: 'Previous degree / appointment', zh: '此前的学位 / 工作经历' }, institution: { en: 'Your previous institution', zh: '此前所在机构' } }
    ],
    service: [{ en: 'Add reviewing, program committee, or other academic service here.', zh: '在这里填写审稿、程序委员会或其他学术服务经历。' }]
  },
  // 真实年份填入 year 后，自动倒序分组。type: conference / journal / preprint。
  publications: [
    {
      title: { en: 'Your publication title goes here', zh: '在这里填写你的论文标题' },
      authors: [{ name: { en: 'Your Name', zh: '你的姓名' }, isMe: true }, 'Co-author Name'],
      venue: { en: 'Conference name · Venue details to add', zh: '会议名称 · 发表信息待添加' },
      year: '', type: 'conference', selected: true, placeholder: true,
      abstract: { en: 'Replace this placeholder with the actual abstract of your paper. You can include the research problem, approach, and key findings.', zh: '请将此占位内容替换为真实的论文摘要，介绍研究问题、所用方法与主要结论。' },
      paper: '', code: '', project: '', bibtex: ''
    },
    {
      title: { en: 'A second publication title goes here', zh: '在这里填写第二篇论文的标题' },
      authors: ['Co-author Name', { name: { en: 'Your Name', zh: '你的姓名' }, isMe: true }],
      venue: { en: 'Journal name · Volume and pages to add', zh: '期刊名称 · 卷期与页码待添加' },
      year: '', type: 'journal', selected: false, placeholder: true,
      abstract: { en: 'Add the abstract for this publication here.', zh: '在这里填写这篇论文的摘要。' },
      paper: '', code: '', project: '', bibtex: ''
    },
    {
      title: { en: 'An ongoing research manuscript', zh: '在研论文 / 预印本标题待添加' },
      authors: [{ name: { en: 'Your Name', zh: '你的姓名' }, isMe: true }, 'Co-author Name'],
      venue: { en: 'Preprint · Repository details to add', zh: '预印本 · 仓储信息待添加' },
      year: '', type: 'preprint', selected: false, placeholder: true,
      abstract: { en: 'Introduce the research in this preprint here.', zh: '在这里介绍这篇预印本的研究内容。' },
      paper: '', code: '', project: '', bibtex: ''
    }
  ]
};

Homepage.mount('#app', academicProfile);
