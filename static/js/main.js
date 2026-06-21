/* LeMédia — main.js */
document.addEventListener('DOMContentLoaded', function () {

  /* ── Auto-dismiss alerts ──────────────────────────────────────────────── */
  document.querySelectorAll('.alert-dismissible').forEach(function (a) {
    setTimeout(function () {
      var inst = bootstrap.Alert.getOrCreateInstance(a);
      if (inst) inst.close();
    }, 5000);
  });

  /* ── Navbar desktop shadow on scroll ──────────────────────────────────── */
  var nav = document.getElementById('mainNav');
  if (nav) {
    window.addEventListener('scroll', function () {
      nav.classList.toggle('shadow', window.scrollY > 50);
    });
  }

  /* ── Barre de progression lecture ─────────────────────────────────────── */
  var bar = document.createElement('div');
  bar.style.cssText =
    'position:fixed;top:0;left:0;height:3px;background:#e63946;' +
    'z-index:9999;width:0;transition:width .1s;pointer-events:none';
  document.body.prepend(bar);
  window.addEventListener('scroll', function () {
    var doc = document.documentElement;
    var pct = (doc.scrollTop / (doc.scrollHeight - doc.clientHeight)) * 100;
    bar.style.width = Math.min(pct, 100) + '%';
  });

  /* ── Bouton retour en haut ─────────────────────────────────────────────── */
  var btt = document.createElement('button');
  btt.innerHTML = '<i class="fas fa-arrow-up"></i>';
  btt.setAttribute('aria-label', 'Retour en haut');
  btt.style.cssText =
    'position:fixed;bottom:80px;right:20px;width:40px;height:40px;' +
    'border-radius:50%;background:#1a2c4e;color:#fff;border:none;cursor:pointer;' +
    'box-shadow:0 4px 12px rgba(0,0,0,.25);opacity:0;transition:opacity .3s;' +
    'z-index:999;font-size:14px;display:flex;align-items:center;justify-content:center;';
  document.body.appendChild(btt);
  window.addEventListener('scroll', function () {
    btt.style.opacity = window.scrollY > 400 ? '1' : '0';
  });
  btt.addEventListener('click', function () {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  /* ══════════════════════════════════════════════════════════════════════
     MOBILE — Recherche dépliable
     ══════════════════════════════════════════════════════════════════ */
  var searchBtn  = document.getElementById('mobileSearchToggle');
  var searchBar  = document.getElementById('mobileSearchBar');

  if (searchBtn && searchBar) {
    searchBtn.addEventListener('click', function () {
      var open = searchBar.classList.toggle('open');
      searchBtn.querySelector('i').className = open
        ? 'fas fa-times'
        : 'fas fa-search';
      if (open) {
        var inp = searchBar.querySelector('input');
        if (inp) inp.focus();
      }
    });
  }

  /* ══════════════════════════════════════════════════════════════════════
     MOBILE — Panel catégories (bottom sheet)
     ══════════════════════════════════════════════════════════════════ */
  var btnCat   = document.getElementById('btnCategories');
  var panel    = document.getElementById('categoriesPanel');
  var overlay  = document.getElementById('catPanelOverlay');
  var closeBtn = document.getElementById('closeCategoriesPanel');

  function openPanel() {
    panel.classList.add('open');
    overlay.classList.add('show');
    document.body.style.overflow = 'hidden';
  }

  function closePanel() {
    panel.classList.remove('open');
    overlay.classList.remove('show');
    document.body.style.overflow = '';
  }

  if (btnCat)   btnCat.addEventListener('click', openPanel);
  if (closeBtn) closeBtn.addEventListener('click', closePanel);
  if (overlay)  overlay.addEventListener('click', closePanel);

  /* Swipe vers le bas pour fermer le panel */
  if (panel) {
    var startY = 0;
    panel.addEventListener('touchstart', function (e) {
      startY = e.touches[0].clientY;
    }, { passive: true });
    panel.addEventListener('touchend', function (e) {
      var diff = e.changedTouches[0].clientY - startY;
      if (diff > 60) closePanel();
    }, { passive: true });
  }

  /* ── Fermer le panel si on clique un lien à l'intérieur ──────────────── */
  if (panel) {
    panel.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', closePanel);
    });
  }

  /* ── Bottom nav : activer visuellement l'item courant ────────────────── */
  var path  = window.location.pathname;
  document.querySelectorAll('.bottom-nav-item').forEach(function (el) {
    var href = el.getAttribute('href');
    if (!href) return;
    if (
      (href === '/' && path === '/') ||
      (href !== '/' && path.startsWith(href))
    ) {
      el.classList.add('active');
    }
  });

});
