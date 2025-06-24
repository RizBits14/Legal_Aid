class PracticeAreasManager {
    constructor() {
        this.currentArea = null;
        this.animationDelay = 100;
        this.isLoading = false;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeAnimations();
        this.loadPracticeAreaStats();
    }

    setupEventListeners() {
        // Practice area card clicks
        document.querySelectorAll('.area-card').forEach(card => {
            card.addEventListener('click', (e) => this.handleCardClick(e));
            card.addEventListener('mouseenter', (e) => this.handleCardHover(e));
            card.addEventListener('mouseleave', (e) => this.handleCardLeave(e));
        });

        // Mobile menu toggle
        const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
        const navLinks = document.querySelector('.nav-links');
        
        if (mobileMenuBtn && navLinks) {
            mobileMenuBtn.addEventListener('click', () => {
                navLinks.classList.toggle('active');
                const icon = mobileMenuBtn.querySelector('i');
                icon.classList.toggle('fa-bars');
                icon.classList.toggle('fa-times');
            });
        }

        // Search functionality
        this.setupSearch();
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => this.handleKeyboardNavigation(e));
    }

    handleCardClick(e) {
        const card = e.currentTarget;
        const area = card.getAttribute('data-area');
        
        if (this.currentArea === area) return;

        // Add loading state
        this.setLoadingState(true);
        
        // Remove active from all cards
        document.querySelectorAll('.area-card').forEach(c => {
            c.classList.remove('active');
            c.style.transform = '';
        });

        // Hide all details with animation
        document.querySelectorAll('.area-detail').forEach(detail => {
            detail.style.opacity = '0';
            detail.style.transform = 'translateY(20px)';
            setTimeout(() => {
                detail.style.display = 'none';
                detail.classList.remove('fade-in');
            }, 300);
        });

        // Activate clicked card
        card.classList.add('active');
        this.currentArea = area;

        // Show detail after a delay
        setTimeout(() => {
            this.showAreaDetail(area);
            this.setLoadingState(false);
        }, 400);

        // Track analytics
        this.trackAreaClick(area);

        // Smooth scroll to details
        setTimeout(() => {
            const detailElement = document.getElementById(`detail-${area}`);
            if (detailElement) {
                detailElement.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'nearest' 
                });
            }
        }, 600);
    }

    handleCardHover(e) {
        const card = e.currentTarget;
        if (!card.classList.contains('active')) {
            card.style.transform = 'translateY(-5px) scale(1.02)';
            
            // Add subtle glow effect
            card.style.boxShadow = '0 15px 35px rgba(106, 156, 137, 0.2)';
        }
    }

    handleCardLeave(e) {
        const card = e.currentTarget;
        if (!card.classList.contains('active')) {
            card.style.transform = '';
            card.style.boxShadow = '';
        }
    }

    showAreaDetail(area) {
        const detail = document.getElementById(`detail-${area}`);
        if (!detail) return;

        detail.style.display = 'block';
        detail.style.opacity = '0';
        detail.style.transform = 'translateY(20px)';

        // Trigger reflow
        detail.offsetHeight;

        // Animate in
        detail.style.transition = 'all 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
        detail.style.opacity = '1';
        detail.style.transform = 'translateY(0)';
        detail.classList.add('fade-in');

        // Load dynamic content if needed
        this.loadDynamicContent(area, detail);
    }

    initializeAnimations() {
        // Animate title and description
        const animatedTitle = document.querySelector('.animated-title');
        const animatedDesc = document.querySelector('.animated-desc');
        
        if (animatedTitle && animatedDesc) {
            setTimeout(() => {
                animatedTitle.style.opacity = '1';
                animatedTitle.style.transform = 'translateY(0)';
            }, 300);
            
            setTimeout(() => {
                animatedDesc.style.opacity = '1';
                animatedDesc.style.transform = 'translateY(0)';
            }, 600);
        }

        // Staggered animation for cards
        const areaCards = document.querySelectorAll('.area-card');
        areaCards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(30px)';
            
            setTimeout(() => {
                card.style.transition = 'all 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, 900 + (index * this.animationDelay));
        });

        // Show first card as active by default
        setTimeout(() => {
            if (areaCards.length > 0) {
                const firstCard = areaCards[0];
                firstCard.classList.add('active');
                this.currentArea = firstCard.getAttribute('data-area');
                this.showAreaDetail(this.currentArea);
            }
        }, 1500);

        // Intersection Observer for scroll animations
        this.setupScrollAnimations();
    }

    setupScrollAnimations() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                    
                    // Add additional effects based on element type
                    if (entry.target.classList.contains('cta-section')) {
                        this.animateCTA(entry.target);
                    }
                }
            });
        }, observerOptions);

        // Observe elements
        document.querySelectorAll('.area-detail, .cta-section, .footer').forEach(el => {
            observer.observe(el);
        });
    }

    animateCTA(ctaElement) {
        const buttons = ctaElement.querySelectorAll('.cta-btn');
        buttons.forEach((btn, index) => {
            setTimeout(() => {
                btn.style.transform = 'translateY(0) scale(1)';
                btn.style.opacity = '1';
            }, index * 200);
        });
    }

    loadPracticeAreaStats() {
        // Load real-time statistics from API
        fetch('/api/practice-areas/stats')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.updateStats(data.stats);
                }
            })
            .catch(error => {
                console.log('Stats loading failed:', error);
                // Use fallback stats
            });
    }

    updateStats(stats) {
        Object.keys(stats).forEach(areaKey => {
            const areaStat = stats[areaKey];
            const detailElement = document.getElementById(`detail-${areaKey}`);
            
            if (detailElement) {
                // Update lawyer count
                const statsDiv = detailElement.querySelector('.stats');
                if (statsDiv) {
                    const countElement = statsDiv.querySelector('.stat-item strong');
                    if (countElement) {
                        this.animateNumber(countElement, 0, areaStat.lawyer_count, 1000);
                    }
                }
            }
        });
    }

    animateNumber(element, start, end, duration) {
        const startTime = performance.now();
        
        const updateNumber = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            const current = Math.floor(start + (end - start) * progress);
            element.textContent = current.toString();
            
            if (progress < 1) {
                requestAnimationFrame(updateNumber);
            }
        };
        
        requestAnimationFrame(updateNumber);
    }

    loadDynamicContent(area, detailElement) {
        // Load additional content like recent cases, testimonials, etc.
        this.loadLawyerPreviews(area, detailElement);
    }

    loadLawyerPreviews(area, detailElement) {
        fetch(`/api/practice-areas/${area}/lawyers`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.lawyers.length > 0) {
                    this.addLawyerPreviews(detailElement, data.lawyers.slice(0, 3));
                }
            })
            .catch(error => {
                console.log('Lawyer preview loading failed:', error);
            });
    }

    addLawyerPreviews(detailElement, lawyers) {
        const existingPreviews = detailElement.querySelector('.lawyer-previews');
        if (existingPreviews) return; // Already loaded

        const previewsContainer = document.createElement('div');
        previewsContainer.className = 'lawyer-previews';
        previewsContainer.innerHTML = `
            <h4 style="color: var(--navbar-color); margin: 20px 0 15px 0;">Top Lawyers in this area:</h4>
            <div style="display: flex; gap: 15px; flex-wrap: wrap;">
                ${lawyers.map(lawyer => `
                    <div style="background: var(--ui-light); padding: 15px; border-radius: 8px; flex: 1; min-width: 200px;">
                        <div style="font-weight: 600; color: var(--navbar-color); margin-bottom: 5px;">
                            ${lawyer.FirstName} ${lawyer.LastName}
                        </div>
                        <div style="font-size: 0.9rem; color: var(--text-color); margin-bottom: 8px;">
                            ${lawyer.YearsOfExperience || 0} years • Rating: ${lawyer.Rating || 4.5}/5
                        </div>
                        <a href="/lawyer/${lawyer.id}" style="color: var(--accent-color); text-decoration: none; font-size: 0.9rem;">
                            View Profile →
                        </a>
                    </div>
                `).join('')}
            </div>
        `;

        detailElement.appendChild(previewsContainer);

        // Animate in
        setTimeout(() => {
            previewsContainer.style.opacity = '1';
            previewsContainer.style.transform = 'translateY(0)';
        }, 100);
    }

    setupSearch() {
        // Add search functionality for practice areas
        const searchInput = document.getElementById('practice-area-search');
        if (!searchInput) return;

        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.filterPracticeAreas(e.target.value);
            }, 300);
        });
    }

    filterPracticeAreas(searchTerm) {
        const cards = document.querySelectorAll('.area-card');
        const term = searchTerm.toLowerCase();

        cards.forEach(card => {
            const cardText = card.textContent.toLowerCase();
            const isVisible = cardText.includes(term) || term === '';
            
            card.style.display = isVisible ? 'flex' : 'none';
            
            if (isVisible) {
                card.style.animation = 'fadeInUp 0.4s ease-out';
            }
        });
    }

    handleKeyboardNavigation(e) {
        const cards = Array.from(document.querySelectorAll('.area-card:not([style*="display: none"])'));
        const currentIndex = cards.findIndex(card => card.classList.contains('active'));

        let newIndex = currentIndex;

        switch(e.key) {
            case 'ArrowRight':
            case 'ArrowDown':
                e.preventDefault();
                newIndex = (currentIndex + 1) % cards.length;
                break;
            case 'ArrowLeft':
            case 'ArrowUp':
                e.preventDefault();
                newIndex = (currentIndex - 1 + cards.length) % cards.length;
                break;
            case 'Enter':
                if (currentIndex >= 0) {
                    e.preventDefault();
                    cards[currentIndex].click();
                }
                return;
            default:
                return;
        }

        if (newIndex !== currentIndex && cards[newIndex]) {
            cards[newIndex].click();
        }
    }

    setLoadingState(isLoading) {
        this.isLoading = isLoading;
        const container = document.querySelector('.container');
        
        if (isLoading) {
            container.style.opacity = '0.7';
            container.style.pointerEvents = 'none';
        } else {
            container.style.opacity = '1';
            container.style.pointerEvents = 'auto';
        }
    }

    trackAreaClick(area) {
        // Analytics tracking
        if (typeof gtag !== 'undefined') {
            gtag('event', 'practice_area_click', {
                'practice_area': area,
                'page_title': 'Practice Areas'
            });
        }
    }
}

