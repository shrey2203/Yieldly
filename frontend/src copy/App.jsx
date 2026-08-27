import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { useState, useEffect } from "react";
import "./App.css";
import LoginForm from "./loginForm";
import LandingPageUI from "./landingPageUI"
import Portfolio from "./portfolioLandingPage"; 
import Analysis from "./analysisLandingPage"; 
import Heatmap from "./heatmapLandingPage"; 
import MutualFund from "./mutualFundLandingPage"; 
import Report from "./reportsLandingPage"; 

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem("token"));
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const checkServerRestart = async () => {
        try {
            // This now points to http://localhost:5000/server_status via the proxy
            const response = await fetch("/api/server_status");
            
            if (!response.ok) throw new Error("Server response was not ok");
            
            const data = await response.json();
            const lastRestartId = sessionStorage.getItem("serverRestartId");

            if (lastRestartId && lastRestartId !== data.server_restart_id) {
                console.log("Server restart detected. Clearing session...");
                localStorage.clear();
                setIsAuthenticated(false);
            }

            sessionStorage.setItem("serverRestartId", data.server_restart_id);
        } catch (error) {
            console.error("Health check failed (Server might be down):", error);
        }
    };

    checkServerRestart();
}, []); // Empty array so it only runs once on page load

  const handleLoginSuccess = (token, username) => {
    console.log("Successfully logged in with : " + username)
    setIsLoading(true); 

    setTimeout(() => {
        setIsAuthenticated(true);
        setIsLoading(false); 
    }, 1000);
};

const handleLogout = () => {
  localStorage.clear();
  setIsAuthenticated(false);
};

return (
  <Router>
    {isLoading && (
      <div className="loading-mask">
        <div className="spinner"></div>
        <p>Logging in... Please wait</p>
      </div>
    )}

    <Routes>
      <Route
        path="/"
        element={
          isAuthenticated ? (
            <LandingPageUI handleLogout={handleLogout} />
          ) : (
            <LoginForm onLogin={handleLoginSuccess} />
          )
        }
      />
      <Route path="/portfolio" element={<Portfolio />} />
      <Route path="/analysis" element={<Analysis />} />
      <Route path="/heatmap" element={<Heatmap />} />
      <Route path="/mutualFunds" element={<MutualFund />} />
      <Route path="/reports" element={<Report />} />
    </Routes>
  </Router>
  );
}

export default App;