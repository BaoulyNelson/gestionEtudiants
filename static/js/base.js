/* ============================================================
   FASCH — Système de Gestion Universitaire
   Scripts principaux (base.js)
   ============================================================ */

/* ── Select2 ─────────────────────────────────────────────── */
$(document).ready(function () {
  $("select.form-select").select2({
    placeholder: "Rechercher...",
    allowClear: true,
    width: "100%"
  });
});

/* ── Dashboard principal ─────────────────────────────────── */
(function () {
  "use strict";

  // Références DOM
  const sidebar = document.getElementById("sidebar");
  const sidebarOverlay = document.getElementById("sidebarOverlay");
  const mobileMenuToggle = document.getElementById("mobileMenuToggle");
  const sidebarClose = document.getElementById("sidebarClose");
  const mainContent = document.getElementById("mainContent");
  const mobileSearchToggle = document.getElementById("mobileSearchToggle");
  const mobileSearchForm = document.getElementById("mobileSearchForm");
  const searchForm = document.getElementById("searchForm");

  // Initialisation au chargement du DOM
  document.addEventListener("DOMContentLoaded", function () {
    initializeDashboard();
    setupEventListeners();
    updateActiveMenuItem();
    initializeSearch();
  });

  // ── Layout responsive ────────────────────────────────────
  function initializeDashboard() {
    updateLayout();

    let resizeTimeout;
    window.addEventListener("resize", function () {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(updateLayout, 150);
    });

    function updateLayout() {
      const isDesktop = window.innerWidth >= 992;

      if (isDesktop) {
        sidebar.classList.add("active");
        mainContent.classList.add("expanded");
        sidebarOverlay.classList.remove("show");
        document.body.style.overflow = "";
      } else {
        sidebar.classList.remove("active");
        mainContent.classList.remove("expanded");
        sidebarOverlay.classList.remove("show");
        document.body.style.overflow = "";
      }
    }
  }

  // ── Event listeners ──────────────────────────────────────
  function setupEventListeners() {
    if (mobileMenuToggle)
      mobileMenuToggle.addEventListener("click", toggleSidebar);
    if (sidebarClose) sidebarClose.addEventListener("click", toggleSidebar);

    if (sidebarOverlay) {
      sidebarOverlay.addEventListener("click", function (e) {
        if (e.target === sidebarOverlay) toggleSidebar();
      });
    }

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && sidebar.classList.contains("active"))
        toggleSidebar();
    });

    document.addEventListener("touchmove", preventBodyScroll, {
      passive: false
    });

    // Fermeture du dropdown utilisateur au clic extérieur
    document.addEventListener("click", function (e) {
      const dropdown = document.querySelector(".dropdown-menu");
      const dropdownToggle = document.getElementById("userDropdown");

      if (
        dropdown &&
        !dropdown.contains(e.target) &&
        !dropdownToggle.contains(e.target)
      ) {
        const bsDropdown = bootstrap.Dropdown.getInstance(dropdownToggle);
        if (bsDropdown) bsDropdown.hide();
      }
    });

    // Fermeture après clic sur un item du dropdown
    document.addEventListener("click", function (e) {
      if (e.target.closest(".dropdown-item")) {
        const bsDropdown = bootstrap.Dropdown.getInstance(
          document.getElementById("userDropdown")
        );
        if (bsDropdown) setTimeout(() => bsDropdown.hide(), 100);
      }
    });
  }

  // ── Toggle sidebar ────────────────────────────────────────
  function toggleSidebar() {
    const isActive = sidebar.classList.contains("active");

    if (isActive) {
      sidebar.classList.remove("active");
      mainContent.classList.remove("expanded");
      sidebarOverlay.classList.remove("show");
      document.body.style.overflow = "";
    } else {
      sidebar.classList.add("active");
      mainContent.classList.add("expanded");
      sidebarOverlay.classList.add("show");
      document.body.style.overflow = "hidden";

      const firstMenuItem = sidebar.querySelector(".sidebar-menu-link");
      if (firstMenuItem) firstMenuItem.focus();
    }
  }

  // ── Blocage du scroll body sur mobile ────────────────────
  function preventBodyScroll(e) {
    const isMobile = window.innerWidth < 992;
    const sidebarActive = sidebar.classList.contains("active");

    if (isMobile && sidebarActive && !sidebar.contains(e.target)) {
      e.preventDefault();
    }
  }

  // ── Menu actif selon l'URL ────────────────────────────────
  function updateActiveMenuItem() {
    const currentPath = window.location.pathname;
    const menuLinks = document.querySelectorAll(".sidebar-menu-link");

    menuLinks.forEach((link) => {
      const href = link.getAttribute("href");
      link.classList.remove("active");

      if (
        href === currentPath ||
        href === currentPath + "/" ||
        currentPath.startsWith(href + "/")
      ) {
        link.classList.add("active");
      }
    });
  }

  // ── Recherche ─────────────────────────────────────────────
  function initializeSearch() {
    if (mobileSearchToggle && mobileSearchForm) {
      mobileSearchToggle.addEventListener("click", function () {
        const isVisible = !mobileSearchForm.classList.contains("d-none");

        if (isVisible) {
          mobileSearchForm.classList.add("d-none");
          this.innerHTML = '<i class="fas fa-search"></i>';
        } else {
          mobileSearchForm.classList.remove("d-none");
          this.innerHTML = '<i class="fas fa-times"></i>';

          const mobileSearchInput = mobileSearchForm.querySelector(
            'input[type="search"]'
          );
          if (mobileSearchInput)
            setTimeout(() => mobileSearchInput.focus(), 100);
        }
      });

      document.addEventListener("click", function (e) {
        if (
          !mobileSearchForm.contains(e.target) &&
          !mobileSearchToggle.contains(e.target) &&
          !mobileSearchForm.classList.contains("d-none")
        ) {
          mobileSearchForm.classList.add("d-none");
          mobileSearchToggle.innerHTML = '<i class="fas fa-search"></i>';
        }
      });
    }

    const searchInputs = document.querySelectorAll(".search-input");
    searchInputs.forEach((input) => {
      input.addEventListener("focus", function () {
        this.parentElement.classList.add("focused");
      });
      input.addEventListener("blur", function () {
        this.parentElement.classList.remove("focused");
      });

      let searchTimeout;
      input.addEventListener("input", function () {
        clearTimeout(searchTimeout);
        const query = this.value.trim();

        if (query.length > 2) {
          searchTimeout = setTimeout(() => {
            console.log("Searching for:", query);
            // TODO : brancher ici la logique de recherche
          }, 300);
        }
      });
    });
  }

  // ── Utilitaires ───────────────────────────────────────────
  function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  // ── Auto-masquage des alertes succès ──────────────────────
  function initializeAlerts() {
    document.querySelectorAll(".alert-success").forEach((alert) => {
      if (!alert.classList.contains("alert-important")) {
        setTimeout(() => {
          const bsAlert = new bootstrap.Alert(alert);
          if (bsAlert) bsAlert.close();
        }, 6000);
      }
    });
  }

  // ── Tooltips Bootstrap ────────────────────────────────────
  function initializeTooltips() {
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach((el) => {
      new bootstrap.Tooltip(el);
    });
  }

  // ── Smooth scroll ─────────────────────────────────────────
  function initializeSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
      anchor.addEventListener("click", function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute("href"));
        if (target)
          target.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    });
  }

  // ── Optimisations perf ────────────────────────────────────
  function optimizePerformance() {
    // Lazy-load des images
    const imageObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const img = entry.target;
          img.src = img.dataset.src;
          img.classList.remove("lazy");
          observer.unobserve(img);
        }
      });
    });

    document
      .querySelectorAll("img[data-src]")
      .forEach((img) => imageObserver.observe(img));

    // Reduced motion pour les connexions lentes
    if ("connection" in navigator && navigator.connection.saveData) {
      document.documentElement.classList.add("reduced-motion");
    }
  }

  // ── Initialisation globale ────────────────────────────────
  function initializeAll() {
    initializeAlerts();
    initializeTooltips();
    initializeSmoothScroll();
    optimizePerformance();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeAll);
  } else {
    initializeAll();
  }

  console.log(
    "🎓 FASCH Dashboard - Professional Edition initialized successfully"
  );
  console.log("📱 Fully responsive design with modern UX patterns");
  console.log("🎨 Designed with accessibility and performance in mind");
})();

