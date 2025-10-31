// =====================================================
// FASCH - Carrousel Hero - Version Corrigée
// =====================================================

console.log('Chargement de caroussel.js');
console.log('StaticBase disponible:', typeof staticBase !== 'undefined' ? staticBase : 'NON DÉFINI');

// Configuration globale
const CONFIG = {
    autoSlideInterval: 5000,
    animationThreshold: 150
};

// Variables globales
let currentSlide = 0;

// =====================================================
// HERO CAROUSEL
// =====================================================
const heroSlides = [
    {
        image: (typeof staticBase !== 'undefined' ? staticBase : '/static/') + "images/faculte.png",
        title: "50 Ans d'Excellence en Sciences Humaines",
        subtitle: "Formant les leaders de demain en psychologie, sociologie, travail social et communication depuis 1975"
    },
    {
        image: (typeof staticBase !== 'undefined' ? staticBase : '/static/') + "images/fasch1.jpg",
        title: "Étude approfondie des processus cognitifs et de leurs applications cliniques",
        subtitle: "Rejoignez FASCH et façonnez l'avenir des sciences humaines en Haïti. Découvrez nos programmes d'excellence et commencez votre candidature dès aujourd'hui."
    },
    {
        image: (typeof staticBase !== 'undefined' ? staticBase : '/static/') + "images/fasch2.jpg",
        title: "Recherche de Pointe en Sciences Sociales",
        subtitle: "Nos professeurs et étudiants contribuent activement à la compréhension de la société haïtienne contemporaine"
    },
    {
        image: (typeof staticBase !== 'undefined' ? staticBase : '/static/') + "images/fasch3.jpg",
        title: "Innovation Pédagogique et Impact Social",
        subtitle: "Des programmes adaptés aux défis modernes d'Haïti avec une approche pratique et communautaire"
    }
];

console.log('Slides configurées:', heroSlides.length);

// =====================================================
// INITIALISATION
// =====================================================
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM chargé, initialisation du carrousel');
    initHeroCarousel();
});

function initHeroCarousel() {
    console.log('Initialisation du carrousel hero');
    
    // Vérifier que les éléments existent
    const heroContent = document.getElementById('hero-content');
    const heroBg = document.getElementById('hero-bg');
    const heroDots = document.querySelectorAll('.hero-dot');
    
    console.log('Éléments trouvés:', {
        heroContent: !!heroContent,
        heroBg: !!heroBg,
        heroDots: heroDots.length
    });
    
    if (!heroContent || !heroBg || heroDots.length === 0) {
        console.error('Éléments du carrousel manquants');
        return;
    }
    
    updateHeroDots();
    startAutoSlide();
}

function changeHeroSlide(index) {
    console.log('Changement de slide vers:', index);
    currentSlide = index;
    updateHeroContent();
    updateHeroDots();
}

function updateHeroContent() {
    const slide = heroSlides[currentSlide];
    const heroContent = document.getElementById('hero-content');
    const heroBg = document.getElementById('hero-bg');
    
    if (!heroContent || !heroBg) {
        console.error('Éléments du carrousel manquants lors de la mise à jour');
        return;
    }
    
    console.log('Mise à jour du contenu vers slide', currentSlide);
    
    // Fade out
    heroContent.style.opacity = '0';
    heroContent.style.transition = 'opacity 0.3s ease';
    
    setTimeout(() => {
        // Mise à jour du contenu
        heroContent.innerHTML = `
            <h1 class="display-3 fw-bold font-playfair mb-4 text-balance">${slide.title}</h1>
            <p class="lead fs-3 mb-5 opacity-90">${slide.subtitle}</p>
            <div class="d-flex flex-column flex-sm-row gap-3 justify-content-center">
                <a href="/accounts/login/" class="btn btn-secondary-custom btn-lg px-5 py-3">Commencer Votre Parcours</a>
                <a href="/departments/" class="border-2 border-white text-white px-5 py-3 rounded fw-semibold text-decoration-none transition-all">
                    Explorer Nos Programmes
                </a>
            </div>
        `;
        
        // Mise à jour de l'image de fond
        heroBg.src = slide.image;
        console.log('Image changée vers:', slide.image);
        
        // Fade in
        heroContent.style.opacity = '1';
    }, 300);
}

function updateHeroDots() {
    const dots = document.querySelectorAll('.hero-dot');
    console.log('Mise à jour des dots, currentSlide:', currentSlide);
    
    dots.forEach((dot, index) => {
        if (index === currentSlide) {
            dot.style.opacity = '1';
            dot.style.transform = 'scale(1.2)';
        } else {
            dot.style.opacity = '0.5';
            dot.style.transform = 'scale(1)';
        }
    });
}

function startAutoSlide() {
    console.log('Démarrage de l\'auto-slide avec intervalle:', CONFIG.autoSlideInterval);
    
    setInterval(() => {
        currentSlide = (currentSlide + 1) % heroSlides.length;
        console.log('Auto-slide vers:', currentSlide);
        updateHeroContent();
        updateHeroDots();
    }, CONFIG.autoSlideInterval);
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
}

// Initialiser les animations au chargement
document.addEventListener('DOMContentLoaded', function() {
    initScrollAnimations();
});

// =====================================================
// AUTRES FONCTIONS UTILES
// =====================================================

// Afficher la date du jour
document.addEventListener('DOMContentLoaded', function() {
    const dateElement = document.getElementById('current-date');
    if (dateElement) {
        const options = {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        };
        const today = new Date();
        dateElement.textContent = today.toLocaleDateString('fr-FR', options);
    }
    
    // Animation pour les articles
    const articles = document.querySelectorAll('.main-article');
    articles.forEach((article, index) => {
        setTimeout(() => {
            article.style.opacity = '1';
        }, 200 * index);
    });
});

// Fermer l'offcanvas si la fenêtre devient desktop
window.addEventListener('resize', () => {
    const offcanvasEl = document.getElementById('offcanvasMenu');
    if (!offcanvasEl) return;
    
    const bsOffcanvas = bootstrap.Offcanvas.getInstance(offcanvasEl);
    if (window.innerWidth >= 992 && bsOffcanvas) {
        bsOffcanvas.hide();
    }
});

console.log('Carrousel.js chargé avec succès');