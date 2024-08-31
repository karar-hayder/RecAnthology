document.addEventListener('DOMContentLoaded', () => {
    const prevButtons = document.querySelectorAll('.carousel-control.prev');
    const nextButtons = document.querySelectorAll('.carousel-control.next');

    prevButtons.forEach(button => {
        button.addEventListener('click', () => {
            const carousel = button.nextElementSibling;
            if (carousel && carousel.classList.contains('carousel')) {
                carousel.scrollBy({ left: -200, behavior: 'smooth' });
            }
        });
    });

    nextButtons.forEach(button => {
        button.addEventListener('click', () => {
            const carousel = button.previousElementSibling;
            if (carousel && carousel.classList.contains('carousel')) {
                carousel.scrollBy({ left: 200, behavior: 'smooth' });
            }
        });
    });
});