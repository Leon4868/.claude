// Run: node --test scripts/render-report.test.mjs
import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import vm from 'node:vm'
import { spawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import { renderReport } from './render-report.mjs'

const dir = path.dirname(fileURLToPath(import.meta.url))
const PNG = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aXa0AAAAASUVORK5CYII=', 'base64')
const categories = ['布局与尺寸', '间距与对齐', '字体与文字', '颜色与表面', '图标与图片', '内容与溢出', '组件状态', '交互与滚动']
const checks = (result = '一致') => categories.map(category => ({ category, result, note: 'fixture evidence' }))

function fixture(run) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'ui-acceptance-test-'))
  try {
    fs.mkdirSync(path.join(root, 'design')); fs.mkdirSync(path.join(root, 'actual'))
    fs.writeFileSync(path.join(root, 'design/B-01.png'), PNG)
    fs.writeFileSync(path.join(root, 'actual/B-01.png'), PNG)
    fs.writeFileSync(path.join(root, 'actual/I-01.png'), PNG)
    return run(root, path.join(root, 'results.json'), path.join(root, 'report.html'))
  } finally { fs.rmSync(root, { recursive: true, force: true }) }
}
const staticSample = () => ({
  schemaVersion: 2,
  meta: { title: '<script>alert(1)</script>', design: 'Figma', environment: 'test' },
  boards: [
    { id: 'B-01', name: '列表', result: '有差异', designShot: 'design/B-01.png', actualShot: 'actual/B-01.png', checks: checks().map((c, i) => i === 2 ? { ...c, result: '有差异' } : c), items: [{ id: 'D-01', severity: '明显', element: '按钮', property: '文案', design: '配置通知', actual: '<b>通知配置</b>', method: '目测', impact: '按钮标签不同', suggestion: '采用设计文案', note: 'Figma 节点及整屏右侧按钮' }] },
    { id: 'B-02', name: '详情', result: '一致', designShot: 'design/B-01.png', actualShot: 'actual/B-01.png', checks: checks() }
  ]
})
// Use one real transition and one documented static-only board in all v2 fixtures.
const dynamicSample = () => {
  const data = staticSample()
  Object.assign(data.boards[0], {
    inventoryNote: '默认快照中发现状态筛选；设计未提供展开态',
    targets: [{ id: 'T-01', name: '状态筛选', kind: '筛选', source: '页面观察' }],
    interactions: [{ id: 'I-01', targetId: 'T-01', action: '展开状态筛选', expected: '选项列表可见', actual: '所有/已停止选项可见', result: '已验证', beforeShot: 'actual/B-01.png', afterShot: 'actual/I-01.png', cleanup: 'Escape关闭，下拉隐藏' }]
  })
  Object.assign(data.boards[1], { inventoryNote: '设计及页面快照为静态说明图', targets: [], interactions: [], interactionNote: '没有可操作控件、动态状态或滚动内容' })
  data.boards[1].checks[7] = { category: categories[7], result: '不适用', note: '静态说明图' }
  return data
}
const write = (file, data) => fs.writeFileSync(file, JSON.stringify(data))

