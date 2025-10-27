// =====================================================
// FASCH - Université d'État d'Haïti
// JavaScript Principal - Version Optimisée
// =====================================================

// Configuration globale
const CONFIG = {
    autoSlideInterval: 5000,
    animationThreshold: 150,
    countdownDeadline: '2026-03-15T23:59:59',
    countdownUpdateInterval: 3600000,
    formMinMotivationLength: 100,
    phoneRegex: /^\+?509[0-9]{9}$/,
    emailRegex: /^[^\s@]+@[^\s@]+\.[^\s@]+$/
};

// Variables globales
let currentSlide = 0;
let departments = {}; // Sera initialisé plus tard

// =====================================================
// INITIALISATION
// =====================================================
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Initialiser les composants
    initHeroCarousel();
    initDepartmentNavigation();
    initScrollAnimations();
    initSmoothScrolling();
    initSearchFunctionality();
    initAdmissionForm();
    initCostCalculator();
    initCountdown();
    
    // Déclencheurs spécifiques
    if (document.getElementById('admission-form')) {
        setupFormValidation();
    }
    
    if (document.querySelector('.dept-nav-btn')) {
        showDepartment('psychology'); // Département par défaut
    }
}

// =====================================================
// HERO CAROUSEL
// =====================================================
const heroSlides = [
    {
        image: staticBase + "images/faculte.png",
        title: "50 Ans d'Excellence en Sciences Humaines",
        subtitle: "Formant les leaders de demain en psychologie, sociologie, travail social et communication depuis 1975"
    },
    {
        image: staticBase + "images/fasch1.jpg",
        title: "Étude approfondie des processus cognitifs et de leurs applications cliniques",
        subtitle: "Rejoignez FASCH et façonnez l'avenir des sciences humaines en Haïti. Découvrez nos programmes d'excellence et commencez votre candidature dès aujourd'hui."
    },
    {
        image: staticBase + "images/fasch2.jpg",
        title: "Recherche de Pointe en Sciences Sociales",
        subtitle: "Nos professeurs et étudiants contribuent activement à la compréhension de la société haïtienne contemporaine"
    },
    {
        image: staticBase + "images/fasch3.jpg",
        title: "Innovation Pédagogique et Impact Social",
        subtitle: "Des programmes adaptés aux défis modernes d'Haïti avec une approche pratique et communautaire"
    }
];

function initHeroCarousel() {
    updateHeroDots();
    startAutoSlide();
}

function changeHeroSlide(index) {
    currentSlide = index;
    updateHeroContent();
    updateHeroDots();
}

function updateHeroContent() {
    const slide = heroSlides[currentSlide];
    const heroContent = document.getElementById('hero-content');
    const heroBg = document.getElementById('hero-bg');
    
    if (!heroContent || !heroBg) return;
    
    heroContent.style.opacity = '0';
    
    setTimeout(() => {
        heroContent.innerHTML = `
            <h1 class="display-3 fw-bold font-playfair mb-4 text-balance">${slide.title}</h1>
            <p class="lead fs-3 mb-5 opacity-90">${slide.subtitle}</p>
            <div class="d-flex flex-column flex-sm-row gap-3 justify-content-center">
                <a href="#" class="btn btn-secondary-custom btn-lg px-5 py-3">Commencer Votre Parcours</a>
                <a href="#" class="border-2 border-white text-white px-5 py-3 rounded fw-semibold text-decoration-none transition-all">
                    Explorer Nos Programmes
                </a>
            </div>
        `;
        heroBg.src = slide.image;
        heroContent.style.opacity = '1';
    }, 250);
}

function updateHeroDots() {
    const dots = document.querySelectorAll('.hero-dot');
    dots.forEach((dot, index) => {
        dot.style.opacity = index === currentSlide ? '1' : '0.5';
    });
}

function startAutoSlide() {
    setInterval(() => {
        currentSlide = (currentSlide + 1) % heroSlides.length;
        updateHeroContent();
        updateHeroDots();
    }, CONFIG.autoSlideInterval);
}

