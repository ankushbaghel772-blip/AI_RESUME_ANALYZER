/**
 * Main JavaScript entrypoint for AI Resume Analysis System.
 * Handles auto-dismiss alerts, animated statistic counters,
 * and subtle 3D card tilt micro-interactions.
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Auto-dismiss alert notifications after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (window.bootstrap && bootstrap.Alert) {
                const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                if (bsAlert) {
                    bsAlert.close();
                }
            }
        }, 5000);
    });

    // 2. Animate numbers on statistics cards
    const statCounters = document.querySelectorAll('.stat-counter');
    statCounters.forEach(counter => {
        const target = parseFloat(counter.getAttribute('data-target') || '0');
        if (isNaN(target) || target === 0) return;

        const isDecimal = target % 1 !== 0;
        let current = 0;
        const duration = 1000;
        const stepTime = 20;
        const totalSteps = duration / stepTime;
        const increment = target / totalSteps;

        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                counter.innerText = isDecimal ? target.toFixed(1) : Math.round(target);
                clearInterval(timer);
            } else {
                counter.innerText = isDecimal ? current.toFixed(1) : Math.round(current);
            }
        }, stepTime);
    });

    // 3. Subtle 3D Tilt Micro-Interaction for Desktop
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (!prefersReducedMotion && window.innerWidth >= 992) {
        const tiltCards = document.querySelectorAll('.card-lift, .stat-card');
        tiltCards.forEach(card => {
            card.addEventListener('mousemove', (e) => {
                const rect = card.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                const centerX = rect.width / 2;
                const centerY = rect.height / 2;
                
                const rotateX = ((y - centerY) / centerY) * -3; // Max 3 deg tilt
                const rotateY = ((x - centerX) / centerX) * 3;

                card.style.transform = `perspective(1000px) rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg) translateY(-4px)`;
            });

            card.addEventListener('mouseleave', () => {
                card.style.transform = '';
            });
        });
    }
});
