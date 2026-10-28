/* Read-only style probe for chrome-devtools `evaluate_script`.
 * Pass this file's content as `function`, and the target elements as `args` ([{ uid }, ...]).
 * Returns CSS-px geometry and computed styles; never modifies the page.
 */
(...elements) => {
  const hex = value => {
    const m = String(value).match(/rgba?\(([^)]+)\)/)
    if (!m) return value
    const [r, g, b, a = '1'] = m[1].split(/[,\s/]+/).filter(Boolean)
    const h = [r, g, b].map(n => Math.round(Number(n)).toString(16).padStart(2, '0')).join('')
    return Number(a) < 1 ? `#${h} / ${Number(a)}` : `#${h}`
  }
  const box = (s, side) => ['Top', 'Right', 'Bottom', 'Left'].map(d => s[side + d]).join(' ')
  return elements.map(el => {
    if (!el || el.nodeType !== 1) return { error: 'not an element' }
    const s = getComputedStyle(el)
    const r = el.getBoundingClientRect()
    const text = (el.innerText || el.value || el.placeholder || '').trim()
    return {
      text: text.length > 80 ? text.slice(0, 80) + '…' : text,
      placeholder: el.placeholder || undefined,
      rect: { x: Math.round(r.x * 10) / 10, y: Math.round(r.y * 10) / 10, width: Math.round(r.width * 10) / 10, height: Math.round(r.height * 10) / 10 },
      fontFamily: s.fontFamily,
      fontSize: s.fontSize,
      fontWeight: s.fontWeight,
      lineHeight: s.lineHeight,
      color: hex(s.color),
      backgroundColor: hex(s.backgroundColor),
      borderWidth: [s.borderTopWidth, s.borderRightWidth, s.borderBottomWidth, s.borderLeftWidth].join(' '),
      borderColor: hex(s.borderTopColor),
      borderRadius: s.borderRadius,
      boxShadow: s.boxShadow === 'none' ? undefined : s.boxShadow,
      padding: box(s, 'padding'),
      margin: box(s, 'margin'),
      gap: s.gap === 'normal' ? undefined : s.gap,
      opacity: s.opacity === '1' ? undefined : s.opacity,
      overflowed: el.scrollWidth > el.clientWidth + 1 || el.scrollHeight > el.clientHeight + 1
    }
  })
}
