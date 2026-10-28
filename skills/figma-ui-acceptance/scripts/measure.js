/* Read-only function expression. Pass an observed unique selector or an Element.
 * Returns CSS px and computed styles; does not read form values or credentials.
 */
(...targets) => targets.map(target => {
  let el = target
  if (typeof target === 'string') {
    let matches
    try { matches = document.querySelectorAll(target) } catch { return { error: 'invalid selector' } }
    if (matches.length !== 1) return { error: 'selector must match exactly one element', matches: matches.length }
    el = matches[0]
  }
  if (!el || el.nodeType !== 1) return { error: 'not an element' }
  const s = getComputedStyle(el)
  const r = el.getBoundingClientRect()
  const round = n => Math.round(n * 100) / 100
  const sides = prefix => ['Top', 'Right', 'Bottom', 'Left'].map(d => s[prefix + d]).join(' ')
  const sensitiveInput = el.tagName === 'INPUT' || el.tagName === 'TEXTAREA'
  const text = sensitiveInput ? '' : (el.innerText || '').trim()
  return {
    text: text.slice(0, 120),
    rect: { x: round(r.x), y: round(r.y), width: round(r.width), height: round(r.height) },
    scroll: { x: window.scrollX, y: window.scrollY },
    fontFamily: s.fontFamily, fontSize: s.fontSize, fontWeight: s.fontWeight,
    lineHeight: s.lineHeight, letterSpacing: s.letterSpacing,
    color: s.color, backgroundColor: s.backgroundColor, opacity: s.opacity,
    borderWidth: ['Top', 'Right', 'Bottom', 'Left'].map(d => s['border' + d + 'Width']).join(' '),
    borderColor: ['Top', 'Right', 'Bottom', 'Left'].map(d => s['border' + d + 'Color']),
    borderRadius: s.borderRadius, boxShadow: s.boxShadow,
    padding: sides('padding'), margin: sides('margin'), gap: s.gap,
    display: s.display, position: s.position, objectFit: s.objectFit,
    whiteSpace: s.whiteSpace, textOverflow: s.textOverflow,
    overflowX: s.overflowX, overflowY: s.overflowY,
    contentSize: { scrollWidth: el.scrollWidth, clientWidth: el.clientWidth, scrollHeight: el.scrollHeight, clientHeight: el.clientHeight },
    overflowed: el.scrollWidth > el.clientWidth + 1 || el.scrollHeight > el.clientHeight + 1
  }
})
