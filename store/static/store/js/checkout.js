/* ATELIER — CHECKOUT DELIVERY CALCULATOR */

document.addEventListener("DOMContentLoaded", () => {

    const deliveryZone = document.getElementById("delivery_zone");
    const deliveryFeeDisplay = document.getElementById("delivery-fee");
    const orderTotalDisplay = document.getElementById("order-total");

    if (!deliveryZone || !deliveryFeeDisplay || !orderTotalDisplay) {
        return;
    }

    const subtotal = Number(orderTotalDisplay.dataset.subtotal);

    function updateOrderTotal() {

        const selectedOption = deliveryZone.options[deliveryZone.selectedIndex];

        const deliveryFee = selectedOption.dataset.fee
            ? Number(selectedOption.dataset.fee)
            : 0;

        const total = subtotal + deliveryFee;

        deliveryFeeDisplay.textContent =
            `KSh ${deliveryFee.toLocaleString("en-KE", {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            })}`;

        orderTotalDisplay.textContent =
            `KSh ${total.toLocaleString("en-KE", {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            })}`;
    }

    deliveryZone.addEventListener("change", updateOrderTotal);

    updateOrderTotal();

});