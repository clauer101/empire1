/**
 * Shared HTML escaping and highlighting utilities.
 */

export function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

export function escAttr(str) {
  return String(str).replace(/&/g, '&amp;').replace(/"/g, '&quot;');
}

export function hilite(str, q, escFn = escHtml) {
  if (!q) return escFn(str);
  const s = String(str);
  const idx = s.toLowerCase().indexOf(q.toLowerCase());
  if (idx === -1) return escFn(s);
  return (
    escFn(s.slice(0, idx)) +
    '<mark class="eac-hl">' +
    escFn(s.slice(idx, idx + q.length)) +
    '</mark>' +
    escFn(s.slice(idx + q.length))
  );
}
