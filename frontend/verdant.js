document.addEventListener("DOMContentLoaded", () => {
    initAuthCheck();
    initDarkMode();
    initMobileNav();
    initActiveLink();
    initBackToTop();
    initButtonRipples();
    initNavSearch();
});

async function initAuthCheck() {
    const token = localStorage.getItem("verdant_token");
    const path = window.location.pathname.toLowerCase();
    const isAuthPage = path.includes("login.html") || path.includes("register.html");

    // Redirect to login if token is missing on non-auth pages
    if (!token) {
        if (!isAuthPage) {
            window.location.href = "login.html";
        }
        return;
    }

    // Token exists, verify/fetch profile
    try {
        
        const res = await fetch("https://verdant-77nb.onrender.com/profile", {

            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        if (!res.ok) {
            throw new Error("Invalid token session");
        }

        const data = await res.json();
        if (data.success && data.user) {
            // Update profile images in navbars dynamically
            const navAvatar = document.querySelector("nav .right img");
            if (navAvatar) {
                if (data.user.photo_url) {
                    navAvatar.src = data.user.photo_url;
                }
                navAvatar.style.cursor = "pointer";
                navAvatar.title = "View Profile";
                navAvatar.addEventListener("click", () => {
                    window.location.href = "profile.html";
                });
            }

            // Redirect authenticated users away from login/register to dashboard
            if (isAuthPage) {
                window.location.href = "index.html";
            }
        }
    } catch (err) {
        console.error(err);
        localStorage.removeItem("verdant_token");
        if (!isAuthPage) {
            window.location.href = "login.html";
        }
    }

    // Dynamically insert Logout option in Sidebar
    const sidebarUl = document.querySelector(".sidebar ul");
    if (sidebarUl && !document.getElementById("sidebarLogout")) {
        const logoutLi = document.createElement("li");
        logoutLi.id = "sidebarLogout";
        logoutLi.innerHTML = '<a href="#" id="logoutLink"><i class="fa-solid fa-right-from-bracket"></i> Logout</a>';
        sidebarUl.appendChild(logoutLi);

        document.getElementById("logoutLink").addEventListener("click", (e) => {
            e.preventDefault();
            localStorage.removeItem("verdant_token");
            showToast("Logged out successfully!", "info");
            setTimeout(() => {
                window.location.href = "login.html";
            }, 800);
        });
    }
}


// ==========================================
// 1. PREMIUM DARK MODE SYSTEM
// ==========================================
function initDarkMode() {
    const themeBtn = document.getElementById("themeBtn");
    
    // Check saved preference or fallback to system preference
    const savedTheme = localStorage.getItem("theme");
    const systemPrefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    
    if (savedTheme === "dark" || (!savedTheme && systemPrefersDark)) {
        document.body.classList.add("dark");
        updateThemeIcon(true);
    } else {
        document.body.classList.remove("dark");
        updateThemeIcon(false);
    }

    if (themeBtn) {
        themeBtn.addEventListener("click", () => {
            document.body.classList.toggle("dark");
            const isDark = document.body.classList.contains("dark");
            localStorage.setItem("theme", isDark ? "dark" : "light");
            updateThemeIcon(isDark);
            showToast(isDark ? "Dark theme enabled 🌙" : "Light theme enabled ☀️", "info");
        });
    }
}

function updateThemeIcon(isDark) {
    const themeBtn = document.getElementById("themeBtn");
    if (!themeBtn) return;
    const icon = themeBtn.querySelector("i");
    if (icon) {
        icon.className = isDark ? "fa-solid fa-sun" : "fa-solid fa-moon";
    }
}

// ==========================================
// 2. MOBILE NAVIGATION HAMBURGER SYSTEM
// ==========================================
function initMobileNav() {
    const nav = document.querySelector("nav");
    const sidebar = document.querySelector(".sidebar");
    if (!nav || !sidebar) return;

    // Inject hamburger button if not present
    if (!document.getElementById("navHamburger")) {
        const hamburgerBtn = document.createElement("div");
        hamburgerBtn.id = "navHamburger";
        hamburgerBtn.className = "hamburger";
        hamburgerBtn.innerHTML = '<i class="fa-solid fa-bars"></i>';
        nav.insertBefore(hamburgerBtn, nav.firstChild);
    }

    // Inject sidebar overlay backdrop if not present
    if (!document.getElementById("sidebarOverlay")) {
        const overlay = document.createElement("div");
        overlay.id = "sidebarOverlay";
        overlay.className = "sidebar-overlay";
        document.body.appendChild(overlay);
    }

    const hamburgerBtn = document.getElementById("navHamburger");
    const overlay = document.getElementById("sidebarOverlay");

    function openSidebar() {
        sidebar.classList.add("open");
        overlay.classList.add("show");
        hamburgerBtn.querySelector("i").className = "fa-solid fa-xmark";
        document.body.style.overflow = "hidden";
    }

    function closeSidebar() {
        sidebar.classList.remove("open");
        overlay.classList.remove("show");
        hamburgerBtn.querySelector("i").className = "fa-solid fa-bars";
        document.body.style.overflow = "";
    }

    hamburgerBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        sidebar.classList.contains("open") ? closeSidebar() : openSidebar();
    });

    overlay.addEventListener("click", closeSidebar);

    // Close on sidebar link click (navigate away)
    sidebar.querySelectorAll("a").forEach(link => {
        link.addEventListener("click", closeSidebar);
    });
}


