document.addEventListener('DOMContentLoaded', () => {
    const filterButtons = document.querySelectorAll('.filter-btn');
    const cards = document.querySelectorAll('.destination-card');

    filterButtons.forEach((button) => {
        button.addEventListener('click', () => {
            const selected = button.dataset.filter;

            filterButtons.forEach((btn) => btn.classList.toggle('active', btn === button));

            cards.forEach((card) => {
                const match = selected === 'all' || card.dataset.category === selected;
                card.style.display = match ? 'block' : 'none';
            });
        });
    });

    const revealItems = document.querySelectorAll('.reveal');

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.12 });

    revealItems.forEach((item) => observer.observe(item));
});
