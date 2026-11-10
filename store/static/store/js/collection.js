
document.addEventListener("DOMContentLoaded", () => {

    // Respect reduced-motion preferences
    const prefersReducedMotion = window.matchMedia(
        "(prefers-reduced-motion: reduce)"
    ).matches;

    if (prefersReducedMotion) {
        return;
    }

    // Smooth scrolling
    document.documentElement.style.scrollBehavior = "smooth";


    // SCROLL REVEAL ANIMATIONS

    const revealElements = document.querySelectorAll(
        ".collection-hero-content, " +
        ".collection-toolbar, " +
        ".collection-product-card, " +
        ".collection-empty, " +
        ".collection-closing"
    );

    revealElements.forEach((element, index) => {
        element.classList.add("collection-reveal");

        if (element.classList.contains("collection-product-card")) {
            element.style.transitionDelay =
                `${(index % 3) * 120}ms`;
        }
    });

    const observer = new IntersectionObserver(
        (entries, observerInstance) => {

            entries.forEach(entry => {

                if (entry.isIntersecting) {
                    entry.target.classList.add("is-visible");

                    observerInstance.unobserve(entry.target);
                }

            });

        },
        {
            threshold: 0.12,
            rootMargin: "0px 0px -40px 0px"
        }
    );

    revealElements.forEach(element => {
        observer.observe(element);
    });


    // PRODUCT IMAGE HOVER INTERACTION

    const productImages = document.querySelectorAll(
        ".collection-product-image"
    );

    productImages.forEach(image => {

        image.addEventListener("mouseenter", () => {
            image.classList.add("is-hovered");
        });

        image.addEventListener("mouseleave", () => {
            image.classList.remove("is-hovered");
        });

    });

});
