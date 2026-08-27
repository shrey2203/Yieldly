import React from 'react';
import './heatmap.css';

const HeatmapUI = ({ heatmapData, loading, error, handleDropdownChange, options, selectedOption, handleTileClick }) => {

    // --- 1. SAFE PARSER HELPER ---
    // This removes commas (,), percentages (%), and spaces before converting to a number
    const safeParse = (value) => {
        if (!value) return 0;
        // Convert to string, remove commas/%, then parse
        const cleanString = String(value).replace(/,/g, '').replace(/%/g, '');
        const number = parseFloat(cleanString);
        return isNaN(number) ? 0 : number;
    };

    // --- 2. STYLE LOGIC (Updated to use safeParse) ---
    const getCardStyle = (pctChange) => {
        const value = safeParse(pctChange);
        
        // Green Scale
        if (value >= 3.0) return { bg: '#14532d', color: '#fff' }; // Deep Green
        if (value >= 1.5) return { bg: '#15803d', color: '#fff' };
        if (value > 0)    return { bg: '#22c55e', color: '#fff' }; // Standard Green
        
        // Red Scale
        if (value <= -3.0) return { bg: '#7f1d1d', color: '#fff' }; // Deep Red
        if (value <= -1.5) return { bg: '#b91c1c', color: '#fff' };
        if (value < 0)     return { bg: '#ef4444', color: '#fff' }; // Standard Red
        
        // Neutral (0 or NaN)
        return { bg: '#6b7280', color: '#fff' }; // Gray
    };

    return (
        <div className="heatmap-page"> 
            <header className="heatmap-header"> 
                <div className="header-left">
                    <h2 className="heatmap-title">Market Heatmap</h2>
                    <p className="heatmap-subtitle">Real-time performance visualization</p>
                </div>
                
                <div className="header-controls">
                    <select 
                        value={selectedOption} 
                        onChange={handleDropdownChange} 
                        className="modern-dropdown"
                    > 
                        {options.map((option, idx) => ( 
                            <option key={idx} value={option}>{option}</option> 
                        ))}
                    </select>
                </div>
            </header> 

            {loading ? (
                <div className="loading-container">
                    <div className="spinner"></div>
                    <p>Analyzing Market Data...</p>
                </div>
            ) : error ? (
                <div className="error-message">{error}</div>
            ) : (
                <div className="heatmap-grid">
                    {heatmapData.map(([ticker, [price, pctChange, absChange]], idx) => {
                        
                        // Use safeParse for logic
                        const numPct = safeParse(pctChange);
                        const numChange = safeParse(absChange);
                        const numPrice = safeParse(price);

                        const style = getCardStyle(numPct);
                        const isPositive = numPct > 0;

                        return (
                            <div 
                                key={idx} 
                                className="heatmap-card"
                                style={{ backgroundColor: style.bg, color: style.color }}
                                onClick={() => handleTileClick(ticker)}
                            >
                                <div className="card-top">
                                    <span className="ticker-name">{ticker}</span>
                                    <span className="ticker-price">
                                        {/* Display formatting */}
                                        {numPrice.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                                    </span>
                                </div>
                                
                                <div className="card-body">
                                    <span className="ticker-percent">
                                        {isPositive ? "+" : ""}{numPct.toFixed(2)}%
                                    </span>
                                </div>

                                <div className="card-footer">
                                    <span className="ticker-change">
                                        {/* Logic for Arrow and Points */}
                                        {isPositive ? "▲" : "▼"} {Math.abs(numChange).toFixed(2)} pts
                                    </span>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
};

export default HeatmapUI;