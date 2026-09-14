/*
 * geometry-probe.js — G1 deterministic layout probe for web pages (references/frontend-verification.md, P5).
 *
 * The whole file is ONE function expression (no trailing semicolon, no imports, no globals), so it can be
 * serialised into the page by Playwright or evaluated as a string by MCP browser tools.
 *
 * Findings (check names):
 *   h-overflow          document wider than the viewport; lists the widest offending elements
 *   clipped-text        element with its own text, clipping styles (overflow hidden/clip, text-overflow ellipsis,
 *                       line clamp) and content larger than its box. Skipped inside [data-truncate-ok]
 *   overlap             two visible interactive elements (not ancestor/descendant) whose boxes intersect
 *   off-viewport        visible interactive element outside [0, innerWidth] horizontally (vertical scroll is fine)
 *   target-size         enabled interactive element smaller than minTarget CSS px in width or height
 *                       (WCAG 2.2 SC 2.5.8). spacing_exception_met is an approximation: confirm by hand
 *   alignment-clusters  a container whose vertically stacked children have more than maxClusters distinct left
 *                       edges (±alignTolerance px) and are not centre-aligned
 *
 * Result: { url, viewport: {width, height, dpr}, options, counts: {<check>: n}, truncated, findings: [
 *   { n, check, selector, box: [x1, y1, x2, y2], label, details } ] }
 *   n = overlay box number for annotated screenshots; box = CSS px relative to the viewport at capture time.
 *   Multiply by viewport.dpr for device-pixel screenshots.
 *
 * Usage from Playwright (Node test or script):
 *   const fs = require('fs');
 *   const vm = require('vm');
 *   const probe = vm.runInNewContext(fs.readFileSync('.mission/bin/geometry-probe.js', 'utf8'));
 *   await page.waitForSelector('[data-testid=screen-ready]');          // reach the state first
 *   const result = await page.evaluate(probe, { minTarget: 24, alignTolerance: 2, maxClusters: 2 });
 *   fs.writeFileSync(outDir + '/g1-geometry-' + variant + '.json', JSON.stringify(result, null, 2));
 *   expect(result.findings.filter(f => f.check === 'h-overflow' || f.check === 'clipped-text')).toEqual([]);
 *
 * String form (Chrome DevTools MCP evaluate_script, Playwright MCP browser_evaluate): pass
 *   () => (<contents of this file>)({})
 *
 * Options (all optional): minTarget 24 · alignTolerance 2 · maxClusters 2 · minStackChildren 3 ·
 *   maxFindings 300 · maxInteractive 1500 · rootSelector 'body'
 * Mark intentional truncation with the attribute data-truncate-ok on the element or an ancestor.
 */
