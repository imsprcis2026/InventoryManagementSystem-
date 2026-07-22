// ===============================
// Remaining Amount Calculator
// ===============================

function calculateRemaining() {

    let total = parseFloat(document.getElementById("total_price").value) || 0;

    let paid = parseFloat(document.getElementById("paid").value) || 0;

    let remaining = total - paid;

    if (remaining < 0) {

        remaining = 0;

    }

    let box = document.getElementById("remaining");

    if (box != null) {

        box.value = remaining.toFixed(2);

    }

}


// ===============================
// Delete Confirmation
// ===============================

function confirmDelete(message = "Are you sure you want to delete this record?") {

    return confirm(message);

}


// ===============================
// Auto Focus Search Box
// ===============================

window.onload = function () {

    let search = document.getElementById("search");

    if (search) {

        search.focus();

    }

}