// ==========================================
// 3. AUTO HIGHLIGHT ACTIVE NAVIGATION LINK
// ==========================================
function initActiveLink() {
    const currentUrl = window.location.pathname.split("/").pop() || "index.html";
    const navItems = document.querySelectorAll(".sidebar ul li");
    
    navItems.forEach(item => {
        const link = item.querySelector("a");
        if (link) {
            const href = link.getAttribute("href");
            if (href === currentUrl || (currentUrl === "" && href === "index.html")) {
                item.classList.add("active");
            } else {
                item.classList.remove("active");
            }
        }
    });
}

// ==========================================
// 4. BACK-TO-TOP BUTTON
// ==========================================
function initBackToTop() {
    let bttBtn = document.getElementById("backToTopBtn");
    if (!bttBtn) {
        bttBtn = document.createElement("div");
        bttBtn.id = "backToTopBtn";
        bttBtn.className = "back-to-top";
        bttBtn.innerHTML = '<i class="fa-solid fa-arrow-up"></i>';
        document.body.appendChild(bttBtn);
    }

    window.addEventListener("scroll", () => {
        if (window.scrollY > 300) {
            bttBtn.classList.add("show");
        } else {
            bttBtn.classList.remove("show");
        }
    });

    bttBtn.addEventListener("click", () => {
        window.scrollTo({
            top: 0,
            behavior: "smooth"
        });
    });
}

// ==========================================
// 5. TOAST NOTIFICATION SYSTEM
// ==========================================
function showToast(message, type = "success") {
    let container = document.getElementById("toastContainer");
    if (!container) {
        container = document.createElement("div");
        container.id = "toastContainer";
        container.className = "toast-container";
        document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    toast.className = `custom-toast ${type}`;
    
    let iconClass = "fa-circle-check";
    if (type === "error") iconClass = "fa-circle-xmark";
    if (type === "info") iconClass = "fa-circle-info";

    toast.innerHTML = `
        <i class="fa-solid ${iconClass}"></i>
        <span>${message}</span>
    `;

    container.appendChild(toast);

    // Auto remove toast
    setTimeout(() => {
        toast.style.animation = "slideOut 0.3s cubic-bezier(0.4, 0, 0.2, 1) forwards";
        toast.addEventListener("animationend", () => toast.remove());
    }, 3000);
}

// ==========================================
// 6. RIPPLE BUTTON EFFECTS
// ==========================================
function initButtonRipples() {
    const buttons = document.querySelectorAll("button, .btn");
    buttons.forEach(btn => {
        btn.addEventListener("click", function(e) {
            const rect = btn.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            const ripple = document.createElement("span");
            ripple.style.position = "absolute";
            ripple.style.left = `${x}px`;
            ripple.style.top = `${y}px`;
            ripple.style.width = "0";
            ripple.style.height = "0";
            ripple.style.background = "rgba(255, 255, 255, 0.4)";
            ripple.style.borderRadius = "50%";
            ripple.style.transform = "translate(-50%, -50%)";
            ripple.style.pointerEvents = "none";
            ripple.style.animation = "rippleAnim 0.6s ease-out";
            
            btn.appendChild(ripple);

            ripple.addEventListener("animationend", () => ripple.remove());
        });
    });
}

// Ripple animation keyframes injected dynamically
if (!document.getElementById("rippleStyles")) {
    const style = document.createElement("style");
    style.id = "rippleStyles";
    style.innerHTML = `
        @keyframes rippleAnim {
            to {
                width: 300px;
                height: 300px;
                opacity: 0;
            }
        }
        @keyframes slideOut {
            to {
                transform: translateY(20px);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
}

// ==========================================
// 7. GLOBAL SEARCH FIELD AUTO-FILTER
// ==========================================
function initNavSearch() {
    const searchInput = document.querySelector("nav .search input");
    if (searchInput) {
        searchInput.addEventListener("keyup", function () {
            const query = this.value.toLowerCase();
            const cards = document.querySelectorAll(".card, .plant-card, .history-card");
            cards.forEach(card => {
                const text = card.textContent.toLowerCase();
                if (text.includes(query)) {
                    card.style.display = "";
                } else {
                    card.style.display = "none";
                }
            });
        });
    }
}

// Export for page-specific scripts to use
window.showToast = showToast;
