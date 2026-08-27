import React, { useState, useEffect, useMemo } from 'react';
import { quantQuestions as initialData } from './data';
import { 
  ChevronRight, ChevronLeft, Eye, EyeOff, LayoutGrid, 
  CheckCircle2, Circle, ExternalLink, Filter, ArrowUpDown, 
  Search, X, PenTool, Hash, Calculator 
} from 'lucide-react';
import 'katex/dist/katex.min.css';
import { InlineMath } from 'react-katex';
import confetti from 'canvas-confetti';
import { LineChart, Line, XAxis, YAxis, ReferenceLine, ResponsiveContainer } from 'recharts';

// --- CONCEPT VISUALIZER ---
const BlackScholesWidget = () => {
  const [s, setS] = useState(100);
  const [k, setK] = useState(100);
  const [v, setV] = useState(0.2); 
  const [t, setT] = useState(1);   

  const calculateDelta = () => {
    const d1 = (Math.log(s / k) + (0.05 + Math.pow(v, 2) / 2) * t) / (v * Math.sqrt(t));
    return (0.5 * (1 + Math.tanh(0.7988 * (d1 + 0.03535 * Math.pow(d1, 3))))).toFixed(3);
  };

  return (
    <div className="mt-6 p-8 bg-slate-900 rounded-[2.5rem] text-white shadow-xl border border-slate-700">
      <div className="flex items-center gap-2 mb-6 text-blue-400 font-black text-xs uppercase tracking-widest">
        <Calculator size={18} /> Greek Sensitivity Engine
      </div>
      <div className="grid grid-cols-2 gap-6 mb-8">
        {[[s, setS, "Spot"], [k, setK, "Strike"], [v, setV, "Vol"], [t, setT, "Time"]].map(([val, setVal, label]) => (
          <div key={label}>
            <label className="block text-[10px] text-slate-400 font-black uppercase mb-2 tracking-widest">{label}</label>
            <input type="number" step="0.1" value={val} onChange={(e) => setVal(Number(e.target.value))} className="w-full bg-slate-800 p-3 rounded-xl border border-slate-700 font-mono text-sm outline-none focus:ring-1 focus:ring-blue-400" />
          </div>
        ))}
      </div>
      <div className="bg-blue-600 p-6 rounded-2xl flex justify-between items-center">
        <span className="font-black text-xs uppercase tracking-widest">Call Delta</span>
        <span className="text-3xl font-black font-mono tracking-tighter">{calculateDelta()}</span>
      </div>
    </div>
  );
};

const LawOfLargeNumbersWidget = () => {
  const [data, setData] = useState([]);
  const [totalSum, setTotalSum] = useState(0);
  const [totalRolls, setTotalRolls] = useState(0);

  const rollDice = (times) => {
    let currentSum = totalSum;
    let currentRolls = totalRolls;
    const newData = [];

    for (let i = 0; i < times; i++) {
      const roll = Math.floor(Math.random() * 6) + 1;
      currentSum += roll;
      currentRolls += 1;
      
      // To keep the chart snappy, we only sample points if rolling large batches
      if (times <= 10 || i % (times / 10) === 0 || i === times - 1) {
        newData.push({
          rollCount: currentRolls,
          average: Number((currentSum / currentRolls).toFixed(3))
        });
      }
    }

    setTotalSum(currentSum);
    setTotalRolls(currentRolls);
    // Keep only the last 200 data points to prevent Recharts from lagging
    setData(prev => [...prev, ...newData].slice(-200));
  };

  const reset = () => {
    setData([]);
    setTotalSum(0);
    setTotalRolls(0);
  };

  const currentAvg = totalRolls === 0 ? 0 : (totalSum / totalRolls).toFixed(3);

  return (
    <div className="mt-6 p-8 bg-slate-900 rounded-[2.5rem] text-white shadow-xl border border-slate-700">
      <div className="flex items-center justify-between mb-6">
        <div className="text-blue-400 font-black text-xs uppercase tracking-widest">
          Law of Large Numbers Engine
        </div>
        <button onClick={reset} className="text-[10px] text-slate-400 hover:text-red-400 uppercase tracking-widest font-bold transition-colors">
          Reset Data
        </button>
      </div>

      <div className="grid grid-cols-2 gap-6 mb-6">
        <div className="bg-slate-800 p-4 rounded-2xl border border-slate-700">
          <div className="text-[10px] text-slate-400 font-black uppercase mb-1 tracking-widest">Total Rolls</div>
          <div className="text-2xl font-black font-mono">{totalRolls}</div>
        </div>
        <div className="bg-blue-600 p-4 rounded-2xl shadow-lg shadow-blue-900/20">
          <div className="text-[10px] text-blue-200 font-black uppercase mb-1 tracking-widest">Current Average</div>
          <div className="text-2xl font-black font-mono">{currentAvg}</div>
        </div>
      </div>

      {/* Recharts Visualization */}
      <div className="h-48 w-full bg-slate-800 rounded-2xl p-4 mb-6 border border-slate-700">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <XAxis dataKey="rollCount" hide />
            <YAxis domain={[1, 6]} ticks={[1, 2, 3, 4, 5, 6]} stroke="#475569" tick={{ fontSize: 10, fill: '#94a3b8' }} />
            {/* The Theoretical Expected Value Line */}
            <ReferenceLine y={3.5} stroke="#f59e0b" strokeDasharray="3 3" label={{ position: 'top', value: 'E[X] = 3.5', fill: '#f59e0b', fontSize: 10 }} />
            <Line type="monotone" dataKey="average" stroke="#3b82f6" strokeWidth={2} dot={false} isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="flex gap-3">
        <button onClick={() => rollDice(1)} className="flex-1 py-3 bg-slate-800 hover:bg-slate-700 border border-slate-600 rounded-xl text-xs font-bold uppercase tracking-widest transition-all active:scale-95">Roll 1x</button>
        <button onClick={() => rollDice(10)} className="flex-1 py-3 bg-slate-800 hover:bg-slate-700 border border-slate-600 rounded-xl text-xs font-bold uppercase tracking-widest transition-all active:scale-95">Roll 10x</button>
        <button onClick={() => rollDice(100)} className="flex-1 py-3 bg-blue-600 hover:bg-blue-500 rounded-xl text-xs font-bold uppercase tracking-widest shadow-lg shadow-blue-900/20 transition-all active:scale-95">Roll 100x</button>
      </div>
    </div>
  );
};