/* ── Bottom Sheet (menu "Plus" — mobile) ─────────────────── */
(function () {
  var sheet = document.getElementById("bottomSheet");
  var overlay = document.getElementById("bottomSheetOverlay");
  var btnOpen = document.getElementById("btnBottomSheet");
  var btnClose = document.getElementById("closeBottomSheet");

  function openSheet() {
    sheet.classList.add("open");
    overlay.classList.add("show");
    document.body.style.overflow = "hidden";
  }

  function closeSheet() {
    sheet.classList.remove("open");
    overlay.classList.remove("show");
    document.body.style.overflow = "";
  }

  if (btnOpen) btnOpen.addEventListener("click", openSheet);
  if (btnClose) btnClose.addEventListener("click", closeSheet);
  if (overlay) overlay.addEventListener("click", closeSheet);

  // Swipe vers le bas pour fermer
  if (sheet) {
    var startY = 0;

    sheet.addEventListener(
      "touchstart",
      function (e) {
        startY = e.touches[0].clientY;
      },
      { passive: true }
    );

    sheet.addEventListener(
      "touchend",
      function (e) {
        if (e.changedTouches[0].clientY - startY > 65) closeSheet();
      },
      { passive: true }
    );

    sheet.querySelectorAll("a").forEach(function (a) {
      a.addEventListener("click", closeSheet);
    });
  }

  // Highlight de l'onglet actif selon l'URL
  var path = window.location.pathname;
  document.querySelectorAll(".bn-item[href]").forEach(function (el) {
    var href = el.getAttribute("href");
    if (!href || href === "#") return;
    if (
      (href === "/" && path === "/") ||
      (href !== "/" && path.startsWith(href))
    ) {
      el.classList.add("active");
    }
  });
})();
