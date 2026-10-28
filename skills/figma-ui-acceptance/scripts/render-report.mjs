// Offline single-file HTML report for UI acceptance. Node >= 18, no dependencies.
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const RESULTS = ['一致', '有差异', '未覆盖', '受阻']
const SEVERITIES = ['阻断', '明显', '细微']
const CATEGORIES = ['布局与尺寸', '间距与对齐', '字体与文字', '颜色与表面', '图标与图片', '内容与溢出', '组件状态', '交互与滚动']
const CHECK_RESULTS = ['一致', '有差异', '未覆盖', '不适用']
const INTERACTION_RESULTS = ['已验证', '有差异', '未覆盖', '受阻', '不适用']
const nonempty = value => typeof value === 'string' && value.trim().length > 0
const MIME = { '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp' }

const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]))

function overallOf(boards, legacy) {
  const done = boards.filter(b => b.designShot && b.actualShot && b.checks.some(c => c.result === '一致' || c.result === '有差异'))
  if (!done.length) return 'BLOCKED'
  if (legacy || boards.some(b => b.result === '未覆盖' || b.result === '受阻' || (b.interactions || []).some(i => i.result === '未覆盖' || i.result === '受阻'))) return 'PARTIAL'
  return boards.some(b => b.result === '有差异') ? 'HAS_DIFF' : 'PASSED'
}