// --- CONCEPT VISUALIZER: Coin Run Simulator ---
const CoinRunsWidget = () => {
  const [data, setData] = useState([]);
  const [simulations, setSimulations] = useState(0);
  const [totalRuns, setTotalRuns] = useState(0);
  const [lastSequence, setLastSequence] = useState([]);
  
  const N = 100;
  const theoreticalAvg = 50.5;

  const runSimulation = (times) => {
    let currentSims = simulations;
    let currentTotalRuns = totalRuns;
    let newSequence = [];
    const newData = [];

    for (let i = 0; i < times; i++) {
      let runs = 1;
      let prevFlip = Math.random() > 0.5 ? 'H' : 'T';
      newSequence = [prevFlip];

      for (let j = 1; j < N; j++) {
        const flip = Math.random() > 0.5 ? 'H' : 'T';
        if (flip !== prevFlip) runs++;
        newSequence.push(flip);
        prevFlip = flip;
      }

      currentSims++;
      currentTotalRuns += runs;

      // Downsample chart data for performance on large batches
      if (times <= 10 || i % Math.max(1, Math.floor(times / 20)) === 0 || i === times - 1) {
        newData.push({
          simCount: currentSims,
          average: Number((currentTotalRuns / currentSims).toFixed(2))
        });
      }
    }

    setSimulations(currentSims);
    setTotalRuns(currentTotalRuns);
    setLastSequence(newSequence);
    setData(prev => [...prev, ...newData].slice(-150)); // Keep last 150 points for performance
  };

  const reset = () => {
    setData([]);
    setSimulations(0);
    setTotalRuns(0);
    setLastSequence([]);
  };

  const currentAvg = simulations === 0 ? 0 : (totalRuns / simulations).toFixed(2);

  return (
    <div className="mt-6 p-8 bg-slate-900 rounded-[2.5rem] text-white shadow-xl border border-slate-700">
      <div className="flex items-center justify-between mb-6">
        <div className="text-blue-400 font-black text-xs uppercase tracking-widest">
          Monte Carlo: Coin Run Expectation
        </div>
        <button onClick={reset} className="text-[10px] text-slate-400 hover:text-red-400 uppercase tracking-widest font-bold transition-colors">
          Reset Data
        </button>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-slate-800 p-4 rounded-2xl border border-slate-700 text-center">
          <div className="text-[9px] text-slate-400 font-black uppercase mb-1 tracking-widest">Simulations</div>
          <div className="text-xl font-black font-mono">{simulations}</div>
        </div>
        <div className="bg-slate-800 p-4 rounded-2xl border border-slate-700 text-center">
          <div className="text-[9px] text-slate-400 font-black uppercase mb-1 tracking-widest">Expected E[R]</div>
          <div className="text-xl font-black font-mono text-amber-400">{theoreticalAvg}</div>
        </div>
        <div className="bg-blue-600 p-4 rounded-2xl shadow-lg shadow-blue-900/20 text-center">
          <div className="text-[9px] text-blue-200 font-black uppercase mb-1 tracking-widest">Empirical Avg</div>
          <div className="text-xl font-black font-mono">{currentAvg}</div>
        </div>
      </div>

      {/* Visual Sequence Grid */}
      {lastSequence.length > 0 && (
        <div className="mb-6">
          <div className="text-[9px] text-slate-400 font-black uppercase mb-2 tracking-widest">Latest Sequence Generated</div>
          <div className="flex flex-wrap gap-[2px] p-3 bg-slate-800 rounded-xl border border-slate-700">
            {lastSequence.map((flip, idx) => (
              <span 
                key={idx} 
                className={`w-3.5 h-3.5 text-[7px] flex items-center justify-center rounded-sm font-black ${flip === 'H' ? 'bg-blue-500 text-white' : 'bg-slate-600 text-slate-300'}`}
              >
                {flip}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Convergence Chart */}
      <div className="h-40 w-full bg-slate-800 rounded-2xl p-4 mb-6 border border-slate-700">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <XAxis dataKey="simCount" hide />
            <YAxis domain={[40, 60]} stroke="#475569" tick={{ fontSize: 10, fill: '#94a3b8' }} />
            <ReferenceLine y={theoreticalAvg} stroke="#f59e0b" strokeDasharray="3 3" label={{ position: 'top', value: 'E[R] = 50.5', fill: '#f59e0b', fontSize: 10 }} />
            <Line type="monotone" dataKey="average" stroke="#3b82f6" strokeWidth={2} dot={false} isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="flex gap-3">
        <button onClick={() => runSimulation(1)} className="flex-1 py-3 bg-slate-800 hover:bg-slate-700 border border-slate-600 rounded-xl text-xs font-bold uppercase tracking-widest transition-all active:scale-95">Sim 1x</button>
        <button onClick={() => runSimulation(10)} className="flex-1 py-3 bg-slate-800 hover:bg-slate-700 border border-slate-600 rounded-xl text-xs font-bold uppercase tracking-widest transition-all active:scale-95">Sim 10x</button>
        <button onClick={() => runSimulation(100)} className="flex-1 py-3 bg-blue-600 hover:bg-blue-500 rounded-xl text-xs font-bold uppercase tracking-widest shadow-lg shadow-blue-900/20 transition-all active:scale-95">Sim 100x</button>
      </div>
    </div>
  );
};

// --- CONCEPT VISUALIZER: Monte Carlo Max of Three ---
const MaxOfThreeWidget = () => {
  const [data, setData] = useState([]);
  const [simulations, setSimulations] = useState(0);
  const [successes, setSuccesses] = useState(0);
  const [lastDraw, setLastDraw] = useState([0, 0, 0]);
  
  const theoreticalP = 0.488;

  const runSimulation = (times) => {
    let currentSims = simulations;
    let currentSuccesses = successes;
    let newDraw = [0, 0, 0];
    const newData = [];

    for (let i = 0; i < times; i++) {
      const x1 = Math.random();
      const x2 = Math.random();
      const x3 = Math.random();
      const maxVal = Math.max(x1, x2, x3);

      if (maxVal > 0.8) currentSuccesses++;
      currentSims++;
      newDraw = [x1, x2, x3];

      // Downsample chart data for performance on large batches
      if (times <= 10 || i % Math.max(1, Math.floor(times / 20)) === 0 || i === times - 1) {
        newData.push({
          simCount: currentSims,
          probability: Number((currentSuccesses / currentSims).toFixed(3))
        });
      }
    }

    setSimulations(currentSims);
    setSuccesses(currentSuccesses);
    setLastDraw(newDraw);
    setData(prev => [...prev, ...newData].slice(-150)); // Keep last 150 points
  };

  const reset = () => {
    setData([]);
    setSimulations(0);
    setSuccesses(0);
    setLastDraw([0, 0, 0]);
  };

  const currentProb = simulations === 0 ? "0.000" : (successes / simulations).toFixed(3);
  const isLatestSuccess = Math.max(...lastDraw) > 0.8;

  return (
    <div className="mt-6 p-8 bg-slate-900 rounded-[2.5rem] text-white shadow-xl border border-slate-700">
      <div className="flex items-center justify-between mb-6">
        <div className="text-blue-400 font-black text-xs uppercase tracking-widest">
          Monte Carlo: Order Statistics Max
        </div>
        <button onClick={reset} className="text-[10px] text-slate-400 hover:text-red-400 uppercase tracking-widest font-bold transition-colors">
          Reset Data
        </button>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-slate-800 p-4 rounded-2xl border border-slate-700 text-center">
          <div className="text-[9px] text-slate-400 font-black uppercase mb-1 tracking-widest">Simulations</div>
          <div className="text-xl font-black font-mono">{simulations}</div>
        </div>
        <div className="bg-slate-800 p-4 rounded-2xl border border-slate-700 text-center">
          <div className="text-[9px] text-slate-400 font-black uppercase mb-1 tracking-widest">Theoretical P</div>
          <div className="text-xl font-black font-mono text-amber-400">{theoreticalP}</div>
        </div>
        <div className={`p-4 rounded-2xl shadow-lg text-center transition-colors ${isLatestSuccess && simulations > 0 ? 'bg-green-600 shadow-green-900/30' : 'bg-blue-600 shadow-blue-900/20'}`}>
          <div className="text-[9px] text-white/70 font-black uppercase mb-1 tracking-widest">Empirical P</div>
          <div className="text-xl font-black font-mono">{currentProb}</div>
        </div>
      </div>

      {/* Visual Draw Indicator */}
      {simulations > 0 && (
        <div className="mb-6 bg-slate-800 rounded-2xl p-6 border border-slate-700 relative">
          <div className="text-[9px] text-slate-400 font-black uppercase mb-4 tracking-widest flex justify-between">
            <span>Latest Draw: U(0,1)</span>
            <span className={isLatestSuccess ? 'text-green-400' : 'text-red-400'}>
              {isLatestSuccess ? 'SUCCESS (Max > 0.8)' : 'FAILED (Max ≤ 0.8)'}
            </span>
          </div>
          
          {/* Bar Chart Container */}
          <div className="relative h-24 flex items-end justify-around border-b-2 border-slate-600 pb-1">
            {/* 0.8 Threshold Line */}
            <div className="absolute w-full border-t-2 border-dashed border-amber-400 z-10" style={{ bottom: '80%' }}>
              <span className="absolute -top-4 left-0 text-[8px] font-bold text-amber-400">0.8 Threshold</span>
            </div>

            {/* The 3 Random Variables */}
            {lastDraw.map((val, idx) => (
              <div key={idx} className="flex flex-col items-center w-12 z-20">
                <span className="text-[10px] font-mono text-slate-300 mb-1">{val.toFixed(2)}</span>
                <div 
                  className={`w-full rounded-t-sm transition-all duration-300 ${val > 0.8 ? 'bg-green-400' : 'bg-blue-500'}`}
                  style={{ height: `${val * 100}%`, minHeight: '4px' }}
                />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Convergence Line Chart */}
      <div className="h-40 w-full bg-slate-800 rounded-2xl p-4 mb-6 border border-slate-700">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <XAxis dataKey="simCount" hide />
            <YAxis domain={[0, 1]} ticks={[0, 0.2, 0.4, 0.6, 0.8, 1]} stroke="#475569" tick={{ fontSize: 10, fill: '#94a3b8' }} />
            <ReferenceLine y={theoreticalP} stroke="#f59e0b" strokeDasharray="3 3" label={{ position: 'top', value: 'P = 0.488', fill: '#f59e0b', fontSize: 10 }} />
            <Line type="monotone" dataKey="probability" stroke="#3b82f6" strokeWidth={2} dot={false} isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="flex gap-3">
        <button onClick={() => runSimulation(1)} className="flex-1 py-3 bg-slate-800 hover:bg-slate-700 border border-slate-600 rounded-xl text-xs font-bold uppercase tracking-widest transition-all active:scale-95">Draw 1x</button>
        <button onClick={() => runSimulation(10)} className="flex-1 py-3 bg-slate-800 hover:bg-slate-700 border border-slate-600 rounded-xl text-xs font-bold uppercase tracking-widest transition-all active:scale-95">Draw 10x</button>
        <button onClick={() => runSimulation(100)} className="flex-1 py-3 bg-blue-600 hover:bg-blue-500 rounded-xl text-xs font-bold uppercase tracking-widest shadow-lg shadow-blue-900/20 transition-all active:scale-95">Draw 100x</button>
      </div>
    </div>
  );
};

// --- CONCEPT VISUALIZER: Bayes' Theorem / Area Model ---
const BayesTheoremWidget = () => {
  const [priorD1, setPriorD1] = useState(50);
  const [d1Black, setD1Black] = useState(100);
  const [d2Black, setD2Black] = useState(50);

  // Derived Values
  const priorD2 = 100 - priorD1;
  const countD1Black = Math.round((priorD1 * d1Black) / 100);
  const countD2Black = Math.round((priorD2 * d2Black) / 100);
  const totalBlack = countD1Black + countD2Black;
  
  const posteriorD1 = totalBlack > 0 ? ((countD1Black / totalBlack) * 100).toFixed(1) : "0.0";

  // Generate 100 grid cells
  const grid = Array.from({ length: 100 }, (_, i) => {
    const isD1 = i < priorD1;
    const isBlack = isD1 ? (i < countD1Black) : (i < priorD1 + countD2Black);
    return { id: i, isD1, isBlack };
  });

  return (
    <div className="mt-6 p-8 bg-slate-900 rounded-[2.5rem] text-white shadow-xl border border-slate-700">
      <div className="flex items-center justify-between mb-6">
        <div className="text-blue-400 font-black text-xs uppercase tracking-widest">
          Probability: Bayesian Update Engine
        </div>
        <button onClick={() => { setPriorD1(50); setD1Black(100); setD2Black(50); }} className="text-[10px] text-slate-400 hover:text-red-400 uppercase tracking-widest font-bold transition-colors">
          Reset Problem
        </button>
      </div>

      <div className="flex flex-col lg:flex-row gap-8">
        
        {/* LEFT COLUMN: Controls & Math */}
        <div className="flex-1 space-y-6">
          {/* Sliders */}
          <div className="bg-slate-800 p-6 rounded-3xl border border-slate-700 space-y-5">
            <div>
              <div className="flex justify-between text-xs font-bold text-slate-300 mb-2 uppercase tracking-widest">
                <span>P(Drawer 1) Prior</span>
                <span className="text-blue-400">{priorD1}%</span>
              </div>
              <input type="range" min="0" max="100" value={priorD1} onChange={(e) => setPriorD1(Number(e.target.value))} className="w-full accent-blue-500" />
            </div>
            <div className="pt-2 border-t border-slate-700">
              <div className="flex justify-between text-xs font-bold text-slate-300 mb-2 uppercase tracking-widest">
                <span>Drawer 1: % Black Balls</span>
                <span className="text-blue-400">{d1Black}%</span>
              </div>
              <input type="range" min="0" max="100" value={d1Black} onChange={(e) => setD1Black(Number(e.target.value))} className="w-full accent-blue-500" />
            </div>
            <div>
              <div className="flex justify-between text-xs font-bold text-slate-300 mb-2 uppercase tracking-widest">
                <span>Drawer 2: % Black Balls</span>
                <span className="text-amber-400">{d2Black}%</span>
              </div>
              <input type="range" min="0" max="100" value={d2Black} onChange={(e) => setD2Black(Number(e.target.value))} className="w-full accent-amber-500" />
            </div>
          </div>

          {/* Analytics Panel */}
          <div className="bg-blue-600 p-6 rounded-3xl shadow-lg shadow-blue-900/20 text-white">
            <div className="text-[10px] text-blue-200 font-black uppercase mb-4 tracking-widest border-b border-blue-500/50 pb-2">
              The Update: "Given we drew a Black ball..."
            </div>
            <div className="flex justify-between items-center mb-3">
              <span className="text-sm font-bold">Valid Sample Space (Total Black)</span>
              <span className="text-xl font-black font-mono">{totalBlack}</span>
            </div>
            <div className="flex justify-between items-center mb-5">
              <span className="text-sm font-bold">Favorable Outcomes (D1 Black)</span>
              <span className="text-xl font-black font-mono">{countD1Black}</span>
            </div>
            <div className="pt-4 border-t border-blue-500/50 flex justify-between items-center">
              <span className="text-sm font-black uppercase tracking-widest">P(Drawer 1 | Black)</span>
              <span className="text-3xl font-black font-mono tracking-tighter">{posteriorD1}%</span>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: 100-Square Area Model */}
        <div className="flex-[1.5] bg-slate-800 p-6 rounded-3xl border border-slate-700 flex flex-col">
          <div className="text-[10px] text-slate-400 font-black uppercase mb-4 tracking-widest flex justify-between">
            <span>Area Model (100 Trials)</span>
            <span>Dimmed = Excluded (White Balls)</span>
          </div>
          
          <div className="flex-1 flex gap-2">
            {/* Drawer 1 Partition */}
            <div className="flex flex-col h-full transition-all duration-300" style={{ width: `${priorD1}%` }}>
              <div className="text-center text-xs font-bold text-blue-400 mb-2 uppercase tracking-widest">Drawer 1</div>
              <div className="flex-1 bg-blue-900/20 border border-blue-500/30 rounded-xl p-2 flex flex-wrap content-start gap-1 overflow-hidden">
                {grid.filter(cell => cell.isD1).map(cell => (
                  <div 
                    key={cell.id} 
                    className={`w-3.5 h-3.5 rounded-full border border-slate-600 transition-all duration-500 ${cell.isBlack ? 'bg-slate-950 scale-100 shadow-md' : 'bg-slate-200 opacity-10 scale-75'}`}
                  />
                ))}
              </div>
            </div>

            {/* Drawer 2 Partition */}
            <div className="flex flex-col h-full transition-all duration-300" style={{ width: `${priorD2}%` }}>
              <div className="text-center text-xs font-bold text-amber-400 mb-2 uppercase tracking-widest">Drawer 2</div>
              <div className="flex-1 bg-amber-900/20 border border-amber-500/30 rounded-xl p-2 flex flex-wrap content-start gap-1 overflow-hidden">
                {grid.filter(cell => !cell.isD1).map(cell => (
                  <div 
                    key={cell.id} 
                    className={`w-3.5 h-3.5 rounded-full border border-slate-600 transition-all duration-500 ${cell.isBlack ? 'bg-slate-950 scale-100 shadow-md' : 'bg-slate-200 opacity-10 scale-75'}`}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>
        
      </div>
    </div>
  );
};

const WidgetDispatcher = ({ tags }) => {
  if (!tags) return null;
  
  if (tags.includes('Options') || tags.includes('Black-Scholes')) return <BlackScholesWidget />;
  if (tags.includes('Indicator Variables')) return <CoinRunsWidget />;  
  if (tags.includes('Expected Value')) return <LawOfLargeNumbersWidget />;
  
  // NEW: Dispatch for the "Maximum of Three" continuous distribution problem
  if (tags.includes('Order Statistics')) return <MaxOfThreeWidget />;
  if (tags.includes("Bayes' Theorem")) return <BayesTheoremWidget />;
  
  return null;
};

// --- MAIN APP ---
const App = () => {
  const [questions, setQuestions] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(null);
  const [showSolution, setShowSolution] = useState(false);
  const [filterStatus, setFilterStatus] = useState('all'); 
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTags, setSelectedTags] = useState([]); 
  const [localNote, setLocalNote] = useState('');
  const [sortOrder, setSortOrder] = useState('easy-to-hard'); 
  
  // NEW: State to toggle taxonomy visibility
  const [isTaxonomyOpen, setIsTaxonomyOpen] = useState(false);

  useEffect(() => {
    const loadData = async () => {
      try {
        const response = await fetch('http://127.0.0.1:5001/get-questions');
        const data = await response.json();
        setQuestions(data.length > 0 ? data : initialData);
      } catch (error) { setQuestions(initialData); }
    };
    loadData();
  }, []);

  const uniqueTags = useMemo(() => {
    const tags = new Set();
    questions.forEach(q => q.tags?.forEach(t => tags.add(t)));
    return Array.from(tags).sort();
  }, [questions]);

  const processedQuestions = useMemo(() => {
    let result = [...questions];
    
    if (searchTerm.trim() !== '') {
      const term = searchTerm.toLowerCase();
      // NEW: Searches ONLY by Title or Tags (Ignores Question body)
      result = result.filter(q => {
        const matchTitle = q.title.toLowerCase().includes(term);
        const matchTags = q.tags?.some(tag => tag.toLowerCase().includes(term));
        return matchTitle || matchTags;
      });
    }
    
    if (filterStatus !== 'all') result = result.filter(q => q.status === filterStatus);
    
    if (selectedTags.length > 0) {
      result = result.filter(q => selectedTags.every(tag => q.tags?.includes(tag)));
    }
    
    const difficultyMap = { Easy: 1, Medium: 2, Hard: 3 };
    if (sortOrder === 'easy-to-hard') result.sort((a, b) => difficultyMap[a.difficulty] - difficultyMap[b.difficulty]);
    else if (sortOrder === 'hard-to-easy') result.sort((a, b) => difficultyMap[b.difficulty] - difficultyMap[a.difficulty]);
    
    return result;
  }, [questions, filterStatus, sortOrder, searchTerm, selectedTags]);

  const stats = useMemo(() => {
    const total = questions.length;
    const solved = questions.filter(q => q.status === 'solved').length;
    return { total, solved, percent: total > 0 ? Math.round((solved / total) * 100) : 0 };
  }, [questions]);

  const saveDataToServer = async (id, updates) => {
    if (updates.status === 'solved') {
      const currentQ = questions.find(q => q.id === id);
      if (currentQ && currentQ.status !== 'solved') {
        confetti({ particleCount: 150, spread: 70, origin: { y: 0.6 }, colors: ['#2563eb', '#10b981', '#f59e0b'] });
      }
    }
    const updated = questions.map(q => q.id === id ? { ...q, ...updates } : q);
    setQuestions(updated);
    try {
      await fetch('http://127.0.0.1:5001/update-status', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updated)
      });
    } catch (e) { console.error("Sync failed"); }
  };

  const handleNext = () => { setCurrentIndex((prev) => (prev + 1) % processedQuestions.length); };
  const handlePrev = () => { setCurrentIndex((prev) => (prev - 1 + processedQuestions.length) % processedQuestions.length); };

  const renderMathContent = (text) => {
    if (!text) return null;
    return text.split('\n').map((line, lineIdx) => (
      <div key={lineIdx} className="min-h-[1.5em]">
        {/* NEW REGEX: Splits by $math$ OR **bold** */}
        {line.split(/(\$.*?\$|\*\*.*?\*\*)/g).map((part, partIdx) => {
          
          // 1. Handle Math
          if (part.startsWith('$') && part.endsWith('$')) {
            return <InlineMath key={partIdx} math={part.slice(1, -1)} />;
          }
          
          // 2. Handle Bold Text
          if (part.startsWith('**') && part.endsWith('**')) {
            return <strong key={partIdx} className="font-black text-gray-900">{part.slice(2, -2)}</strong>;
          }
          
          // 3. Handle Standard Text
          return <span key={partIdx}>{part}</span>;
        })}
      </div>
    ));
  };

  // NEW FIX: Force the solution to close whenever the active question changes
  useEffect(() => {
    setShowSolution(false);
  }, [currentIndex]);

  useEffect(() => {
    if (currentIndex !== null && processedQuestions[currentIndex]) setLocalNote(processedQuestions[currentIndex].notes || '');
  }, [currentIndex, processedQuestions]);

  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      if (currentIndex !== null && localNote !== (processedQuestions[currentIndex].notes || '')) {
        saveDataToServer(processedQuestions[currentIndex].id, { notes: localNote });
      }
    }, 1000);
    return () => clearTimeout(delayDebounceFn);
  }, [localNote]);

  useEffect(() => {
    const handleKeyDown = (e) => {
      // Don't trigger shortcuts if typing in search or scratchpad
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
      
      const key = e.key.toLowerCase();
      
      if (key === 'escape') { setCurrentIndex(null); return; }
      
      if (currentIndex !== null) {
        // --- NEW: Spacebar Logic ---
        if (key === ' ') {
          e.preventDefault(); // Crucial: Stops the page from scrolling down!
          setShowSolution(prev => !prev);
        }
        
        // Existing shortcuts
        if (key === 'arrowright') handleNext();
        if (key === 'arrowleft') handlePrev();
        if (key === 's') setShowSolution(prev => !prev); // Kept 'S' as a backup
        if (key === 'm') saveDataToServer(processedQuestions[currentIndex].id, { status: processedQuestions[currentIndex].status === 'solved' ? 'unsolved' : 'solved' });
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentIndex, processedQuestions]);

  if (questions.length === 0) return <div className="p-10 text-center font-sans">Syncing library...</div>;

  return (
    <div className="min-h-screen bg-gray-50 p-6 font-sans">
      <header className="max-w-9xl mx-auto mb-10">
        <div className="flex justify-between items-center mb-10">
          <div>
            <h1 className="text-4xl font-black tracking-tighter text-gray-900 leading-none">Quant Teasers</h1>
            <p className="text-xs font-bold uppercase text-gray-400 tracking-[0.2em] mt-3">Research & Strategy Lab</p>
          </div>
          <div className="bg-white px-10 py-6 rounded-[2.5rem] shadow-sm border border-gray-100 flex items-center gap-12">
            <div className="text-right">
              <div className="text-[10px] font-black text-gray-300 uppercase tracking-widest mb-1">Solved Portfolio</div>
              <div className="text-3xl font-black text-slate-800">{stats.solved} <span className="text-slate-200">/ {stats.total}</span></div>
            </div>
            <div className="w-64 h-5 bg-gray-100 rounded-full overflow-hidden border border-gray-50 shadow-inner">
              <div className="h-full bg-blue-600 transition-all duration-1000" style={{ width: `${stats.percent}%` }} />
            </div>
          </div>
          {currentIndex !== null && (
            <button onClick={() => setCurrentIndex(null)} className="flex items-center gap-3 bg-white px-10 py-4 rounded-3xl shadow-sm border border-gray-200 text-blue-600 font-black hover:bg-blue-50 transition-all">
              <LayoutGrid size={24} /> Library Grid
            </button>
          )}
        </div>

        {currentIndex === null && (
          <div className="space-y-8">
            <div className="flex gap-6 items-center bg-white p-2 rounded-[3rem] shadow-sm border border-gray-100">
              <div className="relative flex-1">
                <Search className="absolute left-8 top-1/2 -translate-y-1/2 text-gray-300" size={28} />
                <input type="text" placeholder="Filter by Concept..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="w-full pl-20 pr-10 py-3 bg-gray-50 border-none rounded-3xl outline-none font-bold text-xl focus:ring-4 focus:ring-blue-50 transition-all" />
              </div>
              <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)} className="bg-gray-50 border-none text-xs font-black text-gray-500 rounded-3xl px-12 py-7 outline-none cursor-pointer uppercase tracking-widest">
                <option value="all">All Status</option><option value="solved">Solved</option><option value="unsolved">Unsolved</option>
              </select>
              <select value={sortOrder} onChange={(e) => setSortOrder(e.target.value)} className="bg-gray-50 border-none text-xs font-black text-gray-500 rounded-3xl px-12 py-7 outline-none cursor-pointer uppercase tracking-widest">
                <option value="easy-to-hard">Level ↑</option><option value="hard-to-easy">Level ↓</option>
              </select>
            </div>
            
            {/* NEW: Expandable Taxonomy Section */}
            <div className="flex flex-col items-start pl-4 space-y-4">
              <button 
                onClick={() => setIsTaxonomyOpen(!isTaxonomyOpen)}
                className="flex items-center gap-2 text-sm font-black text-gray-400 uppercase tracking-[0.2em] hover:text-blue-600 transition-all"
              >
                <Hash size={18}/> Taxonomy Filter {selectedTags.length > 0 && `(${selectedTags.length} active)`}
                <ChevronRight size={18} className={`transition-transform duration-200 ${isTaxonomyOpen ? 'rotate-90' : ''}`} />
              </button>
              
              {isTaxonomyOpen && (
                <div className="flex flex-wrap gap-4 items-center animate-in slide-in-from-top-2 fade-in duration-200">
                  {uniqueTags.map(tag => (
                    <button key={tag} onClick={() => setSelectedTags(prev => prev.includes(tag) ? prev.filter(t => t !== tag) : [...prev, tag])} className={`px-10 py-5 rounded-2xl text-sm font-black uppercase tracking-widest transition-all border-2 ${selectedTags.includes(tag) ? 'bg-blue-600 border-blue-600 text-white shadow-xl' : 'bg-white border-gray-50 text-gray-400 hover:border-blue-200 hover:text-blue-600'}`}>
                      {tag}
                    </button>
                  ))}
                  {selectedTags.length > 0 && (
                    <button onClick={() => setSelectedTags([])} className="text-sm font-black text-red-400 uppercase tracking-widest ml-2 hover:text-red-600 underline underline-offset-4">
                      Clear Tags
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </header>

      <main className="max-w-9xl mx-auto">
        {currentIndex === null ? (
          /* NEW: lg:grid-cols-6 to show exactly 6 in a row */
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-6">
            {processedQuestions.map((q, index) => (
              <div key={q.id} className="relative group h-full">
                <div onClick={() => setCurrentIndex(index)} className={`p-6 bg-white rounded-[2.5rem] shadow-sm border-2 cursor-pointer transition-all h-full flex flex-col ${q.status === 'solved' ? 'border-green-400 bg-green-50/20' : 'border-white hover:border-blue-400 hover:-translate-y-2'}`}>
                  <div className="flex justify-between items-start mb-6">
                    <span className={`text-[10px] uppercase font-black px-3 py-1.5 rounded-xl border ${q.difficulty === 'Easy' ? 'bg-green-50 text-green-600 border-green-100' : q.difficulty === 'Medium' ? 'bg-yellow-50 text-yellow-600 border-yellow-100' : 'bg-red-50 text-red-600 border-red-100'}`}>{q.difficulty}</span>
                    {q.status === 'solved' && <CheckCircle2 size={20} className="text-green-500" />}
                  </div>
                  <h3 className="text-lg font-bold text-gray-800 leading-tight mb-4">{q.title}</h3>
                  <div className="mt-auto flex flex-wrap gap-2 opacity-80">
                    {q.tags?.slice(0, 2).map(t => <span key={t} className="text-xs bg-slate-100 text-slate-500 px-3 py-1 rounded-xl font-black uppercase tracking-tighter">{t}</span>)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="max-w-9xl mx-auto flex flex-col lg:flex-row gap-12 items-start">
            <div className="flex-[1.5] bg-white p-12 md:p-16 rounded-[4rem] shadow-2xl border border-gray-100 min-h-[600px]">
              <div className="flex justify-between items-center mb-10">
                <div className="flex gap-4">
                  {processedQuestions[currentIndex].tags?.map(t => <span key={t} className="text-xs bg-blue-50 text-blue-600 px-6 py-3 rounded-2xl font-black uppercase tracking-widest">{t}</span>)}
                </div>
                <button onClick={() => saveDataToServer(processedQuestions[currentIndex].id, { status: processedQuestions[currentIndex].status === 'solved' ? 'unsolved' : 'solved' })} className={`flex items-center gap-3 text-xs font-black uppercase tracking-widest ${processedQuestions[currentIndex].status === 'solved' ? 'text-green-600' : 'text-gray-300'}`}>
                  {processedQuestions[currentIndex].status === 'solved' ? <CheckCircle2 size={36} /> : <Circle size={36} />} Solved (M)
                </button>
              </div>

              <div className="text-2xl text-gray-800 mb-12 leading-relaxed font-bold">
                {renderMathContent(processedQuestions[currentIndex].question)}
              </div>

              {processedQuestions[currentIndex].link && (
                <a href={processedQuestions[currentIndex].link} target="_blank" rel="noreferrer" className="inline-flex items-center gap-4 text-xs font-black uppercase tracking-[0.2em] text-blue-500 bg-blue-50 px-10 py-5 rounded-2xl hover:bg-blue-100 transition-all mb-12">
                  Source<ExternalLink size={20} />
                </a>
              )}

              <div className="space-y-12">
              <button onClick={() => setShowSolution(!showSolution)} className="w-fit mx-auto px-12 py-4 bg-blue-400 text-white rounded-[20.5rem] text-2xl font-black flex justify-center items-center gap-6 shadow-2xl shadow-blue-400 hover:scale-[1.01] active:scale-95 transition-all">
                {showSolution ? <EyeOff size={36} /> : <Eye size={36} />} View Solution
              </button>
                
                {showSolution && (
                  <div className="p-12 bg-slate-50 border-l-[12px] border-blue-600 text-slate-800 rounded-r-[3rem] animate-in slide-in-from-top-6 duration-500">
                    <div className="text-lg leading-loose whitespace-pre-wrap font-bold">
                      {renderMathContent(processedQuestions[currentIndex].solution)}
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="flex-1 w-full space-y-10">
              <div className="bg-amber-50 p-12 rounded-[4rem] border-2 border-amber-100 shadow-xl">
                <div className="flex items-center gap-4 mb-8 text-amber-600 font-black text-xs uppercase tracking-widest">
                  <PenTool size={24} /> Research & Derivation Pad
                </div>
                <textarea 
                  value={localNote} 
                  onChange={(e) => setLocalNote(e.target.value)} 
                  placeholder="Define states, build recurrences, or sketch probability trees..." 
                  className="w-full h-[450px] p-8 bg-white border-2 border-amber-100 rounded-[3rem] text-gray-700 font-mono text-sm outline-none resize-none shadow-inner focus:border-amber-300 transition-all" 
                />
              </div>

              <WidgetDispatcher tags={processedQuestions[currentIndex].tags} />

              <div className="flex gap-5">
                <button onClick={handlePrev} className="flex-1 flex justify-center items-center gap-2 py-4 bg-white border-2 border-slate-100 text-slate-400 rounded-2xl font-bold uppercase text-xs tracking-widest hover:bg-slate-50 hover:text-slate-600 hover:border-slate-200 transition-all active:scale-95">
                  <ChevronLeft size={20} /> Prev
                </button>
                <button onClick={handleNext} className="flex-1 flex justify-center items-center gap-2 py-4 bg-slate-900 text-white rounded-2xl font-bold uppercase text-xs tracking-widest shadow-lg shadow-slate-200 hover:bg-black hover:shadow-xl transition-all active:scale-95">
                  Next Teaser <ChevronRight size={20} />
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default App;