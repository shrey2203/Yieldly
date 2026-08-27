import React from "react";
import "./landingPage.css";
import { useNavigate } from "react-router-dom";

const LandingPageUI = ({ handleLogout }) => {
  const navigate = useNavigate();

  const menuItems = [
    { title: "Portfolio", path: "/portfolio", icon: "📊", color: "#6C5CE7" },
    { title: "Mutual Funds", path: "/mutualFunds", icon: "🏦", color: "#00CEC9" },
    { title: "Reports", path: "/reports", icon: "📄", color: "#FD79A8" },
    { title: "Heat Map", path: "/heatmap", icon: "🔥", color: "#FF7675" },
    { title: "Analysis", path: "/analysis", icon: "📈", color: "#FDCB6E" },
  ];

  return (
    <div className="dashboard-container">
      <nav className="dashboard-nav">
        <h1 className="logo-text">Finance<span className="logo-accent">Tracker</span></h1>
        <button onClick={handleLogout} className="logout-btn">
          <span>Logout</span>
          <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
        </button>
      </nav>

      <main className="dashboard-content">
        <div className="welcome-section">
          <h2>Dashboard Overview</h2>
          <p>Track, Analyze, and Optimize your wealth.</p>
        </div>

        <div className="card-grid">
          {menuItems.map((item, index) => (
            <div 
              key={index} 
              className="dashboard-card" 
              onClick={() => navigate(item.path)}
              style={{ "--accent-color": item.color }} // Pass color to CSS
            >
              <div className="card-icon-bg">{item.icon}</div>
              <h3>{item.title}</h3>
              <p>View Details &rarr;</p>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
};

export default LandingPageUI;