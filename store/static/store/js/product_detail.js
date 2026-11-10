/* =========================================
   ATELIER — PRODUCT IMAGE GALLERY
========================================= */

document.addEventListener("DOMContentLoaded", () => {

    const mainImage = document.getElementById("mainProductImage");
    const thumbnails = document.querySelectorAll(".product-thumbnail");

    if (!mainImage || !thumbnails.length) return;

    thumbnails.forEach((thumbnail) => {

        thumbnail.addEventListener("click", () => {

            // Change the main image
            mainImage.src = thumbnail.src;

            // Update active thumbnail
            thumbnails.forEach((image) => {
                image.classList.remove("active");
            });

            thumbnail.classList.add("active");

        });

    });

});