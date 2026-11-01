/* WCO Data Model 4.3.0 ontology explorer — dependency-free. */
(() => {
  'use strict';

  const D = window.WCO_DATA;

  const LANG = (document.documentElement.lang || "zh").toLowerCase().startsWith("en") ? "en" : "zh";
  const I18N = {
    zh: {
      dataNotLoaded: "data.js 未加载。",
      copied: "已复制到剪贴板",
      catMetadata: "元数据", catRoot: "根单据", catContent: "内容", catParty: "当事人",
      catLocation: "地点", catAgency: "政府机构", catTransport: "运输工具",
      searchClass: "类", searchAttr: "数据属性", searchOp: "对象属性",
      noMatch: "没有匹配项", noClassMatch: "没有匹配的类", selectClass: "选择一个类查看详情",
      depth: "深度", paths: "个路径", inferred: "推断放置",
      classId: "WCO 类 ID", oisBranch: "OIS 分支", typicalPath: "典型路径", rawPath: "原始路径",
      dataProps: "数据属性", codeList: "代码表", noDirectAttrs: "该类没有直接数据属性。",
      firstAttrs: "仅显示前 9 个，共 {n} 个。可在属性索引中按类筛选。",
      associations: "包含的关联", noChildren: "没有下级包含角色。",
      firstOut: "仅显示前 10 个，共 {n} 个。",
      referencedBy: "被引用为组件", noParents: "没有父类引用。",
      expandInGraph: "在图中展开", focus: "聚焦", copyIri: "复制 IRI", viewClassProps: "查看该类属性",
      graphLimit: "图中类数已达 240 上限；请使用搜索或“概览”查看。",
      overview: "概览模式：按类别排列 {n} 个类；点击节点查看详情",
      allClasses: "全部类", allCore: "全部核心类型",
      dataElement: "数据元素", format: "格式", datatype: "数据类型", coreType: "核心类型",
      usedBy: "使用类", codeTable: "代码表", role: "关联角色", targetClass: "目标类",
      parents: "父类数", definition: "定义", items: "条", prev: "上一页", next: "下一页",
      page: "第 {p} / {pages} 页 · {n} 条结果",
      details: "详情", dataProperty: "数据属性", objectProperty: "对象属性",
      wcoCore: "WCO 核心类型", xmlTag: "XML 标签", jsonTag: "JSON 标签", namedList: "命名表：",
      usedByThis: "使用该数据元素的类", parentClasses: "父类", viewTarget: "查看目标类",
      codeLists: "个代码表", unknownSource: "未注明来源", sourceTable: "来源表",
      codeValues: "个代码值", dataElements: "个数据元素",
      noCodeValues: "LIB 未列出该表的具名代码值。请按来源表查阅。",
      codeValuesTitle: "代码值", relatedElements: "相关数据元素", noRelated: "未匹配到具体数据元素。",
      class: "类", classes: "类", associationsShort: "关联", flags: "标记", noFlags: "无包级使用标记",
      package: "包", inPackageClass: "包内类：", seq: "Seq.", path: "Path", remark: "备注",
      profilePage: "第 {p} / {pages} 页 · {n} 条",
      png: "PNG 已导出",
      metricClasses: "OWL 类", metricObject: "对象属性", metricData: "数据属性",
      metricAssoc: "包含关系", metricCodes: "代码表", metricTriples: "RDF 三元组"
    },
    en: {
      dataNotLoaded: "data.js failed to load.",
      copied: "Copied to clipboard",
      catMetadata: "Metadata", catRoot: "Root document", catContent: "Content", catParty: "Party",
      catLocation: "Location", catAgency: "Government agency", catTransport: "Transport means",
      searchClass: "Class", searchAttr: "Data property", searchOp: "Object property",
      noMatch: "No matches", noClassMatch: "No matching classes", selectClass: "Select a class to view details",
      depth: "Depth", paths: "paths", inferred: "Inferred placement",
      classId: "WCO class ID", oisBranch: "OIS branch", typicalPath: "Typical path", rawPath: "Raw path",
      dataProps: "Data properties", codeList: "Code list", noDirectAttrs: "This class has no direct data properties.",
      firstAttrs: "Showing the first 9 of {n}. Use the property index to filter by class.",
      associations: "Contained associations", noChildren: "No child roles.",
      firstOut: "Showing the first 10 of {n}.",
      referencedBy: "Referenced as a component", noParents: "No parent references.",
      expandInGraph: "Expand in graph", focus: "Focus", copyIri: "Copy IRI", viewClassProps: "View class properties",
      graphLimit: "The graph is limited to 240 classes; use search or Overview.",
      overview: "Overview: {n} classes by category; click a node for details",
      allClasses: "All classes", allCore: "All core types",
      dataElement: "Data element", format: "Format", datatype: "Datatype", coreType: "Core type",
      usedBy: "Used by", codeTable: "Code list", role: "Role", targetClass: "Target class",
      parents: "Parents", definition: "Definition", items: "items", prev: "Previous", next: "Next",
      page: "Page {p} of {pages} · {n} results",
      details: "Details", dataProperty: "Data property", objectProperty: "Object property",
      wcoCore: "WCO core type", xmlTag: "XML tag", jsonTag: "JSON tag", namedList: "Named list: ",
      usedByThis: "Classes using this data element", parentClasses: "Parents", viewTarget: "View target class",
      codeLists: "code lists", unknownSource: "Source not specified", sourceTable: "Source list",
      codeValues: "code values", dataElements: "data elements",
      noCodeValues: "The LIB does not list named code values for this table. Consult the source list.",
      codeValuesTitle: "Code values", relatedElements: "Related data elements", noRelated: "No matching data elements.",
      class: "Class", classes: "classes", associationsShort: "associations", flags: "flags", noFlags: "No package flags",
      package: "Package", inPackageClass: "Package class: ", seq: "Seq.", path: "Path", remark: "Remark",
      profilePage: "Page {p} of {pages} · {n} items",
      png: "PNG exported",
      metricClasses: "OWL classes", metricObject: "Object properties", metricData: "Data properties",
      metricAssoc: "Containments", metricCodes: "Code lists", metricTriples: "RDF triples"
    }
  };
  const t = (key, vars) => {
    let value = (I18N[LANG] && I18N[LANG][key]) || (I18N.zh[key] || key);
    if (vars) value = value.replace(/\{(\w+)\}/g, (_, k) => vars[k] ?? "");
    return value;
  };

  if (!D) { document.body.innerHTML = '<p style="padding:40px">' + t('dataNotLoaded') + '</p>'; return; }

  const CLASSES = D.classes;
  const BY_ID = new Map(CLASSES.map(c => [c.id, c]));
  const ATTRS = D.attributes;
  const ATTR_BY_ID = new Map(ATTRS.map(a => [a.id, a]));
  const OPS = D.objectProperties;
  const OP_BY_ROLE = new Map(OPS.map(o => [o.role, o]));
  const EDGES = D.edges;
  const EDGES_BY_SOURCE = new Map();
  const EDGES_BY_TARGET = new Map();
  for (const e of EDGES) {
    if (!EDGES_BY_SOURCE.has(e.source)) EDGES_BY_SOURCE.set(e.source, []);
    if (!EDGES_BY_TARGET.has(e.target)) EDGES_BY_TARGET.set(e.target, []);
    EDGES_BY_SOURCE.get(e.source).push(e);
    EDGES_BY_TARGET.get(e.target).push(e);
  }
  for (const arr of EDGES_BY_SOURCE.values()) arr.sort((a, b) => a.role.localeCompare(b.role));
  for (const arr of EDGES_BY_TARGET.values()) arr.sort((a, b) => a.role.localeCompare(b.role));

  const CATS = {
    metadata: { key: 'catMetadata', color: '#d97706' },
    root: { key: 'catRoot', color: '#1f2937' },
    content: { key: 'catContent', color: '#2563eb' },
    party: { key: 'catParty', color: '#7c3aed' },
    location: { key: 'catLocation', color: '#059669' },
    agency: { key: 'catAgency', color: '#dc2626' },
    transport: { key: 'catTransport', color: '#0891b2' }
  };
  const catColor = id => (CATS[BY_ID.get(id)?.category] || CATS.content).color;
  const catLabel = id => t((CATS[BY_ID.get(id)?.category] || CATS.content).key);

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  const esc = s => String(s ?? '').replace(/[&<>"']/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
  const fmt = n => Number(n || 0).toLocaleString('en-US');
  const short = (s, n = 90) => { s = String(s || ''); return s.length > n ? s.slice(0, n - 1) + '…' : s; };

  const state = {
    view: 'graph',
    selected: null,
    treeOpen: new Set(),
    hierOpen: new Set(),
    propTab: 'data',
    propQuery: '',
    propClass: '',
    propCore: '',
    propPage: 1,
    codeQuery: '',
    codeOnlyValues: false,
    codeSelected: null,
    profilePkg: '',
    profileQuery: '',
    profileClass: '',
    profilePage: 1,
    searchIndex: 0
  };

  function safeHash(hash) {
    try { history.replaceState(null, '', hash); }
    catch { /* file:// or sandboxed history: keep the current URL */ }
  }

  function toast(msg) {
    const t = $('#toast');
    t.textContent = msg;
    t.hidden = false;
    clearTimeout(t._timer);
    t._timer = setTimeout(() => { t.hidden = true; }, 2200);
  }

  async function copyText(text) {
    try {
      await navigator.clipboard.writeText(text);
      toast(t('copied'));
    } catch {
      const ta = document.createElement('textarea');
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      ta.remove();
      toast(t('copied'));
    }
  }

  // ---------------------------------------------------------------------
  // Navigation
  // ---------------------------------------------------------------------
  const views = ['graph', 'hierarchy', 'properties', 'codelists', 'profiles', 'about'];
  function parseHash() {
    const h = location.hash.replace(/^#\/?/, '');
    const [path, query] = h.split('?');
    const v = path.split('/')[0] || 'graph';
    const params = new URLSearchParams(query || '');
    return { view: views.includes(v) ? v : 'graph', classId: params.get('class') };
  }

  function setView(view, opts = {}) {
    if (!views.includes(view)) view = 'graph';
    state.view = view;
    for (const v of views) {
      const el = $('#view-' + v);
      if (el) el.classList.toggle('active', v === view);
    }
    $$('.mainnav a').forEach(a => a.classList.toggle('active', a.dataset.view === view));
    if (!opts.keepHash) {
      const suffix = view === 'graph' && state.selected ? '?class=' + encodeURIComponent(state.selected) : '';
      safeHash('#/' + view + suffix);
    }
    if (view === 'graph') {
      requestAnimationFrame(() => { resizeCanvas(); });
    }
    if (view === 'hierarchy') renderHierarchy();
    if (view === 'properties') renderProperties();
    if (view === 'codelists') renderCodeLists();
    if (view === 'profiles') renderProfiles();
    if (view === 'about') renderAbout();
    window.scrollTo({ top: 0, behavior: 'instant' });
  }

  function openClass(id, opts = {}) {
    if (!BY_ID.has(id)) return;
    state.selected = id;
    if (state.view !== 'graph' && state.view !== 'hierarchy') {
      setView('graph', { keepHash: true });
    }
    if (state.view === 'graph') {
      ensureVisible(id, true);
      centerOn(id);
      drawGraph();
      safeHash('#/graph?class=' + encodeURIComponent(id));
    } else {
      safeHash('#/hierarchy?class=' + encodeURIComponent(id));
    }
    renderDetails(id, $('#details'));
    renderDetails(id, $('#hierDetails'));
    updateTreeSelection();
    updateHierSelection();
    if (state.view === 'hierarchy') {
      const h = $('#hierDetails');
      if (h && window.innerWidth < 1080) h.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }

  // ---------------------------------------------------------------------
  // Global search
  // ---------------------------------------------------------------------
  const searchIndex = [];
  for (const c of CLASSES) {
    searchIndex.push({ kind: 'class', id: c.id, name: c.name, zh: c.zh, meta: t('searchClass') + ' · ' + c.id, hay: (c.name + ' ' + c.zh + ' ' + c.id + ' ' + c.def).toLowerCase() });
  }
  for (const a of ATTRS) {
    searchIndex.push({ kind: 'attr', id: a.id, name: a.name, zh: '', meta: t('searchAttr') + ' · ' + a.id, hay: (a.name + ' ' + a.id + ' ' + a.def + ' ' + a.xml).toLowerCase() });
  }
  for (const o of OPS) {
    searchIndex.push({ kind: 'op', id: o.role, name: o.label, zh: '', meta: t('searchOp') + ' · ' + o.role, hay: (o.role + ' ' + o.label + ' ' + o.def).toLowerCase() });
  }

  function renderSearchResults(q) {
    const box = $('#searchResults');
    q = q.trim().toLowerCase();
    if (!q) { box.classList.remove('show'); box.innerHTML = ''; return; }
    const results = searchIndex.filter(x => x.hay.includes(q)).slice(0, 12);
    state.searchIndex = 0;
    if (!results.length) {
      box.innerHTML = '<div class="sr-empty">' + t('noMatch') + '</div>';
      box.classList.add('show');
      return;
    }
    box.innerHTML = results.map((r, i) => `<div class="sr-item${i === 0 ? ' active' : ''}" data-kind="${r.kind}" data-id="${esc(r.id)}" role="option">
      <span class="sr-name">${esc(r.name)}${LANG === 'zh' && r.zh ? ' <span style="color:#8293a7;font-weight:400">' + esc(r.zh) + '</span>' : ''}</span>
      <span class="sr-meta">${esc(r.meta)}</span></div>`).join('');
    box.classList.add('show');
    box._results = results;
  }

  function chooseSearch(kind, id) {
    $('#searchResults').classList.remove('show');
    $('#globalSearch').value = '';
    if (kind === 'class') openClass(id);
    else if (kind === 'attr') openAttrDrawer(id);
    else openOpDrawer(id);
  }

  // ---------------------------------------------------------------------
  // Tree
  // ---------------------------------------------------------------------
  let PRIMARY_PARENT = new Map();
  function buildPrimaryTree() {
    const children = new Map();
    const seen = new Set(['OIS']);
    const queue = ['OIS'];
    // Breadth-first spanning tree using the first (alphabetical) edge.
    while (queue.length) {
      const cur = queue.shift();
      const outs = (EDGES_BY_SOURCE.get(cur) || []).slice().sort((a, b) => a.role.localeCompare(b.role));
      for (const e of outs) {
        if (seen.has(e.target)) continue;
        seen.add(e.target);
        PRIMARY_PARENT.set(e.target, e.source);
        if (!children.has(cur)) children.set(cur, []);
        children.get(cur).push(e);
        queue.push(e.target);
      }
    }
    // Any class not reached (should be none) is attached to CIS.
    for (const c of CLASSES) {
      if (!seen.has(c.id)) {
        PRIMARY_PARENT.set(c.id, '999');
        if (!children.has('999')) children.set('999', []);
        children.get('999').push({ source: '999', target: c.id, role: c.name });
        seen.add(c.id);
      }
    }
    for (const arr of children.values()) arr.sort((a, b) => (BY_ID.get(a.target)?.name || '').localeCompare(BY_ID.get(b.target)?.name || ''));
    return children;
  }
  const TREE_CHILDREN = buildPrimaryTree();

  function collectAncestors(id) {
    const set = new Set([id]);
    let cur = id;
    let guard = 0;
    while (PRIMARY_PARENT.has(cur) && guard++ < 20) {
      cur = PRIMARY_PARENT.get(cur);
      set.add(cur);
    }
    return set;
  }

  function renderTree(container, openSet, filter, selected) {
    const q = (filter || '').trim().toLowerCase();
    let allowed = null;
    if (q) {
      allowed = new Set();
      for (const c of CLASSES) {
        if ((c.name + ' ' + c.zh + ' ' + c.id).toLowerCase().includes(q)) {
          for (const a of collectAncestors(c.id)) allowed.add(a);
        }
      }
    }
    const makeNode = (id, depth) => {
      const c = BY_ID.get(id);
      if (!c) return null;
      const kids = TREE_CHILDREN.get(id) || [];
      const visibleKids = kids.filter(k => !allowed || allowed.has(k.target));
      if (allowed && !allowed.has(id) && !visibleKids.length) return null;
      const isOpen = q ? true : (openSet.has(id) || depth < 2);
      const hasKids = visibleKids.length > 0;
      const row = document.createElement('div');
      row.className = 'tree-row' + (isOpen && hasKids ? ' open' : '') + (id === selected ? ' selected' : '');
      row.dataset.id = id;
      row.style.paddingLeft = (depth * 12 + 4) + 'px';
      row.setAttribute('role', 'treeitem');
      row.setAttribute('aria-expanded', String(isOpen && hasKids));
      row.innerHTML = `<span class="caret" aria-hidden="true">${hasKids ? '▶' : ''}</span>
        <span class="dot" style="background:${catColor(id)}"></span>
        <span class="tname">${esc(c.name)}${LANG === 'zh' && c.zh ? ' <span style="color:#93a3b6;font-weight:400">' + esc(c.zh) + '</span>' : ''}</span>
        <span class="tid">${esc(c.id)}</span>`;
      row.title = c.def;
      const wrap = document.createElement('div');
      wrap.className = 'tree-node' + (isOpen && hasKids ? ' open' : '');
      wrap.appendChild(row);
      if (hasKids) {
        const kidsEl = document.createElement('div');
        kidsEl.className = 'tree-children';
        for (const k of visibleKids) {
          const n = makeNode(k.target, depth + 1);
          if (n) kidsEl.appendChild(n);
        }
        wrap.appendChild(kidsEl);
      }
      row.addEventListener('click', ev => {
        ev.stopPropagation();
        if (ev.target.closest('.caret') && hasKids) {
          const open = wrap.classList.toggle('open');
          row.classList.toggle('open', open);
          if (open) openSet.add(id); else openSet.delete(id);
          return;
        }
        openClass(id);
      });
      row.addEventListener('dblclick', ev => {
        ev.stopPropagation();
        if (!hasKids) return;
        const open = wrap.classList.toggle('open');
        row.classList.toggle('open', open);
        if (open) openSet.add(id); else openSet.delete(id);
      });
      return wrap;
    };
    container.innerHTML = '';
    const root = makeNode('OIS', 0);
    if (root) container.appendChild(root);
    if (!container.children.length) {
      container.innerHTML = '<div class="empty-state">' + t('noClassMatch') + '</div>';
    }
    // Open ancestors of selected class
    if (selected && !q) {
      for (const a of collectAncestors(selected)) {
        openSet.add(a);
        const wrap = container.querySelector('.tree-node[data-id="' + CSS.escape(a) + '"]');
        // data-id is on the row, not the wrapper; fix by querying row then parent
        const row = container.querySelector('.tree-row[data-id="' + CSS.escape(a) + '"]');
        if (row) {
          row.parentElement.classList.add('open');
          row.classList.add('open');
        }
      }
    }
  }

  function updateTreeSelection() {
    for (const el of [$('#tree'), $('#hierTree')]) {
      if (!el) continue;
      $$('.tree-row', el).forEach(r => r.classList.toggle('selected', r.dataset.id === state.selected));
    }
  }
  function updateHierSelection() { updateTreeSelection(); }

  function renderHierarchy() {
    renderTree($('#hierTree'), state.hierOpen, $('#hierFilter').value, state.selected);
    renderDetails(state.selected || 'OIS', $('#hierDetails'));
  }

  // ---------------------------------------------------------------------
  // Details
  // ---------------------------------------------------------------------
  function renderDetails(id, target) {
    if (!target) return;
    const c = BY_ID.get(id);
    if (!c) { target.innerHTML = '<div class="empty-state">' + t('selectClass') + '</div>'; return; }
    const attrs = ATTRS.filter(a => a.classes.includes(id)).sort((a, b) => a.name.localeCompare(b.name));
    const outs = EDGES_BY_SOURCE.get(id) || [];
    const ins = EDGES_BY_TARGET.get(id) || [];
    const crumb = c.path.split(' / ').map((p, i, arr) => i === arr.length - 1 ? `<b>${esc(p)}</b>` : esc(p)).join(' › ');
    const linkChip = (cid, role) => `<button class="assoc-item" data-class="${esc(cid)}"><span class="role">${esc(role)}</span><span class="arrow">→</span><span class="target">${esc(BY_ID.get(cid)?.name || cid)}</span></button>`;
    target.innerHTML = `<div class="detail-inner">
      <div class="crumb">${crumb}</div>
      <h2 class="detail-title">${esc(c.name)}</h2>
      ${LANG === 'zh' && c.zh ? `<div class="detail-zh">${esc(c.zh)}</div>` : ''}
      <div class="badges">
        <span class="badge id">${esc(c.id)}</span>
        <span class="badge cat ${esc(c.category)}">${esc(catLabel(id))}</span>
        <span class="badge">${t('depth')} ${c.depth}</span>
        <span class="badge">${c.occurrences} ${t('paths')}</span>
        ${c.inferred ? '<span class="badge">' + t('inferred') + '</span>' : ''}
      </div>
      <div class="definition">${esc(c.def)}</div>
      <dl class="meta-grid">
        <dt>${t('classId')}</dt><dd class="mono">${esc(c.id)}</dd>
        <dt>UN/CEFACT</dt><dd>${esc(c.super || '—')}</dd>
        <dt>${t('oisBranch')}</dt><dd>${esc(c.branch)}</dd>
        <dt>${t('typicalPath')}</dt><dd>${esc(c.path)}</dd>
        <dt>${t('rawPath')}</dt><dd class="mono" style="font-size:10.3px">${esc(c.rawPath || '—')}</dd>
        <dt>IRI</dt><dd class="mono" style="font-size:10.3px">${esc(D.meta.namespace + 'C_' + c.id)}</dd>
      </dl>
      <div class="section-title">${t('dataProps')} <span>${attrs.length}</span></div>
      ${attrs.length ? `<table class="mini-table">${attrs.slice(0, 9).map(a => `<tr>
        <td><button class="linklike nm" data-attr="${esc(a.id)}">${esc(a.name)}</button><div class="sub">${esc(a.id)} · ${esc(a.format || '')}</div></td>
        <td class="rt">${esc(a.datatype)}${a.codeList ? '<div class="sub">' + t('codeList') + '</div>' : ''}</td></tr>`).join('')}</table>` : '<div class="small" style="color:#8a99ac">' + t('noDirectAttrs') + '</div>'}
      ${attrs.length > 9 ? `<div class="small" style="margin-top:4px">${t('firstAttrs', {n: attrs.length})}</div>` : ''}
      <div class="section-title">${t('associations')} <span>${outs.length}</span></div>
      ${outs.length ? `<div class="assoc-list">${outs.slice(0, 10).map(e => linkChip(e.target, e.role)).join('')}</div>` : '<div class="small" style="color:#8a99ac">' + t('noChildren') + '</div>'}
      ${outs.length > 10 ? `<div class="small" style="margin-top:4px">${t('firstOut', {n: outs.length})}</div>` : ''}
      <div class="section-title">${t('referencedBy')} <span>${ins.length}</span></div>
      ${ins.length ? `<div class="assoc-list">${ins.slice(0, 8).map(e => linkChip(e.source, e.role)).join('')}</div>` : '<div class="small" style="color:#8a99ac">' + t('noParents') + '</div>'}
      <div class="detail-actions">
        <button data-action="expand" data-id="${esc(c.id)}">${t('expandInGraph')}</button>
        <button data-action="focus" data-id="${esc(c.id)}">${t('focus')}</button>
        <button data-action="copy" data-iri="${esc(D.meta.namespace + 'C_' + c.id)}">${t('copyIri')}</button>
        <button data-action="props" data-id="${esc(c.id)}">${t('viewClassProps')}</button>
      </div>
    </div>`;

    target.querySelectorAll('[data-class]').forEach(b => b.addEventListener('click', () => openClass(b.dataset.class)));
    target.querySelectorAll('[data-attr]').forEach(b => b.addEventListener('click', () => openAttrDrawer(b.dataset.attr)));
    target.querySelectorAll('[data-action="expand"]').forEach(b => b.addEventListener('click', () => { ensureVisible(b.dataset.id, true); drawGraph(); }));
    target.querySelectorAll('[data-action="focus"]').forEach(b => b.addEventListener('click', () => { ensureVisible(b.dataset.id, false); centerOn(b.dataset.id); drawGraph(); }));
    target.querySelectorAll('[data-action="copy"]').forEach(b => b.addEventListener('click', () => copyText(b.dataset.iri)));
    target.querySelectorAll('[data-action="props"]').forEach(b => b.addEventListener('click', () => openPropertiesForClass(b.dataset.id)));
  }

  // ---------------------------------------------------------------------
  // Graph
  // ---------------------------------------------------------------------
  const graph = {
    canvas: null, ctx: null, wrap: null, width: 0, height: 0, dpr: 1,
    nodes: new Map(), visible: new Set(), selected: null, hover: null,
    scale: 1, ox: 0, oy: 0, alpha: 1, raf: null, ticks: 0,
    dragging: null, panning: false, moved: false, last: null,
    pointer: { x: 0, y: 0 }, visibleEdges: [], overview: false
  };

  const INITIAL = ['OIS', '3MD', '999', '42A', '58C', '74B'];
  function nameId(name) { return CLASSES.find(c => c.name === name)?.id; }
  for (const n of ['Consignment', 'GoodsShipment', 'Party', 'Consignee', 'Address', 'TransportMeans', 'TransportEquipment', 'DeclarationOffice', 'AdditionalDocument', 'Invoice', 'UCR', 'Warehouse', 'Seal']) {
    const id = nameId(n);
    if (id) INITIAL.push(id);
  }

  function resizeCanvas() {
    const canvas = $('#graph');
    const wrap = $('#canvasWrap');
    if (!canvas || !wrap) return;
    graph.canvas = canvas;
    graph.wrap = wrap;
    graph.ctx = canvas.getContext('2d');
    const rect = wrap.getBoundingClientRect();
    graph.width = Math.max(200, rect.width);
    graph.height = Math.max(200, rect.height);
    graph.dpr = Math.min(2.5, window.devicePixelRatio || 1);
    canvas.width = Math.round(graph.width * graph.dpr);
    canvas.height = Math.round(graph.height * graph.dpr);
    canvas.style.width = graph.width + 'px';
    canvas.style.height = graph.height + 'px';
    graph.ctx.setTransform(graph.dpr, 0, 0, graph.dpr, 0, 0);
    if (!graph.nodes.size) resetGraph(false);
    drawGraph();
  }

  function nodeR(id) {
    const deg = (EDGES_BY_SOURCE.get(id)?.length || 0) + (EDGES_BY_TARGET.get(id)?.length || 0);
    return 5 + Math.min(7, Math.sqrt(deg) * 1.55);
  }

  function ensureVisible(id, withNeighbors = true) {
    if (!BY_ID.has(id)) return;
    graph.overview = false;
    const add = new Set([id]);
    if (withNeighbors) {
      for (const e of EDGES_BY_SOURCE.get(id) || []) add.add(e.target);
      for (const e of EDGES_BY_TARGET.get(id) || []) add.add(e.source);
    }
    if (graph.visible.size + add.size > 240) {
      if (!graph.visible.has(id)) add.clear(), add.add(id);
      toast(t('graphLimit'));
    }
    let changed = false;
    const cx = graph.width / 2, cy = graph.height / 2;
    const anchor = graph.nodes.get(id) || { x: cx, y: cy };
    for (const nid of add) {
      if (graph.visible.has(nid)) continue;
      graph.visible.add(nid);
      changed = true;
      const n = graph.nodes.get(nid);
      if (!n) {
        const a = Math.random() * Math.PI * 2;
        const r = 70 + Math.random() * 90;
        graph.nodes.set(nid, {
          id: nid,
          x: anchor.x + Math.cos(a) * r,
          y: anchor.y + Math.sin(a) * r,
          vx: 0, vy: 0
        });
      }
    }
    if (changed) { graph.alpha = Math.max(graph.alpha, 0.8); startSim(); }
  }

  function resetGraph(redraw = true) {
    graph.overview = false;
    graph.nodes.clear();
    graph.visible.clear();
    for (const id of INITIAL) if (BY_ID.has(id)) graph.visible.add(id);
    const cx = graph.width / 2, cy = graph.height / 2;
    const others = Array.from(graph.visible).filter(id => id !== 'OIS');
    graph.nodes.set('OIS', { id: 'OIS', x: cx, y: cy, vx: 0, vy: 0 });
    others.forEach((id, i) => {
      const angle = (i / Math.max(1, others.length)) * Math.PI * 2 - Math.PI / 2;
      const r = 165 + (i % 3) * 34;
      graph.nodes.set(id, { id, x: cx + Math.cos(angle) * r, y: cy + Math.sin(angle) * r, vx: 0, vy: 0 });
    });
    graph.scale = 1; graph.ox = 0; graph.oy = 0; graph.alpha = 1; graph.ticks = 0;
    state.selected = state.selected && graph.visible.has(state.selected) ? state.selected : 'OIS';
    renderDetails(state.selected, $('#details'));
    startSim();
    if (redraw) drawGraph();
  }

  function startSim() {
    if (graph.raf) return;
    const loop = () => {
      graph.raf = null;
      const active = simStep();
      drawGraph();
      if (active) graph.raf = requestAnimationFrame(loop);
    };
    graph.raf = requestAnimationFrame(loop);
  }

  function simStep() {
    const ids = Array.from(graph.visible);
    if (ids.length > 1 && graph.alpha > 0.015) {
      const cx = graph.width / 2, cy = graph.height / 2;
      // repulsion
      for (let i = 0; i < ids.length; i++) {
        const a = graph.nodes.get(ids[i]);
        for (let j = i + 1; j < ids.length; j++) {
          const b = graph.nodes.get(ids[j]);
          let dx = b.x - a.x, dy = b.y - a.y;
          let d2 = dx * dx + dy * dy;
          if (d2 < 1) { dx = Math.random() - .5; dy = Math.random() - .5; d2 = 1; }
          if (d2 > 120000) continue;
          const d = Math.sqrt(d2);
          const f = 2600 / d2;
          const fx = dx / d * f, fy = dy / d * f;
          a.vx -= fx; a.vy -= fy;
          b.vx += fx; b.vy += fy;
          const minD = nodeR(ids[i]) + nodeR(ids[j]) + 22;
          if (d < minD) {
            const push = (minD - d) / d * 0.42;
            a.x -= dx * push; a.y -= dy * push;
            b.x += dx * push; b.y += dy * push;
          }
        }
      }
      // springs
      for (const e of EDGES) {
        if (!graph.visible.has(e.source) || !graph.visible.has(e.target)) continue;
        const a = graph.nodes.get(e.source), b = graph.nodes.get(e.target);
        const dx = b.x - a.x, dy = b.y - a.y;
        const d = Math.sqrt(dx * dx + dy * dy) || 1;
        const ideal = 108;
        const f = (d - ideal) * 0.014;
        const fx = dx / d * f, fy = dy / d * f;
        a.vx += fx; a.vy += fy;
        b.vx -= fx; b.vy -= fy;
      }
      // gravity + integrate
      for (const id of ids) {
        const n = graph.nodes.get(id);
        n.vx += (cx - n.x) * 0.0018;
        n.vy += (cy - n.y) * 0.0018;
        n.vx *= 0.86; n.vy *= 0.86;
        n.x += n.vx; n.y += n.vy;
        n.x = Math.max(20, Math.min(graph.width - 20, n.x));
        n.y = Math.max(20, Math.min(graph.height - 20, n.y));
      }
      graph.alpha *= 0.991;
    }
    return graph.alpha > 0.015;
  }

  function drawGraph() {
    const ctx = graph.ctx;
    if (!ctx) return;
    ctx.setTransform(graph.dpr, 0, 0, graph.dpr, 0, 0);
    ctx.clearRect(0, 0, graph.width, graph.height);
    // grid
    ctx.save();
    ctx.strokeStyle = 'rgba(148,163,184,.10)';
    ctx.lineWidth = 1;
    const step = 32;
    for (let x = 0; x < graph.width; x += step) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, graph.height); ctx.stroke(); }
    for (let y = 0; y < graph.height; y += step) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(graph.width, y); ctx.stroke(); }
    ctx.restore();

    ctx.save();
    ctx.translate(graph.ox, graph.oy);
    ctx.scale(graph.scale, graph.scale);

    const sel = state.selected;
    const hover = graph.hover;
    const focus = sel || hover;
    const neighbors = new Set();
    if (focus) {
      neighbors.add(focus);
      for (const e of EDGES_BY_SOURCE.get(focus) || []) neighbors.add(e.target);
      for (const e of EDGES_BY_TARGET.get(focus) || []) neighbors.add(e.source);
    }

    // edges (hidden in the all-class overview to avoid a hairball)
    if (!graph.overview) for (const e of EDGES) {
      if (!graph.visible.has(e.source) || !graph.visible.has(e.target)) continue;
      const a = graph.nodes.get(e.source), b = graph.nodes.get(e.target);
      if (!a || !b) continue;
      const active = focus && (e.source === focus || e.target === focus);
      ctx.beginPath();
      ctx.strokeStyle = active ? 'rgba(14,116,144,.55)' : 'rgba(100,116,139,.13)';
      ctx.lineWidth = active ? 1.5 / graph.scale : 1 / graph.scale;
      ctx.moveTo(a.x, a.y);
      ctx.lineTo(b.x, b.y);
      ctx.stroke();
      if (active) {
        const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
        ctx.save();
        ctx.font = `${10 / graph.scale}px Inter, system-ui, sans-serif`;
        ctx.textAlign = 'center';
        ctx.fillStyle = 'rgba(15,58,74,.82)';
        const text = e.role;
        const w = ctx.measureText(text).width + 8 / graph.scale;
        const h = 14 / graph.scale;
        ctx.fillStyle = 'rgba(255,255,255,.88)';
        ctx.fillRect(mx - w / 2, my - h / 2, w, h);
        ctx.fillStyle = 'rgba(15,58,74,.82)';
        ctx.fillText(text, mx, my + 3.4 / graph.scale);
        ctx.restore();
      }
    }

    // nodes
    const ids = Array.from(graph.visible);
    ids.sort((a, b) => {
      const rank = id => id === sel ? 3 : id === hover ? 2 : (neighbors.has(id) ? 1 : 0);
      return rank(a) - rank(b);
    });
    for (const id of ids) {
      const n = graph.nodes.get(id);
      if (!n) continue;
      const c = BY_ID.get(id);
      const r = nodeR(id);
      const isSel = id === sel;
      const isHover = id === hover;
      const dim = focus && !neighbors.has(id) && !isSel;
      ctx.beginPath();
      ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
      ctx.fillStyle = catColor(id);
      ctx.globalAlpha = dim ? .28 : 1;
      ctx.fill();
      ctx.globalAlpha = 1;
      ctx.lineWidth = (isSel ? 2.6 : isHover ? 2 : 1.3) / graph.scale;
      ctx.strokeStyle = isSel ? '#0f172a' : '#ffffff';
      ctx.stroke();
      if (isSel) {
        ctx.beginPath();
        ctx.arc(n.x, n.y, r + 4 / graph.scale, 0, Math.PI * 2);
        ctx.strokeStyle = 'rgba(14,116,144,.45)';
        ctx.lineWidth = 2 / graph.scale;
        ctx.stroke();
      }
      const showLabel = isSel || isHover || (focus && neighbors.has(id)) || graph.scale > 1.45 || graph.visible.size <= 18;
      if (showLabel && c) {
        ctx.save();
        ctx.font = `${isSel ? 11.5 : 10.5 / Math.max(1, graph.scale * .72)}px Inter, "Noto Sans SC", system-ui, sans-serif`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        const label = c.name.length > 26 ? c.name.slice(0, 24) + '…' : c.name;
        const tw = ctx.measureText(label).width;
        const ty = n.y + r + 3 / graph.scale;
        ctx.fillStyle = 'rgba(255,255,255,.82)';
        ctx.fillRect(n.x - tw / 2 - 2, ty - 1, tw + 4, 13);
        ctx.fillStyle = isSel ? '#0f172a' : '#334155';
        ctx.fillText(label, n.x, ty);
        ctx.restore();
      }
    }
    ctx.restore();
  }

  function screenToWorld(x, y) {
    return { x: (x - graph.ox) / graph.scale, y: (y - graph.oy) / graph.scale };
  }
  function hitTest(x, y) {
    const p = screenToWorld(x, y);
    let best = null, bestD = Infinity;
    for (const id of graph.visible) {
      const n = graph.nodes.get(id);
      if (!n) continue;
      const dx = n.x - p.x, dy = n.y - p.y;
      const d = Math.sqrt(dx * dx + dy * dy);
      const rr = nodeR(id) + 5 / graph.scale;
      if (d < rr && d < bestD) { bestD = d; best = id; }
    }
    return best;
  }

  function centerOn(id) {
    const n = graph.nodes.get(id);
    if (!n) return;
    graph.ox = graph.width / 2 - n.x * graph.scale;
    graph.oy = graph.height / 2 - n.y * graph.scale;
  }

  function fitGraph() {
    const pts = Array.from(graph.visible).map(id => graph.nodes.get(id)).filter(Boolean);
    if (!pts.length) return;
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    for (const p of pts) { minX = Math.min(minX, p.x); minY = Math.min(minY, p.y); maxX = Math.max(maxX, p.x); maxY = Math.max(maxY, p.y); }
    const w = Math.max(1, maxX - minX), h = Math.max(1, maxY - minY);
    graph.scale = Math.max(.22, Math.min(2.2, Math.min((graph.width - 120) / w, (graph.height - 120) / h)));
    graph.ox = graph.width / 2 - (minX + maxX) / 2 * graph.scale;
    graph.oy = graph.height / 2 - (minY + maxY) / 2 * graph.scale;
    drawGraph();
  }

  function zoomBy(factor, cx = graph.width / 2, cy = graph.height / 2) {
    const before = screenToWorld(cx, cy);
    graph.scale = Math.max(.15, Math.min(4, graph.scale * factor));
    graph.ox = cx - before.x * graph.scale;
    graph.oy = cy - before.y * graph.scale;
    drawGraph();
  }

  function showAll() {
    graph.overview = true;
    graph.visible.clear();
    graph.nodes.clear();
    const order = ['metadata', 'root', 'content', 'party', 'location', 'agency', 'transport'];
    const sorted = CLASSES.slice().sort((a, b) => (order.indexOf(a.category) - order.indexOf(b.category)) || a.name.localeCompare(b.name));
    const cols = Math.max(10, Math.ceil(Math.sqrt(sorted.length * 1.55)));
    const cellW = (graph.width - 80) / cols;
    const rows = Math.ceil(sorted.length / cols);
    const cellH = (graph.height - 90) / Math.max(1, rows);
    sorted.forEach((c, i) => {
      const col = i % cols, row = Math.floor(i / cols);
      graph.visible.add(c.id);
      graph.nodes.set(c.id, { id: c.id, x: 40 + cellW * (col + .5), y: 40 + cellH * (row + .5), vx: 0, vy: 0 });
    });
    graph.alpha = 0; graph.scale = 1; graph.ox = 0; graph.oy = 0;
    state.selected = state.selected && graph.visible.has(state.selected) ? state.selected : 'OIS';
    drawGraph(); fitGraph();
    toast(t('overview', {n: CLASSES.length}));
  }

  function bindGraph() {
    const canvas = $('#graph');
    if (!canvas) return;
    graph.canvas = canvas;
    graph.ctx = canvas.getContext('2d');
    graph.wrap = $('#canvasWrap');
    canvas.addEventListener('mousedown', e => {
      const rect = canvas.getBoundingClientRect();
      const x = e.clientX - rect.left, y = e.clientY - rect.top;
      const hit = hitTest(x, y);
      graph.moved = false;
      graph.last = { x, y };
      if (hit) {
        graph.dragging = hit;
        graph.selected = hit;
      } else {
        graph.panning = true;
      }
      canvas.classList.add('dragging');
    });
    canvas.addEventListener('mousemove', e => {
      const rect = canvas.getBoundingClientRect();
      const x = e.clientX - rect.left, y = e.clientY - rect.top;
      if (graph.dragging) {
        const p = screenToWorld(x, y);
        const n = graph.nodes.get(graph.dragging);
        if (n) { n.x = p.x; n.y = p.y; n.vx = 0; n.vy = 0; }
        graph.moved = true;
        drawGraph();
      } else if (graph.panning) {
        graph.ox += x - graph.last.x;
        graph.oy += y - graph.last.y;
        graph.last = { x, y };
        if (Math.abs(x - graph.last.x) + Math.abs(y - graph.last.y) > 0) graph.moved = true;
        drawGraph();
      } else {
        const hit = hitTest(x, y);
        if (hit !== graph.hover) { graph.hover = hit; drawGraph(); }
        const tip = $('#graphTooltip');
        if (hit) {
          const c = BY_ID.get(hit);
          tip.hidden = false;
          tip.innerHTML = `<b>${esc(c.name)}</b> <span style="opacity:.65">${esc(c.id)}</span><br><span style="opacity:.78">${esc(short(c.def, 110))}</span>`;
          tip.style.left = Math.min(graph.width - 220, x + 13) + 'px';
          tip.style.top = Math.min(graph.height - 60, y + 13) + 'px';
        } else tip.hidden = true;
      }
    });
    const end = () => {
      if (graph.dragging && !graph.moved) {
        graph.selected = graph.dragging;
        openClass(graph.dragging);
      }
      graph.dragging = null;
      graph.panning = false;
      canvas.classList.remove('dragging');
    };
    canvas.addEventListener('mouseup', end);
    canvas.addEventListener('mouseleave', () => { graph.hover = null; $('#graphTooltip').hidden = true; drawGraph(); end(); });
    canvas.addEventListener('dblclick', e => {
      const rect = canvas.getBoundingClientRect();
      const hit = hitTest(e.clientX - rect.left, e.clientY - rect.top);
      if (hit) { graph.selected = hit; ensureVisible(hit, true); openClass(hit); }
    });
    canvas.addEventListener('wheel', e => {
      e.preventDefault();
      const rect = canvas.getBoundingClientRect();
      zoomBy(e.deltaY < 0 ? 1.12 : 0.89, e.clientX - rect.left, e.clientY - rect.top);
    }, { passive: false });

    new ResizeObserver(() => resizeCanvas()).observe($('#canvasWrap'));
  }

  // ---------------------------------------------------------------------
  // Properties
  // ---------------------------------------------------------------------
  function fillClassFilter() {
    const sel = $('#propClassFilter');
    if (!sel || sel.options.length > 1) return;
    const sorted = CLASSES.slice().sort((a, b) => a.name.localeCompare(b.name));
    sel.innerHTML = '<option value="">' + t('allClasses') + '</option>' + sorted.map(c => `<option value="${esc(c.id)}">${esc(c.name)} (${esc(c.id)})</option>`).join('');
    const core = $('#propCoreFilter');
    const cores = Array.from(new Set(ATTRS.map(a => a.core).filter(Boolean))).sort();
    core.innerHTML = '<option value="">' + t('allCore') + '</option>' + cores.map(x => `<option value="${esc(x)}">${esc(x)}</option>`).join('');
  }

  function filteredDataProps() {
    const q = state.propQuery.toLowerCase();
    return ATTRS.filter(a => {
      if (state.propClass && !a.classes.includes(state.propClass)) return false;
      if (state.propCore && a.core !== state.propCore) return false;
      if (!q) return true;
      return (a.name + ' ' + a.id + ' ' + a.def + ' ' + a.xml + ' ' + a.codeList).toLowerCase().includes(q);
    });
  }
  function filteredOps() {
    const q = state.propQuery.toLowerCase();
    return OPS.filter(o => {
      if (state.propClass && !o.parents.includes(state.propClass)) return false;
      if (!q) return true;
      return (o.role + ' ' + o.label + ' ' + o.def + ' ' + o.rangeName).toLowerCase().includes(q);
    });
  }

  function renderProperties() {
    fillClassFilter();
    const isData = state.propTab === 'data';
    const rows = isData ? filteredDataProps() : filteredOps();
    const per = 40;
    const pages = Math.max(1, Math.ceil(rows.length / per));
    if (state.propPage > pages) state.propPage = pages;
    const start = (state.propPage - 1) * per;
    const pageRows = rows.slice(start, start + per);
    const thead = $('#propTable thead');
    const tbody = $('#propTable tbody');
    if (isData) {
      thead.innerHTML = '<tr><th>' + t('dataElement') + '</th><th>' + t('format') + '</th><th>' + t('datatype') + '</th><th>' + t('coreType') + '</th><th>' + t('usedBy') + '</th><th>' + t('codeTable') + '</th></tr>';
      tbody.innerHTML = pageRows.map(a => `<tr data-attr="${esc(a.id)}">
        <td><div class="cell-name">${esc(a.name)}</div><div class="cell-sub mono">${esc(a.id)} · XML ${esc(a.xml || '—')}</div></td>
        <td><span class="tag">${esc(a.format || '—')}</span></td>
        <td><span class="tag blue">${esc(a.datatype)}</span></td>
        <td>${esc(a.core || '—')}</td>
        <td>${a.count}</td>
        <td>${a.codeList ? `<span class="tag amber">${esc(short(a.codeList, 38))}</span>` : '<span class="muted">—</span>'}</td>
      </tr>`).join('');
      tbody.querySelectorAll('tr').forEach(tr => tr.addEventListener('click', () => openAttrDrawer(tr.dataset.attr)));
    } else {
      thead.innerHTML = '<tr><th>' + t('role') + '</th><th>' + t('targetClass') + '</th><th>' + t('parents') + '</th><th>XML / JSON</th><th>' + t('definition') + '</th></tr>';
      tbody.innerHTML = pageRows.map(o => `<tr data-op="${esc(o.role)}">
        <td><div class="cell-name">${esc(o.role)}</div><div class="cell-sub">${esc(o.label)}</div></td>
        <td>${esc(o.rangeName)} <span class="tag">${esc(o.range)}</span></td>
        <td>${o.count}</td>
        <td class="mono" style="font-size:10.3px">${esc(o.xml || '—')}<br>${esc(o.json || '—')}</td>
        <td>${esc(short(o.def, 70))}</td>
      </tr>`).join('');
      tbody.querySelectorAll('tr').forEach(tr => tr.addEventListener('click', () => openOpDrawer(tr.dataset.op)));
    }
    $('#propTotal').textContent = (isData ? ATTRS.length : OPS.length) + ' ' + t('items');
    $('#dataCount').textContent = ATTRS.length;
    $('#opCount').textContent = OPS.length;
    const pager = $('#propPager');
    pager.innerHTML = `<button ${state.propPage <= 1 ? 'disabled' : ''} data-page="prev">${t('prev')}</button>
      <span>${t('page', {p: state.propPage, pages, n: fmt(rows.length)})}</span>
      <button ${state.propPage >= pages ? 'disabled' : ''} data-page="next">${t('next')}</button>`;
    pager.querySelectorAll('button').forEach(b => b.addEventListener('click', () => {
      if (b.dataset.page === 'prev') state.propPage--;
      if (b.dataset.page === 'next') state.propPage++;
      renderProperties();
    }));
  }

  function openPropertiesForClass(id) {
    state.propTab = 'data';
    state.propClass = id;
    state.propQuery = '';
    state.propPage = 1;
    setView('properties');
    $('#propClassFilter').value = id;
    $('#propSearch').value = '';
    $$('[data-prop-tab]').forEach(b => b.classList.toggle('active', b.dataset.propTab === 'data'));
    renderProperties();
  }

  // ---------------------------------------------------------------------
  // Drawers
  // ---------------------------------------------------------------------
  function closeDrawer() {
    const d = $('#drawer');
    d.hidden = true;
    d.innerHTML = '';
  }
  function openDrawer(html) {
    const d = $('#drawer');
    d.innerHTML = `<div class="drawer-card"><div class="drawer-head"><h2>${t('details')}</h2><button class="icon-btn" id="drawerClose">×</button></div><div class="drawer-body">${html}</div></div>`;
    d.hidden = false;
    $('#drawerClose').addEventListener('click', closeDrawer);
    d.addEventListener('click', ev => { if (ev.target === d) closeDrawer(); });
  }
  function openAttrDrawer(id) {
    const a = ATTR_BY_ID.get(id);
    if (!a) return;
    const classes = a.classes.map(cid => `<button class="tag" data-class="${esc(cid)}">${esc(BY_ID.get(cid)?.name || cid)}</button>`).join(' ');
    openDrawer(`<h2 class="detail-title">${esc(a.name)}</h2>
      <div class="badges"><span class="badge id">${esc(a.id)}</span><span class="badge">${t('dataProperty')}</span><span class="badge">${esc(a.format)}</span></div>
      <div class="definition">${esc(a.def)}</div>
      <dl class="meta-grid">
        <dt>${t('datatype')}</dt><dd class="mono">${esc(a.datatype)}</dd>
        <dt>${t('wcoCore')}</dt><dd>${esc(a.core)}</dd>
        <dt>${t('xmlTag')}</dt><dd class="mono">${esc(a.xml || '—')}</dd>
        <dt>${t('jsonTag')}</dt><dd class="mono">${esc(a.json || '—')}</dd>
        <dt>${t('codeList')}</dt><dd>${esc(a.codeList || '—')}${a.codeListName ? '<br><span class="small">' + t('namedList') + esc(a.codeListName) + '</span>' : ''}</dd>
        <dt>IRI</dt><dd class="mono" style="font-size:10.3px">${esc(D.meta.namespace + 'dp_' + a.id)}</dd>
      </dl>
      <div class="section-title">${t('usedByThis')} <span>${a.classes.length}</span></div>
      <div class="related-list">${classes}</div>
      <div class="detail-actions"><button data-copy="${esc(D.meta.namespace + 'dp_' + a.id)}">${t('copyIri')}</button></div>`);
    $$('[data-class]', $('#drawer')).forEach(b => b.addEventListener('click', () => { closeDrawer(); openClass(b.dataset.class); }));
    $$('[data-copy]', $('#drawer')).forEach(b => b.addEventListener('click', () => copyText(b.dataset.copy)));
  }
  function openOpDrawer(role) {
    const o = OP_BY_ROLE.get(role);
    if (!o) return;
    const parents = o.parents.map(cid => `<button class="tag" data-class="${esc(cid)}">${esc(BY_ID.get(cid)?.name || cid)}</button>`).join(' ');
    openDrawer(`<h2 class="detail-title">${esc(o.role)}</h2>
      <div class="badges"><span class="badge">${t('objectProperty')}</span><span class="badge">${esc(o.count)} ${t('parents')}</span></div>
      <div class="definition">${esc(o.def)}</div>
      <dl class="meta-grid">
        <dt>${t('targetClass')}</dt><dd>${esc(o.rangeName)} <span class="mono">(${esc(o.range)})</span></dd>
        <dt>${t('xmlTag')}</dt><dd class="mono">${esc(o.xml || '—')}</dd>
        <dt>${t('jsonTag')}</dt><dd class="mono">${esc(o.json || '—')}</dd>
        <dt>IRI</dt><dd class="mono" style="font-size:10.3px">${esc(D.meta.namespace + 'has' + o.role[0].toUpperCase() + o.role.slice(1))}</dd>
      </dl>
      <div class="section-title">${t('parentClasses')} <span>${o.parents.length}</span></div>
      <div class="related-list">${parents}</div>
      <div class="detail-actions"><button data-class2="${esc(o.range)}">${t('viewTarget')}</button></div>`);
    $$('[data-class]', $('#drawer')).forEach(b => b.addEventListener('click', () => { closeDrawer(); openClass(b.dataset.class); }));
    const t = $('[data-class2]', $('#drawer'));
    if (t) t.addEventListener('click', () => { closeDrawer(); openClass(t.dataset.class2); });
  }

  // ---------------------------------------------------------------------
  // Code lists
  // ---------------------------------------------------------------------
  function renderCodeLists() {
    const q = state.codeQuery.toLowerCase();
    const list = D.codeLists.filter(cl => {
      if (state.codeOnlyValues && !cl.codes.length) return false;
      if (!q) return true;
      return (cl.name + ' ' + cl.source).toLowerCase().includes(q);
    });
    $('#codeCountLabel').textContent = `${list.length} / ${D.codeLists.length} ${t('codeLists')}`;
    const grid = $('#codeGrid');
    grid.innerHTML = list.map(cl => `<div class="code-card${cl.name === state.codeSelected ? ' selected' : ''}" data-code="${esc(cl.name)}">
      <h3>${esc(cl.name)}</h3>
      <p>${esc(short(cl.source || t('unknownSource'), 92))}</p>
      <div class="cc-meta"><span>${cl.codes.length ? cl.codes.length + ' ' + t('codeValues') : t('sourceTable')}</span><span>${cl.usedBy.length} ${t('dataElements')}</span></div>
    </div>`).join('') || '<div class="empty-state">' + t('noMatch') + '</div>';
    grid.querySelectorAll('.code-card').forEach(card => card.addEventListener('click', () => {
      state.codeSelected = card.dataset.code;
      renderCodeLists();
      renderCodeDetail(card.dataset.code);
    }));
    if (!state.codeSelected && list.length) {
      state.codeSelected = list[0].name;
      renderCodeDetail(list[0].name);
    } else if (state.codeSelected) {
      renderCodeDetail(state.codeSelected);
    }
  }

  function renderCodeDetail(name) {
    const cl = D.codeLists.find(c => c.name === name);
    const target = $('#codeDetail');
    if (!cl || !target) return;
    const values = cl.codes.length ? `<table>${cl.codes.map(c => `<tr><td>${esc(c.code)}</td><td>${esc(c.description || '')}</td></tr>`).join('')}</table>` : '<div class="small">' + t('noCodeValues') + '</div>';
    const related = cl.usedBy.map((id, i) => `<button data-attr="${esc(id)}">${esc(cl.usedByNames[i] || id)}</button>`).join('');
    target.innerHTML = `<h2>${esc(cl.name)}</h2>
      <div class="src">${esc(cl.source || t('unknownSource'))}</div>
      <div class="badges"><span class="badge">${cl.codes.length} ${t('codeValues')}</span><span class="badge">${cl.usedBy.length} ${t('dataElements')}</span></div>
      ${cl.note ? `<div class="definition" style="font-size:11.5px">${esc(cl.note)}</div>` : ''}
      <div class="section-title">${t('codeValuesTitle')} <span>${cl.codes.length}</span></div>
      <div class="code-values">${values}</div>
      <div class="section-title">${t('relatedElements')} <span>${cl.usedBy.length}</span></div>
      <div class="related-list">${related || '<span class="small">' + t('noRelated') + '</span>'}</div>`;
    target.querySelectorAll('[data-attr]').forEach(b => b.addEventListener('click', () => openAttrDrawer(b.dataset.attr)));
  }


  // ---------------------------------------------------------------------
  // Package profiles
  // ---------------------------------------------------------------------
  function profilePackage() {
    if (!D.profiles || !D.profiles.packages || !D.profiles.packages.length) return null;
    return D.profiles.packages.find(p => p.name === state.profilePkg) || D.profiles.packages[0];
  }

  function renderProfiles() {
    const box = $('#profileCards');
    if (!box || !D.profiles || !D.profiles.packages) return;
    const pkgs = D.profiles.packages;
    if (!state.profilePkg) state.profilePkg = pkgs[0].name;
    const pkg = profilePackage();
    box.innerHTML = pkgs.map(p => {
      const flags = new Set(p.items.flatMap(it => it.flags || []));
      return `<div class="profile-card${p.name === pkg.name ? ' active' : ''}" data-pkg="${esc(p.name)}">
        <h3>${esc(p.name)} <span>${p.classes} ${t('classes')}</span></h3>
        <div class="pc-stats"><div><b>${p.elements}</b><i>${t('dataElements')}</i></div><div><b>${p.associations}</b><i>${t('associationsShort')}</i></div><div><b>${flags.size}</b><i>${t('flags')}</i></div></div>
        <div class="pc-flags">${esc(Array.from(flags).slice(0, 6).join(' · ') || t('noFlags'))}</div>
      </div>`;
    }).join('');
    box.querySelectorAll('.profile-card').forEach(card => card.addEventListener('click', () => {
      state.profilePkg = card.dataset.pkg;
      state.profileClass = '';
      state.profilePage = 1;
      renderProfiles();
    }));

    const sel = $('#profileClassFilter');
    const classes = Array.from(new Map(pkg.items.map(it => [it.class, it.className])).entries())
      .sort((a, b) => a[1].localeCompare(b[1]));
    sel.innerHTML = '<option value="">' + t('allClasses') + '</option>' + classes.map(([id, name]) => `<option value="${esc(id)}">${esc(name)} (${esc(id)})</option>`).join('');
    sel.value = state.profileClass;

    const q = state.profileQuery.toLowerCase();
    const items = pkg.items.filter(it => {
      if (state.profileClass && it.class !== state.profileClass) return false;
      if (!q) return true;
      return (it.class + ' ' + it.className + ' ' + it.property + ' ' + it.propertyName + ' ' + (it.flags || []).join(' ') + ' ' + (it.remark || '')).toLowerCase().includes(q);
    });
    const per = 40;
    const pages = Math.max(1, Math.ceil(items.length / per));
    if (state.profilePage > pages) state.profilePage = pages;
    const start = (state.profilePage - 1) * per;
    const rows = items.slice(start, start + per);

    $('#profileTable thead').innerHTML = '<tr><th>' + t('class') + '</th><th>' + t('dataElement') + '</th><th>Min</th><th>Max</th><th>' + t('flags') + '</th><th>' + t('remark') + '</th></tr>';
    $('#profileTable tbody').innerHTML = rows.map((it, i) => `<tr data-i="${i}">
      <td><div class="cell-name">${esc(it.className)}</div><div class="cell-sub mono">${esc(it.class)}${it.seq ? ' · seq ' + esc(it.seq) : ''}</div></td>
      <td><div class="cell-name">${esc(it.propertyName)}</div><div class="cell-sub mono">${esc(it.property)}</div></td>
      <td><span class="tag">${esc(it.min || '—')}</span></td>
      <td><span class="tag ${it.max === '1' ? 'amber' : ''}">${esc(it.max || '—')}</span></td>
      <td>${(it.flags && it.flags.length) ? it.flags.slice(0, 3).map(f => `<span class="tag blue">${esc(f)}</span>`).join(' ') : '<span class="muted">—</span>'}</td>
      <td>${esc(short(it.remark || '—', 60))}</td>
    </tr>`).join('') || '<tr><td colspan="6"><div class="empty-state">' + t('noMatch') + '</div></td></tr>';
    $('#profileTable tbody').querySelectorAll('tr[data-i]').forEach(tr => tr.addEventListener('click', () => {
      openProfileDrawer(items[start + Number(tr.dataset.i)]);
    }));

    $('#profileCountLabel').textContent = `${items.length} ${t('items')} · ${pkg.name}`;
    $('#profilePager').innerHTML = `<button ${state.profilePage <= 1 ? 'disabled' : ''} data-page="prev">${t('prev')}</button>
      <span>${t('profilePage', {p: state.profilePage, pages, n: fmt(items.length)})}</span>
      <button ${state.profilePage >= pages ? 'disabled' : ''} data-page="next">${t('next')}</button>`;
    $('#profilePager').querySelectorAll('button').forEach(b => b.addEventListener('click', () => {
      if (b.dataset.page === 'prev') state.profilePage--;
      if (b.dataset.page === 'next') state.profilePage++;
      renderProfiles();
    }));
  }

  function openProfileDrawer(it) {
    const pkg = profilePackage();
    openDrawer(`<h2 class="detail-title">${esc(it.propertyName)}</h2>
      <div class="badges"><span class="badge id">${esc(it.property)}</span><span class="badge">${esc(pkg.name)}</span><span class="badge">Max ${esc(it.max || '—')}</span></div>
      <div class="definition">${t('inPackageClass')}${esc(it.className)} (${esc(it.class)})</div>
      <dl class="meta-grid">
        <dt>${t('package')}</dt><dd>${esc(pkg.name)}</dd>
        <dt>${t('classes')}</dt><dd>${esc(it.className)} <span class="mono">(${esc(it.class)})</span></dd>
        <dt>${t('dataElement')}</dt><dd>${esc(it.propertyName)} <span class="mono">(${esc(it.property)})</span></dd>
        <dt>Min / Max</dt><dd>${esc(it.min || '—')} / ${esc(it.max || '—')}</dd>
        <dt>${t('seq')}</dt><dd>${esc(it.seq || '—')}</dd>
        <dt>${t('path')}</dt><dd class="mono" style="font-size:10.3px">${esc(it.path || '—')}</dd>
      </dl>
      <div class="section-title">${t('flags')} <span>${(it.flags || []).length}</span></div>
      <div class="related-list">${(it.flags || []).map(f => `<span class="tag blue">${esc(f)}</span>`).join('') || '<span class="muted">—</span>'}</div>
      <div class="section-title">${t('remark')}</div>
      <p class="small">${esc(it.remark || '—')}</p>`);
  }

  // ---------------------------------------------------------------------
  // About
  // ---------------------------------------------------------------------
  function renderAbout() {
    const s = D.meta.stats;
    $('#buildTime').textContent = D.meta.generated.replace('T', ' ').replace('+00:00', ' UTC');
    const metrics = [
      [s.classes, t('metricClasses')], [s.objectProperties, t('metricObject')], [s.dataProperties, t('metricData')],
      [s.associations, t('metricAssoc')], [s.codeLists, t('metricCodes')], [fmt(D.meta.triples), t('metricTriples')]
    ];
    $('#aboutMetrics').innerHTML = metrics.map(([n, l]) => `<div class="metric"><b>${n}</b><span>${l}</span></div>`).join('');
  }

  // ---------------------------------------------------------------------
  // Wiring
  // ---------------------------------------------------------------------
  function bind() {
    const langSwitch = $('#langSwitch');
    if (langSwitch) langSwitch.addEventListener('click', e => {
      e.preventDefault();
      location.href = langSwitch.dataset.target + location.hash;
    });

    $('#statClasses').textContent = D.meta.stats.classes;
    $('#statOps').textContent = D.meta.stats.objectProperties;
    $('#statDps').textContent = D.meta.stats.dataProperties;
    $('#statCodes').textContent = D.meta.stats.codeLists;
    $('#treeCount').textContent = D.meta.stats.classes;
    $('#propTotal').textContent = D.meta.stats.dataProperties + ' ' + t('items');
    $('#dataCount').textContent = D.meta.stats.dataProperties;
    $('#opCount').textContent = D.meta.stats.objectProperties;

    $$('.mainnav a').forEach(a => a.addEventListener('click', e => {
      e.preventDefault();
      setView(a.dataset.view);
    }));

    const gs = $('#globalSearch');
    gs.addEventListener('input', () => renderSearchResults(gs.value));
    gs.addEventListener('focus', () => { if (gs.value.trim()) renderSearchResults(gs.value); });
    gs.addEventListener('keydown', e => {
      const box = $('#searchResults');
      const items = $$('.sr-item', box);
      if (e.key === 'Escape') { box.classList.remove('show'); gs.blur(); }
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        e.preventDefault();
        if (!items.length) return;
        state.searchIndex = (state.searchIndex + (e.key === 'ArrowDown' ? 1 : items.length - 1)) % items.length;
        items.forEach((it, i) => it.classList.toggle('active', i === state.searchIndex));
      }
      if (e.key === 'Enter') {
        e.preventDefault();
        const cur = items[state.searchIndex] || items[0];
        if (cur) chooseSearch(cur.dataset.kind, cur.dataset.id);
      }
    });
    $('#searchResults').addEventListener('click', e => {
      const it = e.target.closest('.sr-item');
      if (it) chooseSearch(it.dataset.kind, it.dataset.id);
    });
    document.addEventListener('click', e => {
      if (!e.target.closest('.topsearch')) $('#searchResults').classList.remove('show');
    });
    document.addEventListener('keydown', e => {
      if (e.key === '/' && !/input|textarea|select/i.test(document.activeElement.tagName)) {
        e.preventDefault();
        gs.focus();
      }
      if (e.key === 'Escape') { closeDrawer(); $('#searchResults').classList.remove('show'); }
    });

    $('#treeFilter').addEventListener('input', () => renderTree($('#tree'), state.treeOpen, $('#treeFilter').value, state.selected));
    $('#hierFilter').addEventListener('input', () => renderTree($('#hierTree'), state.hierOpen, $('#hierFilter').value, state.selected));
    $('#treeExpandAll').addEventListener('click', () => { for (const c of CLASSES) state.treeOpen.add(c.id); renderTree($('#tree'), state.treeOpen, $('#treeFilter').value, state.selected); });
    $('#treeCollapse').addEventListener('click', () => { state.treeOpen.clear(); renderTree($('#tree'), state.treeOpen, $('#treeFilter').value, state.selected); });
    $('#hierExpandAll').addEventListener('click', () => { for (const c of CLASSES) state.hierOpen.add(c.id); renderHierarchy(); });

    $$('[data-graph-action]').forEach(b => b.addEventListener('click', () => {
      const a = b.dataset.graphAction;
      if (a === 'fit') fitGraph();
      if (a === 'reset') { resetGraph(); fitGraph(); }
      if (a === 'all') { showAll(); setTimeout(fitGraph, 400); }
      if (a === 'expand') { if (state.selected) { ensureVisible(state.selected, true); startSim(); } }
      if (a === 'zoomin') zoomBy(1.2);
      if (a === 'zoomout') zoomBy(0.83);
      if (a === 'png') {
        const a = document.createElement('a');
        a.download = 'wco-dm-4.3.0-graph.png';
        a.href = graph.canvas.toDataURL('image/png');
        a.click();
        toast(t('png'));
      }
    }));

    $$('[data-prop-tab]').forEach(b => b.addEventListener('click', () => {
      state.propTab = b.dataset.propTab;
      state.propPage = 1;
      $$('[data-prop-tab]').forEach(x => x.classList.toggle('active', x === b));
      renderProperties();
    }));
    $('#propSearch').addEventListener('input', e => { state.propQuery = e.target.value; state.propPage = 1; renderProperties(); });
    $('#propClassFilter').addEventListener('change', e => { state.propClass = e.target.value; state.propPage = 1; renderProperties(); });
    $('#propCoreFilter').addEventListener('change', e => { state.propCore = e.target.value; state.propPage = 1; renderProperties(); });
    $('#propReset').addEventListener('click', () => {
      state.propQuery = ''; state.propClass = ''; state.propCore = ''; state.propPage = 1;
      $('#propSearch').value = ''; $('#propClassFilter').value = ''; $('#propCoreFilter').value = '';
      renderProperties();
    });
    $('#codeSearch').addEventListener('input', e => { state.codeQuery = e.target.value; renderCodeLists(); });
    $('#codeOnlyValues').addEventListener('change', e => { state.codeOnlyValues = e.target.checked; renderCodeLists(); });

    $('#profileSearch').addEventListener('input', e => { state.profileQuery = e.target.value; state.profilePage = 1; renderProfiles(); });
    $('#profileClassFilter').addEventListener('change', e => { state.profileClass = e.target.value; state.profilePage = 1; renderProfiles(); });
    $('#profileReset').addEventListener('click', () => {
      state.profileQuery = ''; state.profileClass = ''; state.profilePage = 1;
      $('#profileSearch').value = ''; $('#profileClassFilter').value = '';
      renderProfiles();
    });

    window.addEventListener('hashchange', () => {
      const { view, classId } = parseHash();
      setView(view, { keepHash: true });
      if (classId && BY_ID.has(classId)) openClass(classId);
    });
  }

  function init() {
    bind();
    bindGraph();
    const { view, classId } = parseHash();
    state.selected = classId && BY_ID.has(classId) ? classId : 'OIS';
    setView(view, { keepHash: true });
    renderTree($('#tree'), state.treeOpen, '', state.selected);
    renderDetails(state.selected, $('#details'));
    resizeCanvas();
    resetGraph(true);
    fitGraph();
    if (classId && BY_ID.has(classId)) openClass(classId);
    // initial gentle fit after the simulation settles
    setTimeout(fitGraph, 600);
    window.__WCO_DEBUG__ = { graph, state, BY_ID, CLASSES, EDGES };
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
