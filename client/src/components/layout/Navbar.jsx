import { useNavigate } from "react-router-dom";
import { useTheme } from "../../context/ThemeContext";
import { useAuth } from "../../context/AuthContext";
import toast from "react-hot-toast";

export default function Navbar({ onMenuToggle, isSidebarOpen, searchPlaceholder = "Search Plants...", onSearch }) {
  const { isDark, toggleTheme } = useTheme();
  const { getPhotoUrl } = useAuth();
  const navigate = useNavigate();

  return (
    <nav>
      <div className="hamburger" id="navHamburger" onClick={onMenuToggle}>
        <i className={`fa-solid ${isSidebarOpen ? "fa-xmark" : "fa-bars"}`} />
      </div>
      <div className="search">
        <input
          type="text"
          placeholder={searchPlaceholder}
          onKeyUp={(e) => onSearch?.(e.target.value.toLowerCase())}
        />
        <i className="fa-solid fa-magnifying-glass" />
      </div>
      <div className="right">
        <i
          className={`fa-solid ${isDark ? "fa-sun" : "fa-moon"}`}
          id="themeBtn"
          onClick={toggleTheme}
          style={{ cursor: "pointer" }}
        />
        <span id="navTemp">28°C</span>
        <i
          className="fa-regular fa-bell"
          id="bellIcon"
          style={{ cursor: "pointer" }}
          onClick={() => toast("🔔 You are completely caught up! No new notifications.", { icon: "ℹ️" })}
        />
        <img
          src={getPhotoUrl()}
          alt="User avatar"
          id="navProfilePic"
          onClick={() => navigate("/profile")}
          onError={(e) => {
            e.target.src =
              "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=100&h=100";
          }}
          style={{ cursor: "pointer" }}
          title="View Profile"
        />
      </div>
    </nav>
  );
}