// =====================================================
// NAVIGATION DÉPARTEMENTALE
// =====================================================
const departmentTitles = {
    'psychology': 'Département de Psychologie - FASCH',
    'sociology': 'Département de Sociologie - FASCH',
    'social-work': 'Département de Travail Social - FASCH',
    'communication': 'Département de Communication - FASCH'
};

function initDepartmentNavigation() {
    document.querySelectorAll('.dept-nav-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const dept = this.dataset.department;
            showDepartment(dept);
        });
    });
}

function showDepartment(dept) {
    // Validation
    if (!departments[dept]) return;
    
    // Mise à jour des boutons de navigation
    document.querySelectorAll('.dept-nav-btn').forEach(btn => {
        btn.classList.remove('active', 'shadow-sm');
        btn.classList.add('shadow-sm');
    });
    event?.target?.closest('.dept-nav-btn')?.classList.add('active');
    event?.target?.closest('.dept-nav-btn')?.classList.remove('shadow-sm');
    
    // Mise à jour du fond hero
    const heroBg = document.getElementById('dept-hero-bg');
    if (heroBg) {
        heroBg.src = departments[dept].image;
        heroBg.onerror = function() {
            this.src = departments[dept].fallback;
            this.onerror = null;
        };
    }
    
    // Affichage/masquage des sections
    document.querySelectorAll('.department-content').forEach(content => {
        content.classList.remove('active');
    });
    const targetContent = document.getElementById(dept + '-content');
    if (targetContent) {
        targetContent.classList.add('active');
    }
    
    // Mise à jour du titre de la page
    document.title = departmentTitles[dept] || 'Programmes Départementaux - FASCH';
}

// =====================================================
// ANIMATIONS ET SCROLL
// =====================================================
function initScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                // Animation fade-in classique
                entry.target.classList.add('visible');
            }
        });
    }, observerOptions);
    
    // Éléments à animer
    const animatedElements = document.querySelectorAll('.fade-in, .career-card');
    animatedElements.forEach(element => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';
        element.style.transition = 'all 0.6s ease';
        observer.observe(element);
    });
    
    // Animation manuelle pour compatibilité
    handleScrollAnimations();
}

function handleScrollAnimations() {
    const elements = document.querySelectorAll('.fade-in:not(.visible)');
    elements.forEach(element => {
        const elementTop = element.getBoundingClientRect().top;
        if (elementTop < window.innerHeight - CONFIG.animationThreshold) {
            element.classList.add('visible');
        }
    });
}

function initSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const target = document.querySelector(targetId);
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Fonctions de scroll spécifiques
function scrollToSection(sectionId) {
    const target = document.getElementById(sectionId);
    if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

// =====================================================
// RECHERCHE ET FILTRES
// =====================================================
function initSearchFunctionality() {
    // Toggle recherche avancée
    const advancedToggle = document.getElementById('advanced-search-toggle');
    if (advancedToggle) {
        advancedToggle.addEventListener('click', toggleAdvancedSearch);
    }
    
    // Focus sur la recherche principale
    const mainSearch = document.getElementById('main-search');
    if (mainSearch) {
        mainSearch.addEventListener('focus', function() {
            this.scrollIntoView({ behavior: 'smooth', block: 'center' });
        });
    }
}

function toggleAdvancedSearch() {
    const advancedSearch = document.getElementById('advanced-search');
    const toggleText = document.getElementById('advanced-toggle-text');
    const toggleIcon = document.getElementById('advanced-toggle-icon');
    
    if (!advancedSearch) return;
    
    const bsCollapse = new bootstrap.Collapse(advancedSearch, { toggle: true });
    
    advancedSearch.addEventListener('shown.bs.collapse', function() {
        if (toggleText) toggleText.textContent = 'Recherche Simple';
        if (toggleIcon) toggleIcon.classList.add('rotated');
    });
    
    advancedSearch.addEventListener('hidden.bs.collapse', function() {
        if (toggleText) toggleText.textContent = 'Recherche Avancée';
        if (toggleIcon) toggleIcon.classList.remove('rotated');
    });
}

function performSearch() {
    const searchTerm = document.getElementById('main-search')?.value || '';
    console.log('Recherche:', searchTerm);
    // Logique de recherche API ici
    return false;
}

function resetFilters() {
    // Reset des sélecteurs
    const selects = document.querySelectorAll('#advanced-search select');
    selects.forEach(select => select.value = '');
    
    // Reset du champ principal
    const mainSearch = document.getElementById('main-search');
    if (mainSearch) mainSearch.value = '';
    
    performSearch();
}

// =====================================================
// FORMULAIRE D'ADMISSION
// =====================================================
function initAdmissionForm() {
    const form = document.getElementById('admission-form');
    if (form) {
        form.addEventListener('submit', handleAdmissionSubmit);
        
        // Écouteurs pour sauvegarde brouillon
        const saveDraftBtn = document.getElementById('save-draft');
        if (saveDraftBtn) {
            saveDraftBtn.addEventListener('click', saveDraft);
        }
    }
}

function setupFormValidation() {
    const requiredFields = ['prenom', 'nom', 'email', 'telephone', 'programme', 'lettre_motivation', 'accepte_conditions'];
    
    requiredFields.forEach(field => {
        const element = document.getElementById(field);
        if (element) {
            element.addEventListener('input', function() {
                this.classList.remove('is-invalid');
                const errorEl = document.getElementById(field + '-error');
                if (errorEl) errorEl.textContent = '';
            });
            
            // Validation en temps réel pour email et téléphone
            if (field === 'email') {
                element.addEventListener('blur', validateEmail);
            } else if (field === 'telephone') {
                element.addEventListener('blur', validatePhone);
            }
        }
    });
}

function handleAdmissionSubmit(e) {
    e.preventDefault();
    
    if (!validateAdmissionForm()) {
        return false;
    }
    
    // Simulation de soumission
    showFormMessage('Votre candidature a été soumise avec succès! Vous recevrez une confirmation par email dans les prochaines minutes.', 'success');
    this.reset();
    return false;
}

function validateAdmissionForm() {
    const formData = new FormData(document.getElementById('admission-form'));
    const errors = [];
    
    // Nettoyage des erreurs précédentes
    document.querySelectorAll('.form-error, .is-invalid').forEach(el => {
        if (el.classList) el.classList.remove('is-invalid');
        if (el.tagName === 'SMALL') el.textContent = '';
    });
    
    // Validation des champs requis
    const requiredFields = ['prenom', 'nom', 'email', 'telephone', 'programme', 'lettre_motivation'];
    requiredFields.forEach(field => {
        const element = document.getElementById(field);
        const value = element?.value?.trim() || '';
        
        if (!value) {
            addFieldError(element, `${getFieldLabel(field)} est requis.`);
            errors.push(field);
        }
    });
    
    // Validation email
    const email = document.getElementById('email')?.value;
    if (email && !CONFIG.emailRegex.test(email)) {
        addFieldError(document.getElementById('email'), 'Veuillez entrer un email valide.');
        errors.push('email');
    }
    
    // Validation téléphone
    const phone = document.getElementById('telephone')?.value;
    if (phone && !CONFIG.phoneRegex.test(phone.replace(/\s/g, ''))) {
        addFieldError(document.getElementById('telephone'), 'Veuillez entrer un numéro de téléphone haïtien valide.');
        errors.push('telephone');
    }
    
    // Validation lettre de motivation
    const motivation = document.getElementById('lettre_motivation')?.value;
    if (motivation && motivation.length < CONFIG.formMinMotivationLength) {
        addFieldError(document.getElementById('lettre_motivation'), 
            `La lettre de motivation doit contenir au moins ${CONFIG.formMinMotivationLength} caractères.`);
        errors.push('lettre_motivation');
    }
    
    // Conditions d'acceptation
    const acceptConditions = document.getElementById('accepte_conditions');
    if (acceptConditions && !acceptConditions.checked) {
        addFieldError(acceptConditions, 'Vous devez accepter les conditions d\'utilisation.');
        errors.push('accepte_conditions');
    }
    
    return errors.length === 0;
}

function addFieldError(element, message) {
    if (!element) return;
    
    element.classList.add('is-invalid');
    const errorId = element.id + '-error';
    const errorEl = document.getElementById(errorId);
    
    if (errorEl) {
        errorEl.textContent = message;
    } else {
        // Créer élément d'erreur si inexistant
        const errorDiv = document.createElement('small');
        errorDiv.id = errorId;
        errorDiv.className = 'form-text text-danger form-error';
        errorDiv.textContent = message;
        element.parentNode.insertBefore(errorDiv, element.nextSibling);
    }
}

function validateEmail() {
    const email = this.value;
    const isValid = CONFIG.emailRegex.test(email);
    this.classList.toggle('is-invalid', email && !isValid);
    
    const errorEl = document.getElementById('email-error');
    if (errorEl) {
        errorEl.textContent = email && !isValid ? 'Veuillez entrer un email valide.' : '';
    }
}

function validatePhone() {
    const phone = this.value.replace(/\s/g, '');
    const isValid = CONFIG.phoneRegex.test(phone);
    this.classList.toggle('is-invalid', phone && !isValid);
    
    const errorEl = document.getElementById('telephone-error');
    if (errorEl) {
        errorEl.textContent = phone && !isValid ? 'Numéro de téléphone haïtien invalide.' : '';
    }
}

function getFieldLabel(field) {
    const labels = {
        'prenom': 'Le prénom',
        'nom': 'Le nom de famille',
        'email': 'L\'email',
        'telephone': 'Le numéro de téléphone',
        'programme': 'Le programme',
        'lettre_motivation': 'La lettre de motivation'
    };
    return labels[field] || field;
}

function saveDraft() {
    const form = document.getElementById('admission-form');
    if (form) {
        const formData = new FormData(form);
        // Simulation de sauvegarde
        showFormMessage('Brouillon sauvegardé avec succès. Vous pouvez continuer plus tard.', 'success');
    }
}

function showFormMessage(message, type = 'info') {
    const messagesDiv = document.getElementById('form-messages');
    if (!messagesDiv) return;
    
    const alertClass = type === 'success' ? 'success' : 
                      type === 'error' ? 'danger' : 
                      type === 'warning' ? 'warning' : 'info';
    
    messagesDiv.innerHTML = `
        <div class="alert alert-${alertClass} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    messagesDiv.style.display = 'block';
    messagesDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// =====================================================
// CALCULATRICE DE COÛTS
// =====================================================
function initCostCalculator() {
    const costForm = document.getElementById('cost-form');
    if (costForm) {
        costForm.addEventListener('input', calculateCosts);
        calculateCosts(); // Calcul initial
    }
}

function calculateCosts() {
    const programCostEl = document.getElementById('program-cost');
    const scholarshipEl = document.getElementById('scholarship-type');
    
    if (!programCostEl || !scholarshipEl) return;
    
    const programCost = parseInt(programCostEl.value) || 0;
    const scholarshipPercent = parseInt(scholarshipEl.value) || 0;
    
    const annualTuition = programCost * 2; // 2 semestres
    const scholarshipReduction = (annualTuition * scholarshipPercent) / 100;
    const registrationFee = 2500;
    const materials = 3000;
    const totalCost = annualTuition - scholarshipReduction + registrationFee + materials;
    
    // Mise à jour de l'affichage
    document.getElementById('tuition-cost')?.setAttribute('data-cost', annualTuition);
    document.getElementById('tuition-cost')?.textContent = annualTuition.toLocaleString() + ' HTG';
    document.getElementById('scholarship-reduction')?.textContent = '-' + scholarshipReduction.toLocaleString() + ' HTG';
    document.getElementById('total-cost')?.textContent = totalCost.toLocaleString() + ' HTG';
}

// =====================================================
// COMPTEUR À REBours
// =====================================================
function initCountdown() {
    updateCountdown();
    setInterval(updateCountdown, CONFIG.countdownUpdateInterval);
}

function updateCountdown() {
    const deadline = new Date(CONFIG.countdownDeadline);
    const now = new Date();
    const timeDiff = deadline - now;
    
    if (timeDiff > 0) {
        const days = Math.floor(timeDiff / (1000 * 60 * 60 * 24));
        document.getElementById('days')?.textContent = days;
        document.getElementById('days-remaining')?.textContent = days + ' jours restants';
    } else {
        document.getElementById('days')?.textContent = '0';
        document.getElementById('days-remaining')?.textContent = '0 jours restants';
    }
}

// =====================================================
 // INTERACTIONS UTILISATEUR
// =====================================================

// Toggle FAQ
function toggleFAQ(index) {
    const content = document.getElementById(`faq-content-${index}`);
    const icon = document.getElementById(`faq-icon-${index}`);
    
    if (content) {
        content.classList.toggle('show');
    }
    
    if (icon) {
        icon.classList.toggle('bi-chevron-down');
        icon.classList.toggle('bi-chevron-up');
    }
}

// Toggle année de cours
function toggleYear(year) {
    const yearElement = document.querySelector(`[data-year="${year}"]`);
    if (!yearElement) return;
    
    const content = yearElement.querySelector('.year-content');
    const arrow = yearElement.querySelector('.year-arrow');
    
    if (content) {
        content.classList.toggle('show');
    }
    
    if (arrow) {
        arrow.classList.toggle('rotated');
    }
}

// Fonctions de recherche et recherche
function viewResearch(researchId) {
    console.log('Recherche:', researchId);
    // Navigation vers détail de recherche
}

function viewFacultyProfile(facultyId) {
    console.log('Profil enseignant:', facultyId);
    // Navigation vers profil enseignant
}

function viewStudentResearch(researchId) {
    console.log('Recherche étudiant:', researchId);
    // Affichage détail recherche étudiant
}

function viewAllStudentResearch() {
    console.log('Toutes les recherches étudiantes');
    // Navigation vers archive
}

function viewPartnerships(type) {
    console.log('Partenariats:', type);
    // Affichage détails partenariats
}

function exportResults() {
    console.log('Exportation résultats');
    // Génération et téléchargement fichier
}

function viewAbstract(paperId) {
    console.log('Abstract:', paperId);
    // Affichage abstract en modal
}

function downloadPDF(paperId) {
    console.log('Téléchargement PDF:', paperId);
    // Déclenchement téléchargement
}

function citePaper(paperId) {
    console.log('Citation:', paperId);
    // Affichage formats de citation
}

// Fonctions d'application et admission
function requestScholarship() {
    showFormMessage('Demande de bourse envoyée. Notre équipe vous contactera dans les 48 heures.', 'success');
}

function openVirtualTour(location) {
    // Simulation pour fonctionnalité future
    const message = `Visite virtuelle: ${location}. Bientôt disponible avec expérience 360° immersive.`;
    showFormMessage(message, 'info');
}

function contactAmbassador(name) {
    const message = `Contact avec ${name}. Chat avec ambassadeurs étudiants bientôt disponible.`;
    showFormMessage(message, 'info');
}

// =====================================================
// ÉVÉNEMENTS GLOBAUX
// =====================================================

// Écouteurs d'événements globaux
window.addEventListener('scroll', handleScrollAnimations);
window.addEventListener('load', function() {
    handleScrollAnimations();
    // Réinitialisation des animations au chargement
    setTimeout(initScrollAnimations, 100);
});

// Exportation des fonctions globales (si nécessaire pour d'autres scripts)
window.FASCH = {
    showDepartment,
    toggleFAQ,
    toggleYear,
    calculateCosts,
    performSearch,
    scrollToSection,
    requestScholarship,
    saveDraft
};

// Fin du script principal
console.log('FASCH JavaScript chargé avec succès - Version optimisée');