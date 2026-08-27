import { AgGridReact } from "ag-grid-react";

const ReportsUI = ({ 
    gridRef, themeDarkBlue, reportOptions, columnDefs, 
    defaultColDef, triggerReport, isGenerating 
}) => {
    return (
        <div className="reports-dark-container"> {/* This is now Cream */}
              <div className="reports-content">
                <div className="header-section-centered">
                    <h1 className="main-title-glass">Portfolio Reports</h1>
                    <p className="subtitle-glass">Select a report to dispatch</p>
                </div>

                <div className="grid-card-glass">
                    <div className="grid-header-dark">
                        <span className="dot"></span>
                        <h3>Report Selection Menu</h3>
                    </div>
                    
                    <div style={{ height: "650px", width: "100%" }}>
                        <AgGridReact
                            ref={gridRef}
                            theme={themeDarkBlue} // Using the Dark Blue Theme
                            rowData={reportOptions}
                            columnDefs={columnDefs}
                            defaultColDef={defaultColDef}
                        />
                    </div>
                </div>
                
                <p className="footer-note">All reports are generated in real-time using the latest market data.</p>
            </div>
        </div>
    );
};

export default ReportsUI;
