(function () {
    "use strict";

    function all(selector) {
        return Array.prototype.slice.call(
            document.querySelectorAll(selector)
        );
    }

    function setupConfirmations() {
        all("[data-confirm]").forEach(function (node) {
            node.addEventListener("click", function (event) {
                var message = node.getAttribute("data-confirm");
                if (message && !window.confirm(message)) {
                    event.preventDefault();
                }
            });
        });
    }

    function setupSearch() {
        all("[data-table-search]").forEach(function (input) {
            var table = document.querySelector(
                input.getAttribute("data-table-search")
            );
            if (!table) return;

            input.addEventListener("input", function () {
                var needle = input.value.trim().toLowerCase();
                all("tbody tr", table).forEach(function (row) {
                    row.hidden = Boolean(
                        needle &&
                        row.textContent.toLowerCase().indexOf(needle) === -1
                    );
                });
            });
        });
    }

    function setupCopy() {
        all("[data-copy]").forEach(function (button) {
            button.addEventListener("click", function () {
                if (!navigator.clipboard) return;
                navigator.clipboard.writeText(
                    button.getAttribute("data-copy")
                ).then(function () {
                    var original = button.textContent;
                    button.textContent = "کپی شد";
                    window.setTimeout(function () {
                        button.textContent = original;
                    }, 1200);
                });
            });
        });
    }

    document.addEventListener("DOMContentLoaded", function () {
        setupConfirmations();
        setupSearch();
        setupCopy();
    });
}());
