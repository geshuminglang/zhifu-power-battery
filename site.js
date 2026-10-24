/* ZHIFU — site behaviour (no dependencies) */
(function () {
  'use strict';

  var CFG = window.ZHIFU || {};

  function $(sel, root) { return (root || document).querySelector(sel); }
  function $all(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }

  /* ------------------------------------------------------------ header */
  function initHeader() {
    var header = $('#siteHeader');
    var toggle = $('#navToggle');
    var nav = $('#primaryNav');
    if (header) {
      var onScroll = function () {
        if (window.scrollY > 8) header.classList.add('is-stuck');
        else header.classList.remove('is-stuck');
      };
      onScroll();
      window.addEventListener('scroll', onScroll, { passive: true });
    }
    if (toggle && nav) {
      toggle.addEventListener('click', function () {
        var open = nav.classList.toggle('is-open');
        toggle.setAttribute('aria-expanded', String(open));
      });
      $all('a', nav).forEach(function (a) {
        a.addEventListener('click', function () {
          nav.classList.remove('is-open');
          toggle.setAttribute('aria-expanded', 'false');
        });
      });
      document.addEventListener('click', function (e) {
        if (!nav.classList.contains('is-open')) return;
        if (nav.contains(e.target) || toggle.contains(e.target)) return;
        nav.classList.remove('is-open');
        toggle.setAttribute('aria-expanded', 'false');
      });
    }
  }

  /* ------------------------------------------------------------ year */
  function initYear() {
    $all('[data-year]').forEach(function (el) { el.textContent = String(new Date().getFullYear()); });
  }

  /* ------------------------------------------------------------ product filters */
  function initFilters() {
    var bar = $('#filterBar');
    if (!bar) return;
    var cards = $all('.product-item');
    var countEl = $('#resultsCount');
    var emptyEl = $('#emptyState');
    var searchEl = $('#productSearch');
    var state = { voltage: 'all', capacity: 'all', q: '' };

    function apply() {
      var shown = 0;
      cards.forEach(function (card) {
        var v = card.getAttribute('data-voltage');
        var c = parseInt(card.getAttribute('data-capacity'), 10) || 0;
        var text = (card.getAttribute('data-keywords') || card.textContent || '').toLowerCase();
        var okV = state.voltage === 'all' || v === state.voltage;
        var okC = state.capacity === 'all' ||
          (state.capacity === 'low' && c <= 30) ||
          (state.capacity === 'mid' && c >= 60 && c <= 67) ||
          (state.capacity === 'high' && c >= 100);
        var okQ = !state.q || text.indexOf(state.q) !== -1;
        var show = okV && okC && okQ;
        card.hidden = !show;
        if (show) shown++;
      });
      if (countEl) countEl.textContent = shown + (shown === 1 ? ' product' : ' products');
      if (emptyEl) emptyEl.hidden = shown !== 0;
    }

    function bindGroup(attr, key) {
      $all('[data-filter-' + attr + ']').forEach(function (btn) {
        btn.addEventListener('click', function () {
          $all('[data-filter-' + attr + ']').forEach(function (b) { b.classList.remove('is-active'); });
          btn.classList.add('is-active');
          state[key] = btn.getAttribute('data-filter-' + attr);
          apply();
        });
      });
    }
    bindGroup('voltage', 'voltage');
    bindGroup('capacity', 'capacity');

    if (searchEl) {
      var t;
      searchEl.addEventListener('input', function () {
        clearTimeout(t);
        t = setTimeout(function () {
          state.q = searchEl.value.trim().toLowerCase();
          apply();
        }, 120);
      });
    }
    apply();
  }

  /* ------------------------------------------------------------ inquiry form */
  function buildMessage(data) {
    var lines = [];
    lines.push('Hello ZHIFU team,');
    lines.push('');
    lines.push('I would like to request a quotation.');
    lines.push('');
    lines.push('Product: ' + (data.product || '-'));
    lines.push('Quantity: ' + (data.quantity || '-'));
    lines.push('Company: ' + (data.company || '-'));
    lines.push('Country: ' + (data.country || '-'));
    if (data.message) {
      lines.push('');
      lines.push('Details: ' + data.message);
    }
    lines.push('');
    lines.push('Name: ' + (data.name || '-'));
    lines.push('Email: ' + (data.email || '-'));
    return lines.join('\n');
  }

  function initInquiry() {
    var form = $('#inquiryForm');
    if (!form) return;
    var status = $('#formStatus');

    // Preselect the product when arriving from a product page (?model=...)
    var params = new URLSearchParams(window.location.search);
    var model = params.get('model');
    var productField = $('#fieldProduct');
    var productSelect = $('#fieldProductSelect');
    if (model && productSelect) {
      $all('option', productSelect).forEach(function (o) { if (o.value === model) o.selected = true; });
    }
    if (model && productField) productField.value = model;

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var data = {
        product: (productField && productField.value) || (productSelect && productSelect.value) || '',
        quantity: ($('#fieldQuantity') || {}).value || '',
        company: ($('#fieldCompany') || {}).value || '',
        country: ($('#fieldCountry') || {}).value || '',
        name: ($('#fieldName') || {}).value || '',
        email: ($('#fieldEmail') || {}).value || '',
        message: ($('#fieldMessage') || {}).value || ''
      };
      if (!data.name || !data.email) {
        if (status) { status.textContent = 'Please enter your name and email.'; status.className = 'form-status'; }
        return;
      }
      var subject = 'Quotation request — ' + (data.product || 'ZHIFU battery');
      var body = buildMessage(data);
      var to = CFG.email || 'sales@example.com';
      var url = 'mailto:' + to + '?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);
      window.location.href = url;
      if (status) {
        status.textContent = 'Opening your email app… if nothing happens, write to ' + to + ' or use WhatsApp.';
        status.className = 'form-status is-ok';
      }
    });

    // WhatsApp shortcut
    var wa = $('#whatsappSend');
    if (wa) {
      wa.addEventListener('click', function (e) {
        e.preventDefault();
        var data = {
          product: (productField && productField.value) || (productSelect && productSelect.value) || '',
          quantity: ($('#fieldQuantity') || {}).value || '',
          company: ($('#fieldCompany') || {}).value || '',
          country: ($('#fieldCountry') || {}).value || '',
          name: ($('#fieldName') || {}).value || '',
          email: ($('#fieldEmail') || {}).value || '',
          message: ($('#fieldMessage') || {}).value || ''
        };
        var num = String(CFG.whatsapp || '').replace(/[^\d]/g, '');
        var link = num ? ('https://wa.me/' + num + '?text=' + encodeURIComponent(buildMessage(data)))
                       : (CFG.whatsappUrl || '#');
        window.open(link, '_blank', 'noopener');
      });
    }
  }

  /* ------------------------------------------------------------ dynamic QR */
  function initQr() {
    var box = $('#siteQr');
    if (!box || !window.QRCodeLite) return;
    var url = (CFG.siteUrl && CFG.siteUrl.indexOf('http') === 0)
      ? CFG.siteUrl
      : window.location.href.split('#')[0];
    try {
      var result = window.QRCodeLite.generate(url, { ecLevel: 'M' });
      box.innerHTML = window.QRCodeLite.toSVG(result, { unit: 6, quietZone: 3, dark: '#0b1f4b' });
      var dl = $('#qrDownload');
      if (dl) {
        var svg = window.QRCodeLite.toSVG(result, { unit: 12, quietZone: 4, dark: '#0b1f4b' });
        dl.setAttribute('href', 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg));
      }
      var urlEl = $('#qrUrl');
      if (urlEl) urlEl.textContent = url;
    } catch (err) {
      box.textContent = 'QR unavailable';
    }
  }

  /* ------------------------------------------------------------ copy link */
  function initCopy() {
    $all('[data-copy]').forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        var value = btn.getAttribute('data-copy-value') || window.location.href;
        function done() {
          var old = btn.getAttribute('data-label') || btn.textContent;
          btn.setAttribute('data-label', old);
          btn.textContent = 'Copied';
          setTimeout(function () { btn.textContent = old; }, 1600);
        }
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(value).then(done, done);
        } else {
          var ta = document.createElement('textarea');
          ta.value = value;
          document.body.appendChild(ta);
          ta.select();
          try { document.execCommand('copy'); } catch (err) { /* ignore */ }
          document.body.removeChild(ta);
          done();
        }
      });
    });
  }

  /* ------------------------------------------------------------ share */
  function initShare() {
    var btn = $('#shareBtn');
    if (!btn) return;
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      var data = { title: document.title, url: window.location.href };
      if (navigator.share) {
        navigator.share(data).catch(function () { /* cancelled */ });
      } else {
        var link = 'https://wa.me/?text=' + encodeURIComponent(document.title + ' ' + window.location.href);
        window.open(link, '_blank', 'noopener');
      }
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    initHeader();
    initYear();
    initFilters();
    initInquiry();
    initQr();
    initCopy();
    initShare();
  });
})();

