// Offline single-file HTML report for UI acceptance. Node >= 18, no dependencies.
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const RESULTS = ['一致', '有差异', '未覆盖', '受阻']
const SEVERITIES = ['阻断', '明显', '细微']
const MIME = { '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp' }

const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]))

function overallOf(boards) {
  const done = boards.filter(b => b.result === '一致' || b.result === '有差异')
  if (!done.length) return 'BLOCKED'
  if (boards.some(b => b.result === '未覆盖' || b.result === '受阻')) return 'PARTIAL'
  return boards.some(b => b.result === '有差异') ? 'HAS_DIFF' : 'PASSED'
}

export function renderReport(inputFile, outputFile) {
  if (!/\.html?$/i.test(outputFile)) throw new Error('Output must be an .html file')
  const source = fs.realpathSync(inputFile)
  const root = path.dirname(source)
  const input = JSON.parse(fs.readFileSync(source, 'utf8'))
  if (!input.meta || !Array.isArray(input.boards) || !input.boards.length) throw new Error('Require meta and a nonempty boards array')

  const images = new Map()
  const image = file => {
    if (!file) return ''
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
    for (const i of items) {
      if (!i.id || ids.has(i.id)) throw new Error('Item ids must be unique and nonempty: ' + i.id)
      ids.add(i.id)
      if (!SEVERITIES.includes(i.severity)) throw new Error(`Item ${i.id}: severity must be one of ${SEVERITIES.join('/')}`)
      image(i.designShot); image(i.actualShot)
    }
    image(b.designShot); image(b.actualShot)
  }

  const boards = input.boards
  const overall = overallOf(boards)
  const allItems = boards.flatMap(b => (b.items || []).map(i => ({ ...i, board: b })))
  const resultCounts = Object.fromEntries(RESULTS.map(r => [r, boards.filter(b => b.result === r).length]))
  const severityCounts = Object.fromEntries(SEVERITIES.map(s => [s, allItems.filter(i => i.severity === s).length]))

  const shot = (file, label) => file
    ? `<figure><button type="button" class="shot" aria-label="放大 ${escape(label)}"><img src="${image(file)}" alt="${escape(label)}"></button><figcaption>${escape(label)}</figcaption></figure>`
    : `<figure class="empty"><figcaption>${escape(label)}：无截图</figcaption></figure>`
  const pair = (d, a, label) => (d || a) ? `<div class="pair">${shot(d, label + ' · 设计稿')}${shot(a, label + ' · 实际页面')}</div>` : ''
  const itemHtml = i => `<article class="item" data-sev="${escape(i.severity)}" data-search="${escape([i.id, i.element, i.property, i.design, i.actual, i.note, i.board.name].join(' '))}">
<header><strong>${escape(i.id)}</strong><span class="sev s-${escape(i.severity)}">${escape(i.severity)}</span><span>${escape(i.element)}${i.property ? ' · ' + escape(i.property) : ''}</span></header>
<dl><dt>设计值</dt><dd>${escape(i.design)}</dd><dt>实际值</dt><dd>${escape(i.actual)}</dd>${i.note ? `<dt>说明</dt><dd>${escape(i.note)}</dd>` : ''}</dl>${pair(i.designShot, i.actualShot, i.id)}</article>`
  const boardHtml = b => `<section class="board" id="${escape(b.id)}">
<h3>${escape(b.id)} · ${escape(b.name)} <span class="res r-${escape(b.result)}">${escape(b.result)}</span></h3>
<p class="muted">${escape(b.state || '')}${b.page ? ' · ' + escape(String(b.page).split(/[?#]/)[0]) : ''}</p>${b.note ? `<p>${escape(b.note)}</p>` : ''}
${pair(b.designShot, b.actualShot, b.id)}${(b.items || []).map(i => itemHtml({ ...i, board: b })).join('')}</section>`

  const m = input.meta
  const html = `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${escape(m.title || 'UI 验收报告')}</title><style>
*{box-sizing:border-box}body{margin:0;background:#f5f6fa;color:#1d2433;font:14px/1.6 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif}main{max-width:1200px;margin:auto;padding:28px 20px}
.hero{background:#2b2350;color:#fff;border-radius:14px;padding:24px 28px}.hero h1{margin:4px 0 6px;font-size:26px}.hero p{margin:0;color:#d6d0f5}
.verdict{display:inline-block;margin-top:12px;padding:4px 10px;border-radius:6px;font-weight:700;background:#fff;color:#2b2350}
.stats{display:grid;grid-template-columns:repeat(7,1fr);gap:10px;margin:18px 0}.stat{background:#fff;border:1px solid #e1e4ee;border-radius:10px;padding:12px}.stat b{display:block;font-size:24px}
.panel{background:#fff;border:1px solid #e1e4ee;border-radius:12px;padding:20px;margin-top:18px}h2{font-size:19px;margin:0 0 12px}h3{font-size:16px;margin:0}
.toolbar{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px}button,input{font:inherit}.toolbar button{border:1px solid #c9cde0;background:#fff;border-radius:6px;padding:5px 12px;cursor:pointer}.toolbar button.on{background:#2b2350;color:#fff;border-color:#2b2350}.toolbar input{margin-left:auto;border:1px solid #c9cde0;border-radius:6px;padding:5px 10px;min-width:220px}
.board{border-top:1px solid #e1e4ee;padding:16px 0}.muted{color:#6b7389;font-size:12px;margin:4px 0 10px}
.item{border-left:3px solid #d6d9e6;padding:8px 0 8px 14px;margin:12px 0}.item header{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
dl{display:grid;grid-template-columns:70px 1fr;gap:2px 10px;margin:8px 0;font-size:13px}dt{color:#6b7389}dd{margin:0;overflow-wrap:anywhere}
.sev,.res{font-size:12px;font-weight:700;padding:2px 8px;border-radius:5px}.s-阻断,.r-受阻{background:#ffe5e5;color:#b42318}.s-明显{background:#fff0d6;color:#a15c07}.s-细微{background:#eceff5;color:#4a5468}.r-一致{background:#e3f6ea;color:#1b7a43}.r-有差异{background:#fff0d6;color:#a15c07}.r-未覆盖{background:#eceff5;color:#4a5468}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:8px}figure{margin:0}figcaption{font-size:12px;color:#6b7389;margin-top:4px}.shot{display:block;width:100%;padding:0;border:1px solid #e1e4ee;border-radius:6px;background:#f5f6fa;cursor:zoom-in;overflow:hidden}.shot img{display:block;width:100%;max-height:460px;object-fit:contain}.empty{border:1px dashed #c9cde0;border-radius:6px;padding:20px;text-align:center}
dialog{border:0;border-radius:10px;padding:10px;max-width:96vw}dialog::backdrop{background:#0d0b1fcc}dialog img{display:block;max-width:92vw;max-height:84vh}
[hidden]{display:none!important}
@media(max-width:760px){.stats{grid-template-columns:repeat(2,1fr)}.pair{grid-template-columns:1fr}.toolbar input{margin-left:0;width:100%}}
@media print{.toolbar,dialog{display:none}body{background:#fff}.board,.item{break-inside:avoid}}
</style></head><body><main>
<section class="hero"><div>UI ACCEPTANCE</div><h1>${escape(m.title || 'UI 验收报告')}</h1><p>${escape(m.design || '')}</p><p>${escape(m.environment || '')}${m.viewport ? ' · ' + escape(m.viewport) : ''}</p><span class="verdict">总结论 ${overall}</span></section>
<section class="stats">${RESULTS.map(r => `<div class="stat"><b>${resultCounts[r]}</b>画板 ${r}</div>`).join('')}${SEVERITIES.map(s => `<div class="stat"><b>${severityCounts[s]}</b>${s}差异</div>`).join('')}</section>
<section class="panel"><h2>差异清单（${allItems.length}）</h2><div class="toolbar"><button type="button" class="on" data-f="ALL">全部</button>${SEVERITIES.map(s => `<button type="button" data-f="${s}">${s} ${severityCounts[s]}</button>`).join('')}<input type="search" id="q" placeholder="搜索元素、文案、画板" aria-label="搜索差异"></div>
<p class="muted" id="count"></p>${boards.map(boardHtml).join('')}</section>
${(input.notes || []).length ? `<section class="panel"><h2>备注</h2>${input.notes.map(n => `<p>${escape(n)}</p>`).join('')}</section>` : ''}
<section class="panel"><h2>验收信息</h2><dl>${Object.entries(m).map(([k, v]) => `<dt>${escape(k)}</dt><dd>${escape(v)}</dd>`).join('')}</dl></section>
</main><dialog id="v"><img id="vi" alt=""></dialog><script>
const items=[...document.querySelectorAll('.item')];let f='ALL';
function upd(){const q=document.getElementById('q').value.trim().toLowerCase();let n=0;items.forEach(e=>{e.hidden=!((f==='ALL'||e.dataset.sev===f)&&e.dataset.search.toLowerCase().includes(q));if(!e.hidden)n++});document.getElementById('count').textContent='显示 '+n+' / '+items.length+' 条差异'}
document.querySelectorAll('[data-f]').forEach(b=>b.onclick=()=>{f=b.dataset.f;document.querySelectorAll('[data-f]').forEach(x=>x.classList.toggle('on',x===b));upd()});
document.getElementById('q').oninput=upd;upd();
const v=document.getElementById('v');document.querySelectorAll('.shot').forEach(b=>b.onclick=()=>{const i=b.querySelector('img');document.getElementById('vi').src=i.src;v.showModal()});v.onclick=()=>v.close();
</script></body></html>`
  fs.writeFileSync(outputFile, html)
  return { output: path.resolve(outputFile), overall, boards: resultCounts, diffs: severityCounts, screenshots: images.size }
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
