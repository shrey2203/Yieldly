import { useState, useEffect, useMemo, useRef } from "react";
import { ModuleRegistry, ClientSideRowModelModule } from "ag-grid-community";
import { AllCommunityModule } from 'ag-grid-community';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import AnalysisUI from "./analysisUI"; 
import "./analysis.css"; // Ensure this imports styles similar to mutualFund.css

ModuleRegistry.registerModules([ClientSideRowModelModule, AllCommunityModule]);

const Analysis = () => {
    const [loading, setLoading] = useState(false);
    const [searchQuery, setSearchQuery] = useState("");
    const [analysisData, setAnalysisData] = useState([]);
    
    // Summary state to match the MF card format
    const [summary, setSummary] = useState({
        totalStocks: 0,
        avgFii: 0,
        avgDii: 0,
        topGainer: "N/A"
    });

    const gridRef = useRef();

    // Calculate summary whenever data changes
    useEffect(() => {
        if (analysisData.length > 0) {
            const avgFii = analysisData.reduce((acc, curr) => acc + curr.fiiHolding, 0) / analysisData.length;
            const avgDii = analysisData.reduce((acc, curr) => acc + curr.diiHolding, 0) / analysisData.length;
            const top = [...analysisData].sort((a, b) => b.fiiHolding - a.fiiHolding)[0];

            setSummary({
                totalStocks: analysisData.length,
                avgFii: avgFii.toFixed(2),
                avgDii: avgDii.toFixed(2),
                topGainer: top.stock
            });
        }
    }, [analysisData]);

    const columnDefs = useMemo(() => [
        { headerName: "Scrip", field: "stock", flex: 2, checkboxSelection: true },
        { 
            headerName: "FII Holding", 
            field: "fiiHolding", 
            valueFormatter: p => `${p.value}%`,
            cellStyle: p => ({ color: p.value > 15 ? "#10b981" : "#ef4444", fontWeight: "bold" })
        },
        { 
            headerName: "DII Holding", 
            field: "diiHolding", 
            valueFormatter: p => `${p.value}%`,
            cellStyle: p => ({ color: p.value > 15 ? "#10b981" : "#ef4444", fontWeight: "bold" })
        },
        {
          headerName: "Total Institutional",
          flex: 1,
          // Use Number() to cast strings to numbers and || 0 to handle null/undefined
          valueGetter: p => {
              const fii = Number(p.data?.fiiHolding) || 0;
              const dii = Number(p.data?.diiHolding) || 0;
              return (fii + dii).toFixed(2) + "%";
          }
        }
    ], []);

    const handleSearch = async () => {
        if (!searchQuery.trim()) return;
        setLoading(true);
        try {
            const response = await fetch(`api/fetchStockAnalysis?stock=${searchQuery.toUpperCase()}`);
            const stockData = await response.json();
            
            const newEntry = {
                stock: searchQuery.toUpperCase(),
                fiiHolding: parseFloat(stockData[0]) || 0,
                diiHolding: parseFloat(stockData[1]) || 0,
                history: [ // Mocking trend data for the chart
                    { month: 'Jan', val: (stockData[0] || 0) - 2 },
                    { month: 'Feb', val: (stockData[0] || 0) - 1 },
                    { month: 'Mar', val: (stockData[0] || 0) }
                ]
            };
            setAnalysisData(prev => [newEntry, ...prev]);
            setSearchQuery("");
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <AnalysisUI
            loading={loading}
            summary={summary}
            analysisData={analysisData}
            columnDefs={columnDefs}
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
            handleSearch={handleSearch}
            gridRef={gridRef}
        />
    );
};

export default Analysis;

