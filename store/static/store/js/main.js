
/* =====================================================
   ATELIER — GLOBAL WEBSITE INTERACTIONS
   Navigation • Search • Header • Mobile Menu
===================================================== */

document.addEventListener("DOMContentLoaded", () => {

    console.log("ATELIER: Main JavaScript loaded.");

    const menuToggle = document.querySelector(".mobile-menu-toggle");
    const mobileNavigation = document.querySelector(".mobile-navigation");

    const searchToggle = document.querySelector(".search-toggle");
    const searchPanel = document.querySelector(".search-panel");

    const searchInput = searchPanel
        ? searchPanel.querySelector('input[type="search"]')
        : null;

    const header = document.querySelector(".site-header");


    /* 01 — MOBILE NAVIGATION
    -------------------------------------------------- */

    const closeMobileMenu = () => {

        if (!menuToggle || !mobileNavigation) return;

        mobileNavigation.classList.remove("is-open");
        menuToggle.classList.remove("is-active");
        menuToggle.setAttribute("aria-expanded", "false");

    };


    const openMobileMenu = () => {

        if (!menuToggle || !mobileNavigation) return;

        mobileNavigation.classList.add("is-open");
        menuToggle.classList.add("is-active");
        menuToggle.setAttribute("aria-expanded", "true");

    };


    if (menuToggle && mobileNavigation) {

        menuToggle.addEventListener("click", (event) => {

            event.stopPropagation();

            const isOpen = mobileNavigation.classList.contains("is-open");

            if (isOpen) {

                closeMobileMenu();

            } else {

                closeSearch();
                openMobileMenu();

            }

        });


        mobileNavigation.querySelectorAll("a").forEach((link) => {

            link.addEventListener("click", closeMobileMenu);

        });

    }


    /* 02 — SEARCH PANEL
    -------------------------------------------------- */

    const closeSearch = () => {

        if (!searchPanel || !searchToggle) return;

        searchPanel.classList.remove("is-open");
        searchPanel.setAttribute("aria-hidden", "true");
        searchToggle.setAttribute("aria-expanded", "false");

    };


    const openSearch = () => {

        if (!searchPanel || !searchToggle) return;

        closeMobileMenu();

        searchPanel.classList.add("is-open");
        searchPanel.setAttribute("aria-hidden", "false");
        searchToggle.setAttribute("aria-expanded", "true");

        if (searchInput) {
            searchInput.focus();
        }

    };


    if (searchToggle && searchPanel) {

        searchPanel.classList.remove("is-open");
        searchPanel.setAttribute("aria-hidden", "true");
        searchToggle.setAttribute("aria-expanded", "false");

        searchToggle.addEventListener("click", (event) => {

            event.preventDefault();
            event.stopPropagation();

            const isOpen = searchPanel.classList.contains("is-open");

            if (isOpen) {
                closeSearch();
            } else {
                openSearch();
            }

        });


        searchPanel.addEventListener("click", (event) => {

            event.stopPropagation();

        });

    }


    /* 03 — CLOSE PANELS WHEN CLICKING OUTSIDE
    -------------------------------------------------- */

    document.addEventListener("click", (event) => {

        if (
            searchPanel &&
            searchToggle &&
            !searchPanel.contains(event.target) &&
            !searchToggle.contains(event.target)
        ) {

            closeSearch();

        }


        if (
            mobileNavigation &&
            menuToggle &&
            !mobileNavigation.contains(event.target) &&
            !menuToggle.contains(event.target)
        ) {

            closeMobileMenu();

        }

    });


    /* 04 — CLOSE PANELS WITH ESCAPE
    -------------------------------------------------- */

    document.addEventListener("keydown", (event) => {

        if (event.key === "Escape") {

            closeSearch();
            closeMobileMenu();

        }

    });


    /* 05 — STICKY HEADER SCROLL EFFECT
    -------------------------------------------------- */

    if (header) {

        let ticking = false;

        window.addEventListener("scroll", () => {

            if (!ticking) {

                window.requestAnimationFrame(() => {

                    header.classList.toggle(
                        "is-scrolled",
                        window.scrollY > 40
                    );

                    ticking = false;

                });

                ticking = true;

            }

        }, { passive: true });

    }


    /* 06 — CURRENT YEAR
    -------------------------------------------------- */

    document.querySelectorAll("[data-current-year]").forEach((element) => {

        element.textContent = new Date().getFullYear();

    });


    console.log("ATELIER: All website interactions initialized.");

});
