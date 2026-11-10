
/* =====================================================
   ATELIER — HOMEPAGE INTERACTIONS
   Lightweight • Smooth • Responsive
===================================================== */

document.addEventListener("DOMContentLoaded", () => {

    /* 01 — SCROLL REVEAL
    -------------------------------------------------- */

    const revealElements = document.querySelectorAll(
        ".section-heading, .collection-card, .arrival-card, .brand-statement, .final-campaign-content"
    );

    if ("IntersectionObserver" in window) {

        const revealObserver = new IntersectionObserver(
            (entries, observer) => {

                entries.forEach((entry) => {

                    if (entry.isIntersecting) {
                        entry.target.classList.add("is-visible");
                        observer.unobserve(entry.target);
                    }

                });

            },
            {
                threshold: 0.12,
                rootMargin: "0px 0px -40px 0px"
            }
        );

        revealElements.forEach((element) => {
            element.classList.add("reveal-element");
            revealObserver.observe(element);
        });

    } else {

        revealElements.forEach((element) => {
            element.classList.add("is-visible");
        });

    }


    /* 02 — SMOOTH SECTION NAVIGATION
    -------------------------------------------------- */

    const sectionLinks = document.querySelectorAll(
        'a[href^="#"]'
    );

    sectionLinks.forEach((link) => {

        link.addEventListener("click", (event) => {

            const targetId = link.getAttribute("href");

            if (!targetId || targetId === "#") return;

            const target = document.querySelector(targetId);

            if (target) {

                event.preventDefault();

                target.scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                });

            }

        });

    });


    /* 03 — IMAGE HOVER INTERACTIONS
    -------------------------------------------------- */

    const imageCards = document.querySelectorAll(
        ".collection-card, .arrival-card"
    );

    imageCards.forEach((card) => {

        card.addEventListener("mouseenter", () => {
            card.classList.add("image-hovered");
        });

        card.addEventListener("mouseleave", () => {
            card.classList.remove("image-hovered");
        });

    });


    /* 04 — MARQUEE PAUSE ON HOVER
    -------------------------------------------------- */

    const marquee = document.querySelector(".editorial-marquee");
    const marqueeTrack = document.querySelector(".marquee-track");

    if (marquee && marqueeTrack) {

        marquee.addEventListener("mouseenter", () => {
            marqueeTrack.style.animationPlayState = "paused";
        });

        marquee.addEventListener("mouseleave", () => {
            marqueeTrack.style.animationPlayState = "running";
        });

    }


    /* 05 — HERO IMAGE LOAD EFFECT
    -------------------------------------------------- */

    const heroImage = document.querySelector(".hero-image");

    if (heroImage) {

        if (heroImage.complete) {
            heroImage.classList.add("image-loaded");
        } else {

            heroImage.addEventListener("load", () => {
                heroImage.classList.add("image-loaded");
            }, { once: true });

        }

    }


    /* 06 — FOOTER YEAR
    -------------------------------------------------- */

    const yearElement = document.querySelector("[data-current-year]");

    if (yearElement) {
        yearElement.textContent = new Date().getFullYear();
    }

});
