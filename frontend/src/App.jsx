import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion"; 
import { ModuleRegistry } from 'ag-grid-community';
import { RowGroupingModule, PivotModule, TreeDataModule } from 'ag-grid-enterprise';

import "./App.css";
import LoginForm from "./loginForm";
import LandingPageUI from "./landingPageUI";
import Portfolio from "./portfolioLandingPage"; 
import Analysis from "./analysisLandingPage"; 
import Heatmap from "./heatmapLandingPage"; 
import MutualFund from "./mutualFundLandingPage"; 
import Report from "./reportsLandingPage"; 

// Register AG Grid Modules
ModuleRegistry.registerModules([RowGroupingModule, PivotModule, TreeDataModule]);

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem("token"));
  const [isLoading, setIsLoading] = useState(false);

  // ... (keep your checkServerRestart useEffect here)

  const handleLoginSuccess = (token, username) => {
    console.log("Login sequence started...");
    setIsLoading(true); 

    // Important: We need a delay (e.g., 1.5s) to let the entry/exit animations play
    setTimeout(() => {
        setIsAuthenticated(true);
        setIsLoading(false); 
    }, 1500); 
  };

  const handleLogout = () => {
    localStorage.clear();
    setIsAuthenticated(false);
  };

  return (
    <Router>
      {/* 
          CRITICAL: AnimatePresence must be a direct parent 
          of the conditional {isLoading && ...} block 
      */}
      <AnimatePresence mode="wait">
        {isLoading && (
          <motion.div 
            key="loading-screen" // Unique key is required for exit animations
            className="loading-mask"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, scale: 1.1 }}
            transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
          >
            <motion.div 
              className="loader-content"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1, duration: 0.5 }}
            >
              <div className="spinner"></div>
              <motion.p
                animate={{ opacity: [0.5, 1, 0.5] }}
                transition={{ repeat: Infinity, duration: 2 }}
              >
                Syncing Portfolio Data...
              </motion.p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <Routes>
        <Route
          path="/"
          element={
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5 }}
            >
              {isAuthenticated ? (
                <LandingPageUI handleLogout={handleLogout} />
              ) : (
                <LoginForm onLogin={handleLoginSuccess} />
              )}
            </motion.div>
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