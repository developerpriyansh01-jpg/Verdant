import { Link } from "react-router-dom";

export default function Footer({ full = true }) {
  if (!full) {
    return (
      <footer>
        <div className="footer-content">
          <div className="footer-section">
            <h3>Verdant AI</h3>
            <p>
              Empowering plant parents with machine learning diagnostics, eco-friendly conservation
              algorithms, and direct botanical tools.
            </p>
          </div>
        </div>
        <div className="footer-bottom">
          <p>&copy; 2026 Verdant AI. All rights reserved.</p>
        </div>
      </footer>
    );
  }

  return (
    <footer>
      <div className="footer-content">
        <div className="footer-section">
          <h3>Verdant AI</h3>
          <p>
            Empowering plant parents with machine learning diagnostics, eco-friendly conservation
            algorithms, and direct botanical tools.
          </p>
          <div className="social-icons">
            <a href="#"><i className="fa-brands fa-facebook" /></a>
            <a href="#"><i className="fa-brands fa-instagram" /></a>
            <a href="#"><i className="fa-brands fa-twitter" /></a>
            <a href="#"><i className="fa-brands fa-github" /></a>
          </div>
        </div>
        <div className="footer-section">
          <h3>Quick Navigation</h3>
          <ul>
            <li><Link to="/">Dashboard Home</Link></li>
            <li><Link to="/plants">Plant Library</Link></li>
            <li><Link to="/scanner">AI Leaf Scanner</Link></li>
            <li><Link to="/garden">My Digital Garden</Link></li>
          </ul>
        </div>
        <div className="footer-section">
          <h3>Contact Info</h3>
          <ul>
            <li><a href="mailto:contact@verdant-app.io"><i className="fa-solid fa-envelope" /> contact@verdant-app.io</a></li>
            <li><a href="tel:+15552349871"><i className="fa-solid fa-phone" /> +1 (555) 234-9871</a></li>
            <li><a href="#"><i className="fa-solid fa-location-dot" /> San Francisco, CA</a></li>
          </ul>
        </div>
      </div>
      <div className="footer-bottom">
        <p>&copy; 2026 Verdant AI. All rights reserved. Designed with ❤️ for a greener planet.</p>
      </div>
    </footer>
  );
}
