import { useEffect, useState } from "react";
import Sidebar from "./Sidebar";
import Navbar from "./Navbar";
import Footer from "./Footer";
import BackToTop from "./BackToTop";

export default function Layout({ children, searchPlaceholder, onSearch, footerFull = true }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    document.body.style.overflow = sidebarOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [sidebarOpen]);

  useEffect(() => {
    const style = document.getElementById("rippleStyles");
    if (!style) {
      const el = document.createElement("style");
      el.id = "rippleStyles";
      el.innerHTML = `
        @keyframes rippleAnim {
          to { width: 300px; height: 300px; opacity: 0; }
        }
      `;
      document.head.appendChild(el);
    }

    const handleRipple = (e) => {
      const btn = e.currentTarget;
      const rect = btn.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const ripple = document.createElement("span");
      ripple.style.cssText = `position:absolute;left:${x}px;top:${y}px;width:0;height:0;background:rgba(255,255,255,0.4);border-radius:50%;transform:translate(-50%,-50%);pointer-events:none;animation:rippleAnim 0.6s ease-out`;
      btn.appendChild(ripple);
      ripple.addEventListener("animationend", () => ripple.remove());
    };

    const buttons = document.querySelectorAll("button, .btn");
    buttons.forEach((btn) => {
      if (!btn.dataset.ripple) {
        btn.dataset.ripple = "true";
        btn.style.position = btn.style.position || "relative";
        btn.style.overflow = "hidden";
        btn.addEventListener("click", handleRipple);
      }
    });
  });

  return (
    <div className="container">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <main className="main">
        <Navbar
          isSidebarOpen={sidebarOpen}
          onMenuToggle={() => setSidebarOpen((o) => !o)}
          searchPlaceholder={searchPlaceholder}
          onSearch={onSearch}
        />
        {children}
        <Footer full={footerFull} />
      </main>
      <BackToTop />
    </div>
  );
}