(function geometryProbe(rawOptions) {
  var opts = Object.assign({
    minTarget: 24,
    alignTolerance: 2,
    maxClusters: 2,
    minStackChildren: 3,
    maxFindings: 300,
    maxInteractive: 1500,
    rootSelector: 'body'
  }, rawOptions || {});

  var vw = window.innerWidth;
  var vh = window.innerHeight;
  var root = document.querySelector(opts.rootSelector) || document.body;
  var findings = [];
  var counts = {};
  var truncated = false;

  var INTERACTIVE = [
    'a[href]', 'button', 'input:not([type="hidden"])', 'select', 'textarea', 'summary',
    '[role="button"]', '[role="link"]', '[role="checkbox"]', '[role="radio"]', '[role="switch"]',
    '[role="tab"]', '[role="menuitem"]', '[role="option"]', '[role="slider"]',
    '[tabindex]:not([tabindex="-1"])', '[contenteditable=""]', '[contenteditable="true"]'
  ].join(',');

  function round(v) { return Math.round(v * 10) / 10; }

  function rectOf(el) {
    var r = el.getBoundingClientRect();
    return [round(r.left), round(r.top), round(r.right), round(r.bottom)];
  }

  function isVisible(el) {
    var r = el.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) { return false; }
    if (typeof el.checkVisibility === 'function') {
      if (!el.checkVisibility({ checkOpacity: true, checkVisibilityCSS: true })) { return false; }
    }
    var s = window.getComputedStyle(el);
    return s.display !== 'none' && s.visibility !== 'hidden' && s.visibility !== 'collapse' && s.opacity !== '0';
  }

  function isVisuallyHidden(el) {
    var r = el.getBoundingClientRect();
    var s = window.getComputedStyle(el);
    if (r.width <= 1 && r.height <= 1) { return true; }
    if (s.clip && s.clip !== 'auto' && /rect\(\s*0/.test(s.clip)) { return true; }
    if (s.clipPath && /inset\(\s*50%/.test(s.clipPath)) { return true; }
    return r.right < -500 || r.left > vw + 500;
  }

  function selectorOf(el) {
    if (el.id) { return '#' + CSS.escape(el.id); }
    var parts = [];
    var node = el;
    while (node && node.nodeType === 1 && parts.length < 4 && node !== document.documentElement) {
      var testId = node.getAttribute('data-testid');
      if (testId) { parts.unshift('[data-testid="' + testId + '"]'); break; }
      if (node.id) { parts.unshift('#' + CSS.escape(node.id)); break; }
      var tag = node.tagName.toLowerCase();
      var parent = node.parentElement;
      if (parent) {
        var same = Array.prototype.filter.call(parent.children, function (c) { return c.tagName === node.tagName; });
        if (same.length > 1) { tag += ':nth-of-type(' + (same.indexOf(node) + 1) + ')'; }
      }
      parts.unshift(tag);
      node = parent;
    }
    return parts.join(' > ');
  }

  function labelOf(el) {
    var t = el.getAttribute('aria-label') || el.getAttribute('title') || el.innerText || el.value || '';
    return String(t).replace(/\s+/g, ' ').trim().slice(0, 60);
  }

  function add(check, el, details) {
    counts[check] = (counts[check] || 0) + 1;
    if (findings.length >= opts.maxFindings) { truncated = true; return; }
    findings.push({
      n: findings.length + 1,
      check: check,
      selector: el ? selectorOf(el) : 'document',
      box: el ? rectOf(el) : [0, 0, round(document.documentElement.scrollWidth), vh],
      label: el ? labelOf(el) : '',
      details: details || {}
    });
  }

  function insideHorizontalScroller(el) {
    var node = el.parentElement;
    while (node && node !== document.body && node !== document.documentElement) {
      var ox = window.getComputedStyle(node).overflowX;
      if (ox === 'auto' || ox === 'scroll' || ox === 'hidden' || ox === 'clip') { return true; }
      node = node.parentElement;
    }
    return false;
  }

  function intersection(a, b) {
    var w = Math.min(a[2], b[2]) - Math.max(a[0], b[0]);
    var h = Math.min(a[3], b[3]) - Math.max(a[1], b[1]);
    return w > 0 && h > 0 ? round(w * h) : 0;
  }

  function hasOwnText(el) {
    for (var i = 0; i < el.childNodes.length; i++) {
      var c = el.childNodes[i];
      if (c.nodeType === 3 && c.textContent.trim().length > 0) { return true; }
    }
    return false;
  }

  function isDisabled(el) {
    return el.disabled === true || el.getAttribute('aria-disabled') === 'true';
  }

  // 1. Horizontal overflow of the document, with the widest offenders.
  var docWidth = document.documentElement.scrollWidth;
  if (docWidth > vw + 1) {
    var offenders = [];
    Array.prototype.forEach.call(root.querySelectorAll('*'), function (el) {
      if (!isVisible(el) || isVisuallyHidden(el)) { return; }
      var r = el.getBoundingClientRect();
      if (r.right > vw + 1 && !insideHorizontalScroller(el)) {
        offenders.push({ selector: selectorOf(el), right: round(r.right), box: rectOf(el) });
      }
    });
    offenders.sort(function (a, b) { return b.right - a.right; });
    add('h-overflow', null, { scrollWidth: docWidth, innerWidth: vw, widest: offenders.slice(0, 10) });
  }

  // 2. Clipped text (skips [data-truncate-ok] on the element or any ancestor).
  Array.prototype.forEach.call(root.querySelectorAll('*'), function (el) {
    var tag = el.tagName.toLowerCase();
    if (tag === 'input' || tag === 'textarea' || tag === 'select' || tag === 'option' || tag === 'script' ||
        tag === 'style' || tag === 'html' || tag === 'body') { return; }
    if (el.closest('[data-truncate-ok]')) { return; }
    if (!hasOwnText(el) || !isVisible(el) || isVisuallyHidden(el)) { return; }
    var s = window.getComputedStyle(el);
    var clips = /(hidden|clip)/.test(s.overflowX + ' ' + s.overflowY) || s.textOverflow === 'ellipsis' ||
      (s.webkitLineClamp && s.webkitLineClamp !== 'none');
    if (!clips) { return; }
    var overX = el.scrollWidth > el.clientWidth + 1;
    var overY = el.scrollHeight > el.clientHeight + 1;
    if (overX || overY) {
      add('clipped-text', el, {
        axis: overX && overY ? 'both' : (overX ? 'x' : 'y'),
        scrollWidth: el.scrollWidth, clientWidth: el.clientWidth,
        scrollHeight: el.scrollHeight, clientHeight: el.clientHeight,
        text: String(el.textContent).replace(/\s+/g, ' ').trim().slice(0, 80)
      });
    }
  });

  // Interactive elements used by checks 3–5.
  var interactive = Array.prototype.filter.call(root.querySelectorAll(INTERACTIVE), function (el) {
    return isVisible(el) && !isVisuallyHidden(el);
  });
  if (interactive.length > opts.maxInteractive) {
    truncated = true;
    interactive = interactive.slice(0, opts.maxInteractive);
  }
  var boxes = interactive.map(rectOf);

  // 3. Overlapping interactive elements.
  for (var i = 0; i < interactive.length; i++) {
    for (var j = i + 1; j < interactive.length; j++) {
      var a = interactive[i];
      var b = interactive[j];
      if (a.contains(b) || b.contains(a)) { continue; }
      var area = intersection(boxes[i], boxes[j]);
      if (area > 1) {
        add('overlap', a, { other: selectorOf(b), otherBox: boxes[j], otherLabel: labelOf(b), areaPx: area });
      }
    }
  }

  // 4. Off-viewport interactive elements (horizontal only).
  interactive.forEach(function (el, idx) {
    var bx = boxes[idx];
    if (bx[0] < -1 || bx[2] > vw + 1) {
      add('off-viewport', el, { innerWidth: vw, insideHorizontalScroller: insideHorizontalScroller(el) });
    }
  });

  // 5. Target size below minTarget CSS px, with an approximate WCAG 2.5.8 spacing-exception hint.
  var undersized = [];
  interactive.forEach(function (el, idx) {
    if (isDisabled(el)) { return; }
    var bx = boxes[idx];
    var w = round(bx[2] - bx[0]);
    var h = round(bx[3] - bx[1]);
    if (w < opts.minTarget || h < opts.minTarget) { undersized.push({ el: el, idx: idx, w: w, h: h }); }
  });
  undersized.forEach(function (u) {
    var bx = boxes[u.idx];
    var cx = (bx[0] + bx[2]) / 2;
    var cy = (bx[1] + bx[3]) / 2;
    var radius = opts.minTarget / 2;
    var spacingOk = true;
    for (var k = 0; k < interactive.length && spacingOk; k++) {
      if (k === u.idx || interactive[k].contains(u.el) || u.el.contains(interactive[k])) { continue; }
      var ob = boxes[k];
      var isOtherUndersized = undersized.some(function (o) { return o.idx === k; });
      if (isOtherUndersized) {
        var ocx = (ob[0] + ob[2]) / 2;
        var ocy = (ob[1] + ob[3]) / 2;
        if (Math.hypot(cx - ocx, cy - ocy) < opts.minTarget) { spacingOk = false; }
      } else {
        var dx = Math.max(ob[0] - cx, 0, cx - ob[2]);
        var dy = Math.max(ob[1] - cy, 0, cy - ob[3]);
        if (Math.hypot(dx, dy) < radius) { spacingOk = false; }
      }
    }
    var parentText = u.el.parentElement ? hasOwnText(u.el.parentElement) : false;
    var inlineCandidate = window.getComputedStyle(u.el).display === 'inline' && parentText;
    add('target-size', u.el, {
      width: u.w, height: u.h, minTarget: opts.minTarget,
      spacing_exception_met: spacingOk, inline_exception_candidate: inlineCandidate
    });
  });

  // 6. Left-edge alignment clusters per container (vertically stacked, not centre-aligned children).
  function clusterCount(values, tol) {
    var sorted = values.slice().sort(function (p, q) { return p - q; });
    var clusters = [];
    sorted.forEach(function (v) {
      var last = clusters[clusters.length - 1];
      if (last && v - last[0] <= tol) { last.push(v); } else { clusters.push([v]); }
    });
    return clusters;
  }
  Array.prototype.forEach.call(root.querySelectorAll('*'), function (container) {
    if (!isVisible(container)) { return; }
    var kids = Array.prototype.filter.call(container.children, function (c) {
      if (!isVisible(c) || isVisuallyHidden(c)) { return false; }
      var pos = window.getComputedStyle(c).position;
      return pos !== 'absolute' && pos !== 'fixed';
    });
    if (kids.length < opts.minStackChildren) { return; }
    var rects = kids.map(function (c) { return c.getBoundingClientRect(); });
    var order = rects.map(function (r, idx) { return idx; }).sort(function (p, q) { return rects[p].top - rects[q].top; });
    var stackedPairs = 0;
    for (var m = 1; m < order.length; m++) {
      if (rects[order[m]].top >= rects[order[m - 1]].bottom - 1) { stackedPairs++; }
    }
    if (stackedPairs < (order.length - 1) * 0.8) { return; }
    var lefts = rects.map(function (r) { return r.left; });
    var centres = rects.map(function (r) { return (r.left + r.right) / 2; });
    var leftClusters = clusterCount(lefts, opts.alignTolerance);
    if (leftClusters.length <= opts.maxClusters) { return; }
    if (clusterCount(centres, opts.alignTolerance).length === 1) { return; }
    add('alignment-clusters', container, {
      clusters: leftClusters.map(function (c) { return { left: round(c[0]), count: c.length }; }),
      maxClusters: opts.maxClusters,
      children: kids.slice(0, 12).map(function (c) { return { selector: selectorOf(c), box: rectOf(c) }; })
    });
  });

  return {
    url: location.href,
    viewport: { width: vw, height: vh, dpr: window.devicePixelRatio },
    options: opts,
    counts: counts,
    truncated: truncated,
    findings: findings
  };
})
