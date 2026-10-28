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

function fixture(run) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'ui-acceptance-test-'))
  try {
    fs.mkdirSync(path.join(root, 'design')); fs.mkdirSync(path.join(root, 'actual'))
    fs.writeFileSync(path.join(root, 'design/B-01.png'), PNG)
    fs.writeFileSync(path.join(root, 'actual/B-01.png'), PNG)
    return run(root, path.join(root, 'results.json'), path.join(root, 'report.html'))
  } finally { fs.rmSync(root, { recursive: true, force: true }) }
}
const sample = () => ({
  meta: { title: '<script>alert(1)</script>', design: 'Figma', environment: 'test' },
  boards: [
    { id: 'B-01', name: '列表', result: '有差异', designShot: 'design/B-01.png', actualShot: 'actual/B-01.png', items: [{ id: 'D-01', severity: '明显', element: '按钮', property: '文案', design: '配置通知', actual: '<b>通知配置</b>' }] },
    { id: 'B-02', name: '详情', result: '一致' }
  ]
})
const write = (file, data) => fs.writeFileSync(file, JSON.stringify(data))

test('embeds images, escapes text and computes HAS_DIFF', () => fixture((root, input, output) => {
  write(input, sample())
  const r = renderReport(input, output)
  const html = fs.readFileSync(output, 'utf8')
  assert.equal(r.overall, 'HAS_DIFF')
  assert.equal(r.diffs['明显'], 1)
  assert.equal(r.screenshots, 2)
  assert(html.includes('data:image/png;base64,'))
  assert(html.includes('&lt;b&gt;通知配置'))
  assert(!html.includes('<script>alert(1)'))
  assert.equal((html.match(/<script>/g) || []).length, 1)
  assert(!/(?:src|href)="https?:/.test(html))
  new vm.Script(html.split('<script>')[1].split('</script>')[0])
}))

test('overall verdict follows board results', () => fixture((root, input, output) => {
  const cases = [
    [b => { b[0].result = '一致'; delete b[0].items }, 'PASSED'],
    [b => { b[1].result = '未覆盖'; b[1].note = '无样本' }, 'PARTIAL'],
    [b => { b[0].result = '受阻'; b[0].note = '需登录'; delete b[0].items; b[1].result = '受阻'; b[1].note = '需登录' }, 'BLOCKED']
  ]
  for (const [mutate, expected] of cases) {
    const data = sample(); mutate(data.boards); write(input, data)
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
    const data = sample(); mutate(data); write(input, data)
    assert.throws(() => renderReport(input, output), pattern)
  }
  fs.writeFileSync(path.join(root, 'design/fake.png'), 'not an image')
  const data = sample(); data.boards[0].designShot = 'design/fake.png'; write(input, data)
  assert.throws(() => renderReport(input, output), /does not match/)
}))

test('CLI works through a symlinked skill directory', () => fixture((root, input, output) => {
  write(input, sample())
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