export function renderReport(inputFile, outputFile) {
  if (!/\.html?$/i.test(outputFile)) throw new Error('Output must be an .html file')
  const source = fs.realpathSync(inputFile)
  const root = path.dirname(source)
  const input = JSON.parse(fs.readFileSync(source, 'utf8'))
  if (!input.meta || !Array.isArray(input.boards) || !input.boards.length) throw new Error('Require meta and a nonempty boards array')
  if (input.schemaVersion !== undefined && ![1, 2].includes(input.schemaVersion)) throw new Error('Unsupported schemaVersion')
  const legacy = input.schemaVersion !== 2
  if (input.timings !== undefined && (!Array.isArray(input.timings) || input.timings.some(t => !nonempty(t.phase) || !Number.isFinite(t.durationSeconds) || t.durationSeconds < 0 || (t.toolCalls !== undefined && (!Number.isInteger(t.toolCalls) || t.toolCalls < 0))))) throw new Error('Invalid timings: require phase, nonnegative durationSeconds and optional integer toolCalls')

  const images = new Map()
  const image = file => {
    if (!file) return ''
    if (typeof file !== 'string' || path.isAbsolute(file)) throw new Error('Screenshot must be a relative path')
    if (images.has(file)) return images.get(file)
    const resolved = fs.realpathSync(path.resolve(root, file))
    const relative = path.relative(root, resolved)
    if (relative.startsWith('..') || path.isAbsolute(relative)) throw new Error('Screenshot outside evidence directory: ' + file)
    const mime = MIME[path.extname(resolved).toLowerCase()]
    if (!mime) throw new Error('Only PNG/JPEG/WebP screenshots supported: ' + file)
    const bytes = fs.readFileSync(resolved)
    const ok = mime === 'image/png' ? bytes.subarray(0, 8).equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]))
      : mime === 'image/jpeg' ? bytes[0] === 0xff && bytes[1] === 0xd8 && bytes[2] === 0xff
        : bytes.toString('ascii', 0, 4) === 'RIFF' && bytes.toString('ascii', 8, 12) === 'WEBP'
    if (!ok) throw new Error('Screenshot content does not match its extension: ' + file)
    const uri = `data:${mime};base64,${bytes.toString('base64')}`
    images.set(file, uri)
    return uri
  }

  const ids = new Set()
  for (const b of input.boards) {
    if (!b.id || ids.has(b.id)) throw new Error('Board ids must be unique and nonempty: ' + b.id)
    ids.add(b.id)
    if (!RESULTS.includes(b.result)) throw new Error(`Board ${b.id}: result must be one of ${RESULTS.join('/')}`)
    const items = b.items || []
    if (!Array.isArray(items)) throw new Error(`Board ${b.id}: items must be an array`)
    if (b.result === '有差异' && !items.length) throw new Error(`Board ${b.id}: 有差异 requires at least one item`)
    if (b.result === '一致' && items.length) throw new Error(`Board ${b.id}: 一致 must not have items`)
    if ((b.result === '未覆盖' || b.result === '受阻') && !b.note) throw new Error(`Board ${b.id}: ${b.result} requires a note`)
    if (!Array.isArray(b.checks) || b.checks.length !== CATEGORIES.length || new Set(b.checks.map(c => c.category)).size !== CATEGORIES.length) throw new Error(`Board ${b.id}: checks must include all eight unique categories`)
    for (const c of b.checks) {
      if (!CATEGORIES.includes(c.category) || !CHECK_RESULTS.includes(c.result) || !nonempty(c.note)) throw new Error(`Board ${b.id}: invalid check or missing evidence note`)
    }
    const incomplete = b.checks.some(c => c.result === '未覆盖')
    const compared = b.checks.some(c => c.result === '一致' || c.result === '有差异')
    const differs = b.checks.some(c => c.result === '有差异')
    if ((b.result === '一致' || b.result === '有差异') && (incomplete || !compared || !b.designShot || !b.actualShot)) throw new Error(`Board ${b.id}: completed comparison requires screenshots and covered checks`)
    if (b.result === '一致' && differs) throw new Error(`Board ${b.id}: 一致 conflicts with a differing check`)
    if ((items.length > 0) !== differs) throw new Error(`Board ${b.id}: differences must agree with checks`)
    if (b.result === '受阻' && compared) throw new Error(`Board ${b.id}: compared checks require 未覆盖 rather than 受阻`)
    for (const i of items) {
      if (!i.id || ids.has(i.id)) throw new Error('Item ids must be unique and nonempty: ' + i.id)
      ids.add(i.id)
      if (!SEVERITIES.includes(i.severity)) throw new Error(`Item ${i.id}: severity must be one of ${SEVERITIES.join('/')}`)
      for (const key of ['element', 'property', 'design', 'actual', 'impact', 'suggestion', 'note']) {
        if (!nonempty(i[key])) throw new Error(`Item ${i.id}: missing ${key}`)
      }
      if (!['测量', '目测'].includes(i.method)) throw new Error(`Item ${i.id}: method must be 测量/目测`)
      if (!(i.designShot || b.designShot) || !(i.actualShot || b.actualShot)) throw new Error(`Item ${i.id}: requires design and actual evidence screenshots`)
      image(i.designShot); image(i.actualShot)
    }
    image(b.designShot); image(b.actualShot)
    if (!legacy) {
      if (!nonempty(b.inventoryNote) || !Array.isArray(b.targets) || !Array.isArray(b.interactions)) throw new Error(`Board ${b.id}: v2 requires inventoryNote, targets and interactions`)
      const targetIds = new Set()
      for (const t of b.targets) {
        if (!nonempty(t.id) || ids.has(t.id)) throw new Error('Target ids must be unique and nonempty: ' + t.id)
        ids.add(t.id); targetIds.add(t.id)
        if (!nonempty(t.name) || !nonempty(t.kind) || !['设计', '页面观察'].includes(t.source)) throw new Error(`Target ${t.id}: require name, kind and source 设计/页面观察`)
      }
      if (!b.targets.length && (!nonempty(b.interactionNote) || b.interactions.length || b.checks.find(c => c.category === '交互与滚动').result !== '不适用')) throw new Error(`Board ${b.id}: static-only comparison requires interactionNote and 不适用 interaction check`)
      for (const i of b.interactions) {
        if (!nonempty(i.id) || ids.has(i.id)) throw new Error('Interaction ids must be unique and nonempty: ' + i.id)
        ids.add(i.id)
        if (!targetIds.has(i.targetId)) throw new Error(`Interaction ${i.id}: unknown targetId`)
        if (!INTERACTION_RESULTS.includes(i.result)) throw new Error(`Interaction ${i.id}: invalid result`)
        for (const key of ['action', 'expected', 'actual']) if (!nonempty(i[key])) throw new Error(`Interaction ${i.id}: missing ${key}`)
        if (['已验证', '有差异'].includes(i.result)) {
          if (!nonempty(i.beforeShot) || !nonempty(i.afterShot) || i.beforeShot === i.afterShot || !nonempty(i.cleanup)) throw new Error(`Interaction ${i.id}: executed transition requires distinct beforeShot/afterShot and cleanup`)
          image(i.beforeShot); image(i.afterShot)
          if (b.result === '受阻') throw new Error(`Board ${b.id}: executed interactions require 未覆盖 rather than 受阻`)
        } else if (!nonempty(i.reason)) throw new Error(`Interaction ${i.id}: ${i.result} requires reason`)
        if (i.result === '有差异' && !items.some(item => item.id === i.issueId)) throw new Error(`Interaction ${i.id}: difference requires an issueId from this board`)
      }
      for (const t of b.targets) if (!b.interactions.some(i => i.targetId === t.id)) throw new Error(`Target ${t.id}: no interaction record`)
      const pending = b.interactions.some(i => ['未覆盖', '受阻'].includes(i.result))
      if (pending && ['一致', '有差异'].includes(b.result)) throw new Error(`Board ${b.id}: incomplete interactions cannot be marked completed`)
      if (b.interactions.some(i => i.result !== '不适用') && b.checks.find(c => c.category === '交互与滚动').result === '不适用') throw new Error(`Board ${b.id}: active interaction targets conflict with 不适用 check`)
    }
  }

  const boards = input.boards
  const overall = overallOf(boards, legacy)
  const interactions = boards.flatMap(b => b.interactions || [])
  const interactionCounts = Object.fromEntries(INTERACTION_RESULTS.map(r => [r, interactions.filter(i => i.result === r).length]))
  const targetCount = boards.reduce((n, b) => n + (b.targets || []).length, 0)
  const allItems = boards.flatMap(b => (b.items || []).map(i => ({ ...i, board: b })))
  const resultCounts = Object.fromEntries(RESULTS.map(r => [r, boards.filter(b => b.result === r).length]))
  const severityCounts = Object.fromEntries(SEVERITIES.map(s => [s, allItems.filter(i => i.severity === s).length]))

  const shot = (file, label) => file
    ? `<figure><button type="button" class="shot" aria-label="放大 ${escape(label)}"><img src="${image(file)}" alt="${escape(label)}"></button><figcaption>${escape(label)}</figcaption></figure>`
    : `<figure class="empty"><figcaption>${escape(label)}：无截图</figcaption></figure>`
  const pair = (d, a, label) => (d || a) ? `<div class="pair">${shot(d, label + ' · 设计稿')}${shot(a, label + ' · 实际页面')}</div>` : ''
  const itemHtml = i => `<article class="item" data-sev="${escape(i.severity)}" data-search="${escape([i.id, i.element, i.property, i.design, i.actual, i.note, i.board.name].join(' '))}">
<header><strong>${escape(i.id)}</strong><span class="sev s-${escape(i.severity)}">${escape(i.severity)}</span><span>${escape(i.element)}${i.property ? ' · ' + escape(i.property) : ''}</span><span class="muted">${escape(i.method)}</span></header>
<dl><dt>设计值</dt><dd>${escape(i.design)}</dd><dt>实际值</dt><dd>${escape(i.actual)}</dd><dt>影响</dt><dd>${escape(i.impact)}</dd><dt>修改建议</dt><dd>${escape(i.suggestion)}</dd><dt>依据</dt><dd>${escape(i.note)}</dd></dl>${pair(i.designShot, i.actualShot, i.id)}</article>`
  const interactionHtml = b => legacy ? '' : `<details open><summary>动态覆盖：${b.targets.length} 个目标 / ${b.interactions.length} 条转换</summary><p>${escape(b.inventoryNote)}</p>${b.interactionNote ? `<p>${escape(b.interactionNote)}</p>` : ''}${b.interactions.map(i => {
    const t = b.targets.find(t => t.id === i.targetId)
    return `<article class="interaction"><strong>${escape(i.id)} · ${escape(t.name)}</strong> <span class="res">${escape(i.result)}</span><span class="muted"> ${escape(t.kind)} · 依据：${escape(t.source)}</span><dl>${[['操作',i.action],['预期',i.expected],['实际',i.actual],['原因',i.reason],['还原现场',i.cleanup],['问题',i.issueId],['依据',i.note]].filter(([,v]) => v).map(([k,v]) => `<dt>${escape(k)}</dt><dd>${escape(v)}</dd>`).join('')}</dl>${i.beforeShot || i.afterShot ? `<details><summary>查看操作前后证据</summary><div class="pair">${shot(i.beforeShot,i.id+' · 操作前')}${shot(i.afterShot,i.id+' · 操作后')}</div></details>` : ''}</article>`
  }).join('')}</details>`
  const boardHtml = b => `<section class="board" id="${escape(b.id)}">
<h3>${escape(b.id)} · ${escape(b.name)} <span class="res r-${escape(b.result)}">${escape(b.result)}</span></h3>
<p class="muted">${escape(b.state || '')}${b.page ? ' · ' + escape(String(b.page).split(/[?#]/)[0]) : ''}</p>${b.note ? `<p>${escape(b.note)}</p>` : ''}
<p class="muted">${[b.designNode && 'Figma 节点 ' + b.designNode, b.viewport, b.steps && '进入路径：' + b.steps].filter(Boolean).map(escape).join(' · ')}</p>
<details><summary>查看检查覆盖与依据</summary><dl>${b.checks.map(c => `<dt>${escape(c.category)}</dt><dd><strong>${escape(c.result)}</strong> · ${escape(c.note)}</dd>`).join('')}</dl></details>
${interactionHtml(b)}${pair(b.designShot, b.actualShot, b.id)}${(b.items || []).map(i => itemHtml({ ...i, board: b })).join('')}</section>`

  const m = input.meta
  const html = `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${escape(m.title || 'UI 验收报告')}</title><style>
*{box-sizing:border-box}body{margin:0;background:#f5f6fa;color:#1d2433;font:14px/1.6 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif}main{max-width:1200px;margin:auto;padding:28px 20px}
.hero{background:#2b2350;color:#fff;border-radius:14px;padding:24px 28px}.hero h1{margin:4px 0 6px;font-size:26px}.hero p{margin:0;color:#d6d0f5}
.verdict{display:inline-block;margin-top:12px;padding:4px 10px;border-radius:6px;font-weight:700;background:#fff;color:#2b2350}
.stats{display:grid;grid-template-columns:repeat(7,1fr);gap:10px;margin:18px 0}.stat{background:#fff;border:1px solid #e1e4ee;border-radius:10px;padding:12px}.stat b{display:block;font-size:24px}
.panel{background:#fff;border:1px solid #e1e4ee;border-radius:12px;padding:20px;margin-top:18px}h2{font-size:19px;margin:0 0 12px}h3{font-size:16px;margin:0}
.toolbar{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px}button,input{font:inherit}.toolbar button{border:1px solid #c9cde0;background:#fff;border-radius:6px;padding:5px 12px;cursor:pointer}.toolbar button.on{background:#2b2350;color:#fff;border-color:#2b2350}.toolbar input{margin-left:auto;border:1px solid #c9cde0;border-radius:6px;padding:5px 10px;min-width:220px}
.board{border-top:1px solid #e1e4ee;padding:16px 0}.muted{color:#6b7389;font-size:12px;margin:4px 0 10px}
.item,.interaction{border-left:3px solid #d6d9e6;padding:8px 0 8px 14px;margin:12px 0}.item header{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
dl{display:grid;grid-template-columns:90px 1fr;gap:2px 10px;margin:8px 0;font-size:13px}dt{color:#6b7389}dd{margin:0;overflow-wrap:anywhere}summary{cursor:pointer;color:#55467e}details{margin:10px 0}
.sev,.res{font-size:12px;font-weight:700;padding:2px 8px;border-radius:5px}.s-阻断,.r-受阻{background:#ffe5e5;color:#b42318}.s-明显{background:#fff0d6;color:#a15c07}.s-细微{background:#eceff5;color:#4a5468}.r-一致{background:#e3f6ea;color:#1b7a43}.r-有差异{background:#fff0d6;color:#a15c07}.r-未覆盖{background:#eceff5;color:#4a5468}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:8px}figure{margin:0}figcaption{font-size:12px;color:#6b7389;margin-top:4px}.shot{display:block;width:100%;padding:0;border:1px solid #e1e4ee;border-radius:6px;background:#f5f6fa;cursor:zoom-in;overflow:hidden}.shot img{display:block;width:100%;max-height:460px;object-fit:contain}.empty{border:1px dashed #c9cde0;border-radius:6px;padding:20px;text-align:center}
dialog{border:0;border-radius:10px;padding:10px;max-width:96vw}dialog::backdrop{background:#0d0b1fcc}dialog img{display:block;max-width:92vw;max-height:84vh}
[hidden]{display:none!important}
@media(max-width:760px){.stats{grid-template-columns:repeat(2,1fr)}.pair{grid-template-columns:1fr}.toolbar input{margin-left:0;width:100%}}
@media print{.toolbar,dialog{display:none}body{background:#fff}.board,.item{break-inside:avoid}}
</style></head><body><main>
<section class="hero"><div>UI 设计验收</div><h1>${escape(m.title || 'UI 验收报告')}</h1><p>${escape(m.design || '')}</p><p>${escape(m.environment || '')}${m.viewport ? ' · ' + escape(m.viewport) : ''}</p><span class="verdict">${{PASSED:'已验范围一致',HAS_DIFF:'已完成，有差异',PARTIAL:'部分完成，存在未覆盖项',BLOCKED:'尚无有效比较'}[overall]} · ${overall}</span></section>
<section class="stats">${RESULTS.map(r => `<div class="stat"><b>${resultCounts[r]}</b>画板 ${r}</div>`).join('')}${SEVERITIES.map(s => `<div class="stat"><b>${severityCounts[s]}</b>${s}差异</div>`).join('')}</section>
<section class="panel"><h2>交互覆盖</h2>${legacy ? '<p>旧版记录未提供逐项动态覆盖；已有比较保留，不能据此判定完整验收通过。</p>' : `<p>${targetCount} 个验收目标 · ${interactionCounts['已验证'] + interactionCounts['有差异']} 条已执行转换 · ${interactionCounts['未覆盖'] + interactionCounts['受阻']} 条未覆盖/受阻 · ${interactionCounts['不适用']} 条不适用</p><p class="muted">统计仅覆盖清单中已列出的目标；设计依据与页面观察在各条记录中说明。</p>`}</section>
<section class="panel"><h2>差异清单（${allItems.length}）</h2><div class="toolbar"><button type="button" class="on" data-f="ALL">全部</button>${SEVERITIES.map(s => `<button type="button" data-f="${s}">${s} ${severityCounts[s]}</button>`).join('')}<input type="search" id="q" placeholder="搜索元素、文案、画板" aria-label="搜索差异"></div>
<p class="muted" id="count"></p>${boards.map(boardHtml).join('')}</section>
${(input.notes || []).length ? `<section class="panel"><h2>备注</h2>${input.notes.map(n => `<p>${escape(n)}</p>`).join('')}</section>` : ''}
${(input.timings || []).length ? `<section class="panel"><h2>执行耗时</h2><dl>${input.timings.map(t => `<dt>${escape(t.phase)}</dt><dd>${escape(t.durationSeconds)} 秒${t.toolCalls === undefined ? '' : ' · ' + escape(t.toolCalls) + ' 次调用'}</dd>`).join('')}</dl></section>` : ''}
<section class="panel"><h2>验收信息</h2><dl>${Object.entries(m).map(([k, v]) => `<dt>${escape(({title:'名称',design:'设计范围',environment:'环境',viewport:'视口',tester:'验收人',startedAt:'开始时间',endedAt:'结束时间'})[k] || k)}</dt><dd>${escape(v)}</dd>`).join('')}</dl></section>
</main><dialog id="v"><img id="vi" alt=""></dialog><script>
const items=[...document.querySelectorAll('.item')];let f='ALL';
function upd(){const q=document.getElementById('q').value.trim().toLowerCase();let n=0;items.forEach(e=>{e.hidden=!((f==='ALL'||e.dataset.sev===f)&&e.dataset.search.toLowerCase().includes(q));if(!e.hidden)n++});document.getElementById('count').textContent='显示 '+n+' / '+items.length+' 条差异'}
document.querySelectorAll('[data-f]').forEach(b=>b.onclick=()=>{f=b.dataset.f;document.querySelectorAll('[data-f]').forEach(x=>x.classList.toggle('on',x===b));upd()});
document.getElementById('q').oninput=upd;upd();
const v=document.getElementById('v');document.querySelectorAll('.shot').forEach(b=>b.onclick=()=>{const i=b.querySelector('img');document.getElementById('vi').src=i.src;v.showModal()});v.onclick=()=>v.close();
</script></body></html>`
  fs.writeFileSync(outputFile, html)
  return { output: path.resolve(outputFile), overall, boards: resultCounts, diffs: severityCounts, screenshots: images.size, coverage: { legacy, targets: targetCount, interactions: interactionCounts } }
}

// Compare real paths so the CLI also works when the skill directory is reached through a symlink.
if (process.argv[1] && fs.realpathSync(process.argv[1]) === fs.realpathSync(fileURLToPath(import.meta.url))) {
  try {
    const args = process.argv.slice(2)
    if (args.length !== 4 || args[0] !== '--input' || args[2] !== '--output') throw new Error('Usage: node render-report.mjs --input results.json --output report.html')
    if (path.resolve(args[1]) === path.resolve(args[3])) throw new Error('Output must not overwrite input')
    console.log(JSON.stringify(renderReport(args[1], args[3])))
  } catch (error) {
    console.error(error.message)
    process.exitCode = 1
  }
}
