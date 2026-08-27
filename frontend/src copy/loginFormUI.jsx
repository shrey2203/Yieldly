import React from "react";
import "./loginForm.css"; 

const LoginFormUI = ({ username, setUsername, handleLogin, error, loading }) => {
  return (
    <div className="login-container">
      
      {/* --- PROCESSING OVERLAY (Premium Transition State) --- */}
      {loading && (
        <div className="processing-overlay">
          <div className="yi-loader-circle">
            <div className="yi-logo-inner">Yi.</div>
            <div className="orbit"></div>
          </div>
          <h2 className="processing-text">Securing your session...</h2>
          <p className="processing-subtext">Fetching your Yieldly portfolio</p>
        </div>
      )}

      {/* Main Wrapper: Blurs slightly when loading to focus on the overlay */}
      <div className={`login-wrapper ${loading ? "blur-out" : ""}`}>
        
        {/* LEFT SIDE: Branding Panel */}
        <div className="login-aside">
          <div className="aside-content">
            <h1>Invest in <br/><span className="highlight">Everything.</span></h1>
            <p>
                Simple, transparent investing in Stocks and Mutual Funds. 
            </p>
          </div>
        </div>

        {/* RIGHT SIDE: Form Panel */}
        <div className="login-box">
          {/* Custom Yieldly Abstract Logo */}
          <div className="login-logo" style={{ 
              width: '55px', 
              height: '55px', 
              background: 'linear-gradient(135deg, #00d09c 0%, #00b386 100%)',
              borderRadius: '14px',
              margin: '0 auto 25px auto',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              fontWeight: 'bold',
              fontSize: '22px',
          }}>
              Yi.
          </div>
          
          <h2>Login</h2>
          <p className="subtext">Enter your username to get started</p>

          <form onSubmit={handleLogin} className="login-form">
            <div className="form-group">
              <label htmlFor="username">Username</label>
              <input 
                id="username"
                type="text" 
                placeholder="..." 
                value={username} 
                onChange={(e) => setUsername(e.target.value)} 
                required 
                autoComplete="username"
              />
            </div>

            {/* Error Message Display */}
            {error && (
              <div className="error-message">
                <span>⚠️</span> {error}
              </div>
            )}

            <button 
                type="submit" 
                disabled={loading} 
                className="login-button"
            >
              Continue
            </button>
          </form>

          <p className="footer-agreement">
            By continuing, you agree to the Yieldly <br/>
            <strong>Terms of Service</strong> and <strong>Privacy Policy</strong>.
          </p>
        </div>

      </div>
    </div>
  );
};

export default LoginFormUI;