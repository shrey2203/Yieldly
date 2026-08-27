import { useState, useMemo, useRef, useCallback } from "react";
import { ModuleRegistry, ClientSideRowModelModule } from "ag-grid-community";
import { themeBalham, colorSchemeDarkBlue } from 'ag-grid-community';
import "./reports.css";
import ReportsUI from "./ReportsUI";

ModuleRegistry.registerModules([ClientSideRowModelModule]);

/**
 * 1. DEFINE OUTSIDE
 * This prevents the input from losing focus/re-mounting on every keystroke.
 */
const RecipientInput = ({ params, recipientEmails, setRecipientEmails }) => {
    // Local state for snappy typing
    const [localValue, setLocalValue] = useState(recipientEmails[params.data.id] || "");

    const handleChange = (e) => {
        const val = e.target.value;
        setLocalValue(val);
    };

    // Commit to global state when user finishes typing or clicks away
    const handleBlur = () => {
        setRecipientEmails(prev => ({
            ...prev,
            [params.data.id]: localValue
        }));
    };

    return (
        <input 
            type="text" 
            className="grid-email-input"
            value={localValue}
            onChange={handleChange}
            onBlur={handleBlur}
            onKeyDown={e => e.stopPropagation()} 
            placeholder="Names..."
            style={{ width: '95%', padding: '4px', color: 'black', border: '1px solid #ccc', borderRadius: '4px' }}
        />
    );
};

const Reports = () => {
    const [isGenerating, setIsGenerating] = useState(false);
    const [recipientEmails, setRecipientEmails] = useState({});
    const gridRef = useRef();
    const userId = localStorage.getItem("username");
    const themeDarkBlue = themeBalham.withPart(colorSchemeDarkBlue).withParams({ accentColor: "red" });

    const [reportOptions] = useState([
        { id: 'combined_equity_mf', reportName: "Unified Portfolio Analytics", description: "A comprehensive view of total net worth, aggregating Equity and Mutual Fund performance to track cross-asset growth and unified daily P&L." },
        { id: 'equity_daily_total', reportName: "Consolidated Equity Dynamics", description: "A high-level daily summary of equity performance, isolating market volatility from capital movements to show true portfolio growth." },
        { id: 'equity_daily_user', reportName: "User-Wise Equity Performance", description: "Detailed daily P&L breakdown segmented by individual user accounts, enabling performance benchmarking and account-level auditing." },
        { id: 'mf_daily_total', reportName: "Mutual Fund Growth Summary", description: "Time-series analysis of Mutual Fund NAV fluctuations, providing daily insights into fund performance and cumulative investment returns." },
        { id: 'mf_daily_user', reportName: "Daily MF Performance (User-wise)", description: "Granular daily P&L breakdown separated by individual user accounts." },
        { id: 'mf_monthly_total', reportName: "Monthly Portfolio Performance", description: "Summary of monthly growth and value appreciation." },
        { id: 'mf_monthly_user', reportName: "Monthly Performance (User-wise)", description: "User-specific monthly performance tracking." },
        { id: 'mf_yearly_total', reportName: "Yearly Portfolio Performance", description: "Fiscal year-to-date (YTD) performance summaries." },
        { id: 'mf_yearly_user', reportName: "Yearly Performance (User-wise)", description: "Long-term yearly growth metrics categorized by account holder." },
        { id: 'mf_transactions_master', reportName: "Transactions Master Ledger", description: "Complete historical log of all transactions." }    
    ]);

    /**
     * 2. TRIGGER REPORT
     * Wrapped in useCallback to stay stable
     */
    const triggerReport = useCallback(async (reportId) => {
        // Look up the value from the state
        const recipientsList = recipientEmails[reportId] || ""; 
        
        console.log("Attempting dispatch for ID:", reportId, "Recipients:", recipientsList);

        setIsGenerating(true);
        try {
            const encodedRecipients = encodeURIComponent(recipientsList);
            const response = await fetch(
                `api/fetchReports?userId=${userId}&reportId=${reportId}&sendTo=${encodedRecipients}`,
                { headers: { Authorization: `Bearer ${localStorage.getItem("token")}` } }
            );
            if (response.ok) {
                alert(recipientsList === "" ? "Sent to default recipient!" : `Sent to: ${recipientsList}`);
            } else {
                const result = await response.json();
                throw new Error(result.message || "Server failed");
            }
        } catch (error) {
            console.error("Report Dispatch Error:", error);
            alert("Error: " + error.message);
        } finally {
            setIsGenerating(false);
        }
    }, [recipientEmails, userId]); // Dependencies are vital here!

    /**
     * 3. COLUMN DEFS WITH MEMO
     * We pass recipientEmails to the dependency array so the 'Action' 
     * button always has the latest data when clicked.
     */
    const columnDefs = useMemo(() => [
        { 
            field: "reportName", 
            headerName: "Report Title", 
            flex: 2,
            cellStyle: { fontWeight: '900', display: 'flex', alignItems: 'center' } 
        },
        { 
            field: "description", 
            headerName: "Description", 
            flex: 3,
            cellStyle: { textAlign: 'left', display: 'flex', alignItems: 'center' }
        },
        { 
            headerName: "Recipient Names", 
            flex: 2,
            cellRenderer: (params) => (
                <RecipientInput 
                    params={params} 
                    recipientEmails={recipientEmails} 
                    setRecipientEmails={setRecipientEmails} 
                />
            )
        },
        { 
            headerName: "Action", 
            flex: 1,
            cellRenderer: (params) => (
                <button 
                    className="grid-dispatch-btn"
                    onClick={() => triggerReport(params.data.id)}
                    disabled={isGenerating}
                >
                    {isGenerating ? "..." : "📧 Dispatch"}
                </button>
            )
        }     
    ], [recipientEmails, isGenerating, triggerReport]);

    const defaultColDef = useMemo(() => ({
        resizable: true,
        sortable: true,
        filter: true,
    }), []);

    return (
        <ReportsUI
            gridRef={gridRef}
            themeLightWarm={themeDarkBlue}
            reportOptions={reportOptions}
            columnDefs={columnDefs}
            defaultColDef={defaultColDef}
            isGenerating={isGenerating}
        />
    );
};

export default Reports;