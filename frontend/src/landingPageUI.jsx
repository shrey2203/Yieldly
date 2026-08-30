import React, { useState, useEffect, useMemo } from "react";
import "./landingPage.css";
import { useNavigate } from "react-router-dom";

const LandingPageUI = ({ handleLogout }) => {
  const navigate = useNavigate();
  const rawUser = localStorage.getItem("username");
  const username = (rawUser && rawUser !== "null" && rawUser !== "undefined") ? rawUser : "User";
  
  const [totalDividends, setTotalDividends] = useState(null);
  const [portfolioMetrics, setPortfolioMetrics] = useState(null);
  const [mfMetrics, setMfMetrics] = useState(null);
  const [activeTab, setActiveTab] = useState("combined"); // 'combined' | 'equity' | 'mf'

  // Time-based dynamic greeting
  const greeting = useMemo(() => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good Morning";
    if (hour < 18) return "Good Afternoon";
    return "Good Evening";
  }, []);

  const todayFormatted = useMemo(() => {
    const options = { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' };
    return new Date().toLocaleDateString('en-IN', options);
  }, []);

  // Compute Combined Sum of Both (Equity + Mutual Funds)
  const combinedMetrics = useMemo(() => {
    if (!portfolioMetrics && !mfMetrics) return null;
    const eqCurr = portfolioMetrics ? portfolioMetrics.current : 0;
    const eqInv = portfolioMetrics ? portfolioMetrics.invested : 0;
    const mfCurr = mfMetrics ? mfMetrics.current : 0;
    const mfInv = mfMetrics ? mfMetrics.invested : 0;

    const current = eqCurr + mfCurr;
    const invested = eqInv + mfInv;
    const profit = current - invested;
    const profitPct = invested > 0 ? (profit / invested) * 100 : 0;
    return { current, invested, profit, profitPct, eqCurr, eqInv, mfCurr, mfInv };
  }, [portfolioMetrics, mfMetrics]);

  useEffect(() => {
    const fetchQuickMetrics = async () => {
      try {
        const token = localStorage.getItem("token");
        const headers = token ? { 'Authorization': `Bearer ${token}` } : {};

        // 1. Fetch dividends
        fetch(`/api/fetchTotalDividends?userId=${encodeURIComponent(username)}`, { headers })
          .then(res => res.ok ? res.json() : null)
          .then(divData => {
            if (divData) setTotalDividends(divData.totalDividends || 0);
          })
          .catch(err => console.error("Error fetching dividends:", err));

        // 2. Fetch Equity portfolio holdings
        fetch(`/api/fetchPortfolio?userId=${encodeURIComponent(username)}`, { headers })
          .then(res => res.ok ? res.json() : null)
          .then(portData => {
            if (portData && portData.holdings) {
              let invested = 0;
              let current = 0;
              portData.holdings.forEach(item => {
                if (Number(item.quantity || 0) > 0) {
                  invested += Number(item.totalBuy || 0);
                  current += Number(item.totalValue || 0);
                }
              });
              const profit = current - invested;
              const profitPct = invested > 0 ? (profit / invested) * 100 : 0;
              setPortfolioMetrics({ invested, current, profit, profitPct });
            }
          })
          .catch(err => console.error("Error fetching equity portfolio:", err));

        // 3. Fetch Mutual Funds data
        fetch(`/api/fetchMutualFundData?userId=${encodeURIComponent(username)}`, { headers })
          .then(res => res.ok ? res.json() : null)
          .then(mfData => {
            if (mfData) {
              const invested = Number(mfData.totalInvestedSum || 0);
              const current = Number(mfData.totalCurrentSum || 0);
              const profit = current - invested;
              const profitPct = invested > 0 ? (profit / invested) * 100 : 0;
              setMfMetrics({ invested, current, profit, profitPct });
            }
          })
          .catch(err => console.error("Error fetching mutual fund data:", err));

      } catch (err) {
        console.error("Error fetching overview metrics:", err);
      }
    };

    fetchQuickMetrics();
  }, [username]);

  const formatINR = (num) => Number(num || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 });

  const menuItems = [
    {
      title: "Equity Portfolio",
      path: "/portfolio",
      icon: "📊",
      subtitle: "Holdings, IPOs & P&L",
      color: "#6366f1",
      gradient: "linear-gradient(135deg, #6366f1 0%, #4338ca 100%)",
    },
    {
      title: "Mutual Funds",
      path: "/mutualFunds",
      icon: "🏦",
      subtitle: "SIP & NAV Growth",
      color: "#06b6d4",
      gradient: "linear-gradient(135deg, #06b6d4 0%, #0e7490 100%)",
    },
    {
      title: "Reports & Tax",
      path: "/reports",
      icon: "📄",
      subtitle: "STCG / LTCG Statements",
      color: "#ec4899",
      gradient: "linear-gradient(135deg, #ec4899 0%, #be185d 100%)",
    },
    {
      title: "Market Heatmap",
      path: "/heatmap",
      icon: "🔥",
      subtitle: "Sector Performance",
      color: "#f97316",
      gradient: "linear-gradient(135deg, #f97316 0%, #c2410c 100%)",
    },
    {
      title: "Technical Analysis",
      path: "/analysis",
      icon: "📈",
      subtitle: "Moving Averages & Trends",
      color: "#eab308",
      gradient: "linear-gradient(135deg, #eab308 0%, #a16207 100%)",
    },
  ];

  return (
    <div className="dashboard-container">
      {/* Top Navbar */}
      <nav className="dashboard-nav">
        <div className="nav-brand">
          <div className="brand-logo-badge">💎</div>
          <h1 className="logo-text">Finance<span className="logo-accent">Tracker</span></h1>
        </div>

        <div className="nav-right">
          <div className="user-profile-chip">
            <div className="user-avatar">{username.charAt(0).toUpperCase()}</div>
            <div className="user-info-text">
              <span className="user-name">{username}</span>
              <span className="user-status"><span className="status-dot"></span>Active</span>
            </div>
          </div>

          <button onClick={handleLogout} className="logout-btn" title="Sign Out">
            <span>Logout</span>
            <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
              <polyline points="16 17 21 12 16 7"></polyline>
              <line x1="21" y1="12" x2="9" y2="12"></line>
            </svg>
          </button>
        </div>
      </nav>

      {/* Main Content */}
      <main className="dashboard-content">
        {/* Welcome Header */}
        <div className="welcome-section">
          <div className="welcome-text-group">
            <span className="welcome-eyebrow">{todayFormatted}</span>
            <h2>{greeting}, <span className="welcome-name">{username}</span> 👋</h2>
            <p className="welcome-subtext">Track, Analyze, and Optimize your wealth.</p>
          </div>

          <div className="quick-actions-bar">
            <button className="quick-action-pill" onClick={() => navigate("/portfolio")}>
              <span>📊</span> Equity
            </button>
            <button className="quick-action-pill" onClick={() => navigate("/mutualFunds")}>
              <span>🏦</span> Mutual Funds
            </button>
            <button className="quick-action-pill" onClick={() => navigate("/reports")}>
              <span>📑</span> Tax Reports
            </button>
          </div>
        </div>

        {/* Wealth Perspective Tabs */}
        <div className="wealth-tab-container">
          <div className="wealth-tabs-pill">
            <button 
              className={`wealth-tab-btn ${activeTab === 'combined' ? 'active' : ''}`}
              onClick={() => setActiveTab('combined')}
            >
              <span>🌐</span> Total Wealth (Sum of Both)
            </button>
            <button 
              className={`wealth-tab-btn ${activeTab === 'equity' ? 'active' : ''}`}
              onClick={() => setActiveTab('equity')}
            >
              <span>📊</span> Equity
            </button>
            <button 
              className={`wealth-tab-btn ${activeTab === 'mf' ? 'active' : ''}`}
              onClick={() => setActiveTab('mf')}
            >
              <span>🏦</span> Mutual Funds
            </button>
          </div>
        </div>

        {/* Concise Metrics Strip */}
        <div className="metrics-strip">
          {activeTab === 'combined' && (
            <>
              {/* Total Wealth Combined Card */}
              <div className="metric-pill-card portfolio-stat-pill" onClick={() => navigate("/portfolio")}>
                <div className="metric-icon" style={{ background: 'rgba(99, 102, 241, 0.15)', color: '#6366f1' }}>💎</div>
                <div className="metric-details">
                  <div className="metric-header-inline">
                    <span className="metric-label">Total Net Worth</span>
                    {combinedMetrics && (
                      <span className={`metric-profit-tag ${combinedMetrics.profit >= 0 ? 'pos' : 'neg'}`}>
                        {combinedMetrics.profit >= 0 ? '▲ +' : '▼ -'}{Math.abs(combinedMetrics.profitPct).toFixed(2)}%
                      </span>
                    )}
                  </div>
                  <p className="metric-val">
                    {combinedMetrics ? `₹${formatINR(combinedMetrics.current)}` : "Loading..."}
                  </p>
                  <div className="metric-sub-breakdown">
                    <div className="sub-stat-row">
                      <span className="sub-stat-label">Invested:</span>
                      <span className="sub-stat-val">₹{combinedMetrics ? formatINR(combinedMetrics.invested) : "0"}</span>
                    </div>
                    <div className="sub-stat-row">
                      <span className="sub-stat-label">Profit:</span>
                      <span className={`sub-stat-val ${combinedMetrics?.profit >= 0 ? 'text-green' : 'text-red'}`}>
                        {combinedMetrics?.profit >= 0 ? '+₹' : '-₹'}{combinedMetrics ? formatINR(Math.abs(combinedMetrics.profit)) : "0"}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Equity Share Card */}
              <div className="metric-pill-card portfolio-stat-pill" onClick={() => navigate("/portfolio")}>
                <div className="metric-icon" style={{ background: 'rgba(99, 102, 241, 0.12)', color: '#6366f1' }}>💼</div>
                <div className="metric-details">
                  <div className="metric-header-inline">
                    <span className="metric-label">Equity</span>
                    {portfolioMetrics && (
                      <span className={`metric-profit-tag ${portfolioMetrics.profit >= 0 ? 'pos' : 'neg'}`}>
                        {portfolioMetrics.profit >= 0 ? '▲ +' : '▼ -'}{Math.abs(portfolioMetrics.profitPct).toFixed(2)}%
                      </span>
                    )}
                  </div>
                  <p className="metric-val">
                    {portfolioMetrics ? `₹${formatINR(portfolioMetrics.current)}` : "Loading..."}
                  </p>
                  <div className="metric-sub-breakdown">
                    <div className="sub-stat-row">
                      <span className="sub-stat-label">Invested:</span>
                      <span className="sub-stat-val">₹{portfolioMetrics ? formatINR(portfolioMetrics.invested) : "0"}</span>
                    </div>
                    <div className="sub-stat-row">
                      <span className="sub-stat-label">Profit:</span>
                      <span className={`sub-stat-val ${portfolioMetrics?.profit >= 0 ? 'text-green' : 'text-red'}`}>
                        {portfolioMetrics?.profit >= 0 ? '+₹' : '-₹'}{portfolioMetrics ? formatINR(Math.abs(portfolioMetrics.profit)) : "0"}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Mutual Funds Share Card */}
              <div className="metric-pill-card portfolio-stat-pill" onClick={() => navigate("/mutualFunds")}>
                <div className="metric-icon" style={{ background: 'rgba(6, 182, 212, 0.12)', color: '#06b6d4' }}>🏦</div>
                <div className="metric-details">
                  <div className="metric-header-inline">
                    <span className="metric-label">Mutual Funds</span>
                    {mfMetrics && (
                      <span className={`metric-profit-tag ${mfMetrics.profit >= 0 ? 'pos' : 'neg'}`}>
                        {mfMetrics.profit >= 0 ? '▲ +' : '▼ -'}{Math.abs(mfMetrics.profitPct).toFixed(2)}%
                      </span>
                    )}
                  </div>
                  <p className="metric-val">
                    {mfMetrics ? `₹${formatINR(mfMetrics.current)}` : "Loading..."}
                  </p>
                  <div className="metric-sub-breakdown">
                    <div className="sub-stat-row">
                      <span className="sub-stat-label">Invested:</span>
                      <span className="sub-stat-val">₹{mfMetrics ? formatINR(mfMetrics.invested) : "0"}</span>
                    </div>
                    <div className="sub-stat-row">
                      <span className="sub-stat-label">Profit:</span>
                      <span className={`sub-stat-val ${mfMetrics?.profit >= 0 ? 'text-green' : 'text-red'}`}>
                        {mfMetrics?.profit >= 0 ? '+₹' : '-₹'}{mfMetrics ? formatINR(Math.abs(mfMetrics.profit)) : "0"}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Total Dividends Card */}
              <div className="metric-pill-card" onClick={() => navigate("/portfolio")}>
                <div className="metric-icon" style={{ background: 'rgba(16, 185, 129, 0.12)', color: '#10b981' }}>🎁</div>
                <div className="metric-details">
                  <span className="metric-label">Total Dividends</span>
                  <p className="metric-val">
                    {totalDividends !== null ? `₹${formatINR(totalDividends)}` : "₹0"}
                  </p>
                  <span className="metric-sub text-green">Passive Yield</span>
                </div>
              </div>
            </>
          )}

          {activeTab === 'equity' && (
            <>
              {/* Equity Card */}
              <div className="metric-pill-card portfolio-stat-pill" onClick={() => navigate("/portfolio")}>
                <div className="metric-icon" style={{ background: 'rgba(99, 102, 241, 0.12)', color: '#6366f1' }}>💼</div>
                <div className="metric-details">
                  <div className="metric-header-inline">
                    <span className="metric-label">Equity Portfolio</span>
                    {portfolioMetrics && (
                      <span className={`metric-profit-tag ${portfolioMetrics.profit >= 0 ? 'pos' : 'neg'}`}>
                        {portfolioMetrics.profit >= 0 ? '▲ +' : '▼ -'}{Math.abs(portfolioMetrics.profitPct).toFixed(2)}%
                      </span>
                    )}
                  </div>
                  <p className="metric-val">
                    {portfolioMetrics ? `₹${formatINR(portfolioMetrics.current)}` : "Loading..."}
                  </p>
                  <div className="metric-sub-breakdown">
                    <div className="sub-stat-row">
                      <span className="sub-stat-label">Invested:</span>
                      <span className="sub-stat-val">₹{portfolioMetrics ? formatINR(portfolioMetrics.invested) : "0"}</span>
                    </div>
                    <div className="sub-stat-row">
                      <span className="sub-stat-label">Profit:</span>
                      <span className={`sub-stat-val ${portfolioMetrics?.profit >= 0 ? 'text-green' : 'text-red'}`}>
                        {portfolioMetrics?.profit >= 0 ? '+₹' : '-₹'}{portfolioMetrics ? formatINR(Math.abs(portfolioMetrics.profit)) : "0"}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Total Dividends */}
              <div className="metric-pill-card" onClick={() => navigate("/portfolio")}>
                <div className="metric-icon" style={{ background: 'rgba(16, 185, 129, 0.12)', color: '#10b981' }}>🎁</div>
                <div className="metric-details">
                  <span className="metric-label">Total Dividends</span>
                  <p className="metric-val">
                    {totalDividends !== null ? `₹${formatINR(totalDividends)}` : "₹0"}
                  </p>
                  <span className="metric-sub text-green">Passive Yield</span>
                </div>
              </div>

              {/* Heatmap */}
              <div className="metric-pill-card" onClick={() => navigate("/heatmap")}>
                <div className="metric-icon" style={{ background: 'rgba(249, 115, 22, 0.12)', color: '#f97316' }}>🔥</div>
                <div className="metric-details">
                  <span className="metric-label">Market Heatmap</span>
                  <p className="metric-val">Sector Pulse</p>
                  <span className="metric-sub">Explore Weights &rarr;</span>
                </div>
              </div>

              {/* Capital Gains */}
              <div className="metric-pill-card" onClick={() => navigate("/reports")}>
                <div className="metric-icon" style={{ background: 'rgba(236, 72, 153, 0.12)', color: '#ec4899' }}>📜</div>
                <div className="metric-details">
                  <span className="metric-label">Capital Gains</span>
                  <p className="metric-val">STCG & LTCG</p>
                  <span className="metric-sub">Tax Statements &rarr;</span>
                </div>
              </div>
            </>
          )}

          {activeTab === 'mf' && (
            <>
              {/* Mutual Funds Card */}
              <div className="metric-pill-card portfolio-stat-pill" onClick={() => navigate("/mutualFunds")}>
                <div className="metric-icon" style={{ background: 'rgba(6, 182, 212, 0.12)', color: '#06b6d4' }}>🏦</div>
                <div className="metric-details">
                  <div className="metric-header-inline">
                    <span className="metric-label">Mutual Funds</span>
                    {mfMetrics && (
                      <span className={`metric-profit-tag ${mfMetrics.profit >= 0 ? 'pos' : 'neg'}`}>
                        {mfMetrics.profit >= 0 ? '▲ +' : '▼ -'}{Math.abs(mfMetrics.profitPct).toFixed(2)}%
                      </span>
                    )}
                  </div>
                  <p className="metric-val">
                    {mfMetrics ? `₹${formatINR(mfMetrics.current)}` : "Loading..."}
                  </p>
                  <div className="metric-sub-breakdown">
                    <div className="sub-stat-row">
                      <span className="sub-stat-label">Invested:</span>
                      <span className="sub-stat-val">₹{mfMetrics ? formatINR(mfMetrics.invested) : "0"}</span>
                    </div>
                    <div className="sub-stat-row">
                      <span className="sub-stat-label">Profit:</span>
                      <span className={`sub-stat-val ${mfMetrics?.profit >= 0 ? 'text-green' : 'text-red'}`}>
                        {mfMetrics?.profit >= 0 ? '+₹' : '-₹'}{mfMetrics ? formatINR(Math.abs(mfMetrics.profit)) : "0"}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* SIP Tracker */}
              <div className="metric-pill-card" onClick={() => navigate("/mutualFunds")}>
                <div className="metric-icon" style={{ background: 'rgba(6, 182, 212, 0.12)', color: '#06b6d4' }}>📈</div>
                <div className="metric-details">
                  <span className="metric-label">SIP Analytics</span>
                  <p className="metric-val">NAV Growth</p>
                  <span className="metric-sub text-green">Active Milestones</span>
                </div>
              </div>

              {/* Fund Distribution */}
              <div className="metric-pill-card" onClick={() => navigate("/mutualFunds")}>
                <div className="metric-icon" style={{ background: 'rgba(99, 102, 241, 0.12)', color: '#6366f1' }}>⚖️</div>
                <div className="metric-details">
                  <span className="metric-label">Asset Allocation</span>
                  <p className="metric-val">Fund Breakdown</p>
                  <span className="metric-sub">View Details &rarr;</span>
                </div>
              </div>

              {/* Capital Gains */}
              <div className="metric-pill-card" onClick={() => navigate("/reports")}>
                <div className="metric-icon" style={{ background: 'rgba(236, 72, 153, 0.12)', color: '#ec4899' }}>📜</div>
                <div className="metric-details">
                  <span className="metric-label">Capital Gains</span>
                  <p className="metric-val">STCG & LTCG</p>
                  <span className="metric-sub">Tax Statements &rarr;</span>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Clean Module Cards */}
        <div className="card-grid">
          {menuItems.map((item, index) => (
            <div 
              key={index} 
              className="dashboard-card" 
              onClick={() => navigate(item.path)}
              style={{ "--card-accent": item.color }}
            >
              <div className="card-icon-bubble" style={{ background: item.gradient }}>
                {item.icon}
              </div>
              <div className="card-body">
                <h3>{item.title}</h3>
                <p className="card-desc">{item.subtitle}</p>
              </div>
              <div className="card-footer">
                <span className="card-action-text">Open</span>
                <span className="card-arrow-circle">&rarr;</span>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
};

export default LandingPageUI;