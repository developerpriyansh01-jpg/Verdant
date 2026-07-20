import { NavLink } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

const navItems = [
  { to: "/", icon: "fa-house", label: "Home", end: true },
  { to: "/plants", icon: "fa-seedling", label: "Plants" },
  { to: "/scanner", icon: "fa-camera", label: "AI Plant Scanner" },
  { to: "/garden", icon: "fa-tree", label: "My Garden" },
  { to: "/water", icon: "fa-droplet", label: "Water Saving" },
  { to: "/report", icon: "fa-triangle-exclamation", label: "Report Disease" },
  { to: "/community", icon: "fa-cloud-sun", label: "Season Care" },
  { to: "/history", icon: "fa-clock-rotate-left", label: "Scan History" },
  { to: "/profile", icon: "fa-user-circle", label: "My Profile" },
];

export default function Sidebar({ isOpen, onClose }) {
  const { logout } = useAuth();

  return (
    <>
      <div
        id="sidebarOverlay"
        className={`sidebar-overlay ${isOpen ? "show" : ""}`}
        onClick={onClose}
      />
      <aside className={`sidebar ${isOpen ? "open" : ""}`}>
        <div className="logo">
          <i className="fa-solid fa-leaf" />
          <h2>Verdant</h2>
        </div>
        <ul>
          {navItems.map((item) => (
            <li key={item.to}>
              <NavLink to={item.to} end={item.end} onClick={onClose}>
                <i className={`fa-solid ${item.icon}`} /> {item.label}
              </NavLink>
            </li>
          ))}
          <li id="sidebarLogout">
            <a
              href="#"
              onClick={(e) => {
                e.preventDefault();
                onClose();
                logout();
              }}
            >
              <i className="fa-solid fa-right-from-bracket" /> Logout
            </a>
          </li>
        </ul>
      </aside>
    </>
  );
}