// Utility functions for enhanced interactions
class PracticeAreaUtils {
    static createRippleEffect(element, e) {
        const ripple = document.createElement('div');
        const rect = element.getBoundingClientRect();
        const size = 60;
        const x = e.clientX - rect.left - size / 2;
        const y = e.clientY - rect.top - size / 2;
        
        ripple.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.6);
            transform: scale(0);
            animation: ripple 0.6s linear;
            left: ${x}px;
            top: ${y}px;
            pointer-events: none;
        `;
        
        element.style.position = 'relative';
        element.style.overflow = 'hidden';
        element.appendChild(ripple);
        
        setTimeout(() => {
            ripple.remove();
        }, 600);
    }

    static addParallaxEffect() {
        window.addEventListener('scroll', () => {
            const scrolled = window.pageYOffset;
            const parallaxElements = document.querySelectorAll('.hero-section');
            
            parallaxElements.forEach(el => {
                const speed = 0.5;
                el.style.transform = `translateY(${scrolled * speed}px)`;
            });
        });
    }

    static addHoverSound() {
        const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmYdBDuQ1PO7aS4GM...');
        
        document.querySelectorAll('.area-card').forEach(card => {
            card.addEventListener('mouseenter', () => {
                if (audio) {
                    audio.currentTime = 0;
                    audio.volume = 0.1;
                    audio.play().catch(() => {}); // Ignore autoplay restrictions
                }
            });
        });
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize main functionality
    new PracticeAreasManager();
    
    // Add utility enhancements
    PracticeAreaUtils.addParallaxEffect();
    
    // Add ripple effect to buttons
    document.querySelectorAll('.action-btn, .cta-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            PracticeAreaUtils.createRippleEffect(this, e);
        });
    });
});

// CSS animation keyframes (add to CSS file)
const additionalCSS = `
@keyframes ripple {
    to {
        transform: scale(4);
        opacity: 0;
    }
}

@keyframes slideInLeft {
    from {
        opacity: 0;
        transform: translateX(-30px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

@keyframes slideInRight {
    from {
        opacity: 0;
        transform: translateX(30px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

.lawyer-previews {
    opacity: 0;
    transform: translateY(20px);
    transition: all 0.6s ease;
}
`;

// Add CSS to document
if (typeof document !== 'undefined') {
    const style = document.createElement('style');
    style.textContent = additionalCSS;
    document.head.appendChild(style);
}