/* VEXORA UI helpers — dependency free. */
(() => {
    "use strict";

    window.VexoraUI = {
        icon(name, className = "vx-icon") {
            const img = document.createElement("img");
            img.className = className;
            img.alt = "";
            img.setAttribute("aria-hidden", "true");
            img.src = `${window.VEXORA_STATIC_PATH || "/static/"}icons/${encodeURIComponent(name)}.svg`;
            return img;
        },

        toast(message, type = "info") {
            const host = document.querySelector("[data-toast-host]") || (() => {
                const el = document.createElement("div");
                el.dataset.toastHost = "1";
                el.style.cssText = "position:fixed;inset:auto 20px 20px auto;z-index:9999;display:grid;gap:8px";
                document.body.appendChild(el);
                return el;
            })();

            const toast = document.createElement("div");
            toast.setAttribute("role", "status");
            toast.dataset.type = type;
            toast.textContent = message;
            toast.style.cssText = [
                "padding:11px 15px",
                "border:1px solid rgba(255,255,255,.12)",
                "border-radius:12px",
                "background:rgba(20,20,28,.94)",
                "color:#fff",
                "box-shadow:0 12px 30px rgba(0,0,0,.25)"
            ].join(";");
            host.appendChild(toast);
            setTimeout(() => toast.remove(), 3200);
        }
    };
})();
