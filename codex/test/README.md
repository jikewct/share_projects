# 个人学术 Homepage

原生 HTML / CSS / JavaScript 个人学术主页，支持英文、中文切换，无第三方依赖或构建步骤。

包含个人照片与资料、个人介绍、研究方向、论文发表、教育与工作经历、学术服务和联系方式。

## 运行

直接打开 `index.html`，或者启动静态服务器：

```sh
python3 -m http.server 8080 --bind 127.0.0.1
```

访问 `http://127.0.0.1:8080`。

## 填入个人资料

所有内容集中在 `main.js`，请替换占位内容：

- `language`：默认语言，`en` 或 `zh`。
- `profile.name`、`alternateName`、`initials`：姓名、另一语言的姓名及头像占位字母。
- `profile.role`、`institution`、`location`：职位、机构与所在地。
- `profile.photo`：个人照片相对路径，例如 `./assets/profile.jpg`。
- `profile.email`、`cv`、`scholar`、`github`、`orcid`：邮箱及相关链接；留空时不显示无效链接。
- `profile.biography`：介绍段落数组。
- `profile.research`：研究方向的标题与简介数组。
- `profile.education`：教育与工作经历，按希望的顺序排列。
- `profile.service`：学术服务数组，不需要时用 `[]`。
- `publications`：论文数组，按真实年份自动倒序分组。

双语字段用 `{ en: 'English text', zh: '中文文案' }`。论文标题、作者、机构等也可以直接用字符串，缺少一种语言时会使用另一种语言。文本按纯文本渲染，不支持 HTML 标签。

替换为真实资料后，将 `isTemplate` 改为 `false`，删除论文的 `placeholder: true` 或改为 `false`。

## 添加论文

```js
{
  title: { en: 'Actual publication title', zh: '真实论文标题' },
  authors: [
    { name: { en: 'Your Name', zh: '你的姓名' }, isMe: true },
    'Co-author'
  ],
  venue: 'Actual conference or journal',
  year: 2026,
  type: 'conference', // conference / journal / preprint
  selected: true,     // 显示代表作标记
  placeholder: false,
  abstract: { en: 'Actual abstract…', zh: '真实摘要……' },
  paper: 'https://your-publication-url',
  code: '',
  project: '',
  bibtex: ''         // 填入正式 BibTeX 后显示引用与复制按钮
}
```

请使用真实发表信息和链接。空链接不会生成按钮，摘要或 BibTeX 留空时不显示对应折叠区。引用复制需要浏览器允许剪贴板访问，失败时可手动选择引用文本。

## 接入已有页面

```html
<link rel="stylesheet" href="./homepage.css">
<div id="homepage"></div>
<script src="./homepage.js"></script>
<script>
  const homepage = Homepage.mount('#homepage', {
    language: 'en',
    profile: { name: { en: 'Your Name', zh: '你的姓名' } },
    publications: [],
    onLanguageChange(language) {
      // 如需持久化语言偏好，可在这里接入应用。
    }
  });
  // 离开页面时：homepage.destroy();
</script>
```

`syncDocument: true` 会同步浏览器标题、HTML 语言和页面描述；嵌入其他应用时默认不修改文档属性。重复挂载会清理旧实例，多实例的元素 ID、语言和筛选状态独立。挂载会替换容器原有内容，销毁后容器为空。

## 文件与样式

- `index.html`：页面入口与元数据。
- `main.js`：双语个人资料和论文数据。
- `homepage.js`：模块、语言切换、论文搜索、类型筛选及引用复制。
- `homepage.css`：桌面、手机和打印布局，`--ah-*` 变量控制配色。
- `homepage-preview.jpg`：页面预览截图。

CSS 以 `.academic-homepage` 为作用域，开头的 `:root` 与 `body` 两条规则用于独立演示，嵌入既有应用时可按需要移除。

支持键盘操作、Escape 关闭移动端导航、搜索空状态及减少动态效果的系统偏好。语言和筛选状态仅保存在当前页面内存中。