test('embeds images, escapes text and computes HAS_DIFF', () => fixture((root, input, output) => {
  write(input, dynamicSample())
  const r = renderReport(input, output)
  const html = fs.readFileSync(output, 'utf8')
  assert.equal(r.overall, 'HAS_DIFF')
  assert.equal(r.diffs['明显'], 1)
  assert.equal(r.screenshots, 3)
  assert.equal(r.coverage.targets, 1)
  assert.equal(r.coverage.interactions['已验证'], 1)
  assert(html.includes('Escape关闭，下拉隐藏'))
  assert(html.includes('data:image/png;base64,'))
  assert(html.includes('&lt;b&gt;通知配置'))
  assert(!html.includes('<script>alert(1)'))
  assert.equal((html.match(/<script>/g) || []).length, 1)
  assert(!/(?:src|href)="https?:/.test(html))
  new vm.Script(html.split('<script>')[1].split('</script>')[0])
}))

test('overall verdict follows board results', () => fixture((root, input, output) => {
  const cases = [
    [b => { b[0].result = '一致'; delete b[0].items; b[0].checks = checks() }, 'PASSED'],
    [b => { b[1].result = '未覆盖'; b[1].note = '无样本'; b[1].checks[5].result = '未覆盖' }, 'PARTIAL'],
    [b => { b.forEach(x => { x.result = '受阻'; x.note = '需登录'; delete x.items; x.checks = checks('未覆盖') }); b[0].interactions[0].result = '受阻'; b[0].interactions[0].reason = '登录失效'; b[1].checks[7].result = '不适用' }, 'BLOCKED']
  ]
  for (const [mutate, expected] of cases) {
    const data = dynamicSample(); mutate(data.boards); write(input, data)
    assert.equal(renderReport(input, output).overall, expected)
  }
}))

test('rejects inconsistent data', () => fixture((root, input, output) => {
  const bad = [
    [d => { d.boards[0].items = [] }, /requires at least one item/],
    [d => { d.boards[1].items = [{ id: 'D-9', severity: '细微' }] }, /must not have items/],
    [d => { d.boards[1].result = '受阻' }, /requires a note/],
    [d => { d.boards[0].items[0].severity = 'major' }, /severity/],
    [d => { d.boards[1].id = 'B-01' }, /unique/],
    [d => { d.boards[0].designShot = '../escape.png' }, /outside evidence|ENOENT/]
  ]
  for (const [mutate, pattern] of bad) {
    const data = dynamicSample(); mutate(data); write(input, data)
    assert.throws(() => renderReport(input, output), pattern)
  }
  fs.writeFileSync(path.join(root, 'design/fake.png'), 'not an image')
  const data = dynamicSample(); data.boards[0].designShot = 'design/fake.png'; write(input, data)
  assert.throws(() => renderReport(input, output), /does not match/)
}))

test('CLI works through a symlinked skill directory', () => fixture((root, input, output) => {
  write(input, dynamicSample())
  fs.symlinkSync(dir, path.join(root, 'linked'))
  const run = spawnSync(process.execPath, [path.join(root, 'linked', 'render-report.mjs'), '--input', input, '--output', output], { encoding: 'utf8' })
  assert.equal(run.status, 0, run.stderr)
  assert.equal(JSON.parse(run.stdout).overall, 'HAS_DIFF')
}))

test('measure.js is a valid function expression', () => {
  const fn = new vm.Script('(' + fs.readFileSync(path.join(dir, 'measure.js'), 'utf8') + ')').runInNewContext({})
  assert.equal(typeof fn, 'function')
  assert.equal(JSON.stringify(fn(null)), JSON.stringify([{ error: 'not an element' }]))
})

test('prevents passing unchecked or undocumented boards', () => fixture((root, input, output) => {
  const cases = [
    [d => { delete d.boards[1].actualShot }, /requires screenshots/],
    [d => { d.boards[1].checks[0].result = '未覆盖' }, /covered checks/],
    [d => { d.boards[1].checks.pop() }, /all eight/],
    [d => { d.boards[1].checks[0].note = '' }, /evidence note/],
    [d => { delete d.boards[0].items[0].suggestion }, /missing suggestion/],
    [d => { d.boards[0].checks = checks() }, /agree with checks/]
  ]
  for (const [mutate, pattern] of cases) {
    const data = dynamicSample(); mutate(data); write(input, data)
    assert.throws(() => renderReport(input, output), pattern)
  }
}))

test('partial comparison retains confirmed differences even without a fully completed board', () => fixture((root, input, output) => {
  const data = dynamicSample(); data.boards.pop()
  data.boards[0].result = '未覆盖'; data.boards[0].note = '空态无样本'
  data.boards[0].checks[5].result = '未覆盖'
  write(input, data)
  const result = renderReport(input, output)
  assert.equal(result.overall, 'PARTIAL')
  assert.equal(result.diffs['明显'], 1)
  assert(fs.readFileSync(output, 'utf8').includes('空态无样本'))
}))

test('cannot complete a board with unexecuted or undocumented interactions', () => fixture((root, input, output) => {
  const cases = [
    [d => { delete d.boards[0].interactions }, /v2 requires/],
    [d => { d.boards[0].targets.push({ id: 'T-02', name: '横向滚动', kind: '滚动', source: '设计' }) }, /no interaction record/],
    [d => { d.boards[0].interactions[0].targetId = 'unknown' }, /unknown targetId/],
    [d => { d.boards[0].interactions[0].result = '未覆盖'; d.boards[0].interactions[0].reason = '尚未执行' }, /incomplete interactions/],
    [d => { delete d.boards[0].interactions[0].afterShot }, /requires distinct/],
    [d => { d.boards[0].interactions[0].afterShot = 'actual/B-01.png' }, /requires distinct/],
    [d => { delete d.boards[0].interactions[0].cleanup }, /requires distinct/],
    [d => { d.boards[0].interactions[0].result = '不适用' }, /requires reason/],
    [d => { d.boards[0].interactions[0].result = '有差异' }, /requires an issueId/],
    [d => { delete d.boards[1].interactionNote }, /static-only/],
    [d => { d.boards[0].checks[7].result = '不适用' }, /conflict with 不适用/]
  ]
  for (const [mutate, pattern] of cases) {
    const data = dynamicSample(); mutate(data); write(input, data)
    assert.throws(() => renderReport(input, output), pattern)
  }
}))

test('pending dynamic coverage gives PARTIAL and preserves already found defects', () => fixture((root, input, output) => {
  const data = dynamicSample()
  data.boards[0].result = '未覆盖'; data.boards[0].note = '滚动尚待执行'
  data.boards[0].targets.push({ id: 'T-02', name: '表格横向滚动', kind: '滚动', source: '设计' })
  data.boards[0].interactions.push({ id: 'I-02', targetId: 'T-02', action: '滚动到右端', expected: '状态列可见', actual: '尚未执行', result: '未覆盖', reason: '浏览器连接中断' })
  write(input, data)
  const result = renderReport(input, output)
  assert.equal(result.overall, 'PARTIAL')
  assert.equal(result.diffs['明显'], 1)
  assert.equal(result.coverage.interactions['未覆盖'], 1)
  assert(fs.readFileSync(output, 'utf8').includes('浏览器连接中断'))
}))

test('interaction difference must reference an existing board issue', () => fixture((root, input, output) => {
  const data = dynamicSample()
  Object.assign(data.boards[0].interactions[0], { result: '有差异', issueId: 'D-01' })
  write(input, data)
  assert.equal(renderReport(input, output).coverage.interactions['有差异'], 1)
}))

test('legacy static comparisons remain readable but cannot claim completed acceptance', () => fixture((root, input, output) => {
  const data = staticSample(); delete data.schemaVersion
  write(input, data)
  const result = renderReport(input, output)
  assert.equal(result.overall, 'PARTIAL')
  assert.equal(result.coverage.legacy, true)
  assert(fs.readFileSync(output, 'utf8').includes('旧版记录未提供逐项动态覆盖'))
}))

test('measure.js reads geometry without reading input values', () => {
  const element = { nodeType: 1, tagName: 'INPUT', get value() { throw new Error('must not read value') }, get innerText() { throw new Error('must not read input text') }, getBoundingClientRect: () => ({ x: 10, y: 20, width: 100, height: 32 }), scrollWidth: 100, clientWidth: 100, scrollHeight: 32, clientHeight: 32 }
  const fn = new vm.Script('(' + fs.readFileSync(path.join(dir, 'measure.js'), 'utf8') + ')').runInNewContext({ getComputedStyle: () => ({ fontSize: '14px' }), window: { scrollX: 0, scrollY: 0 }, document: { querySelectorAll: () => [element] } })
  const [result] = fn('input')
  assert.equal(result.text, '')
  assert.equal(result.rect.width, 100)
  assert.equal(result.fontSize, '14px')
  assert.equal(result.overflowed, false)
})
