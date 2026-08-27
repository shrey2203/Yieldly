import { AgGridReact } from "ag-grid-react";

const AnalysisUI = ({ gridRef, themeDarkBlue, analysisData, columnDefs, defaultColDef, ClientSideRowModelModule, searchQuery, setSearchQuery, handleSearch, handleKeyDown}) => (
    <div className="portfolioPage" style={{ height: "90vh", width: "99vw" }}>
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "10px", position: "relative" }}>
        
        {/* Center: Title */}
        <h2 style={{ 
            margin: 0, 
            position: "absolute", 
            left: "50%", 
            transform: "translateX(-50%)" 
        }}>
            ANALYSIS
        </h2>

        {/* Right: Search Bar */}
        <div>
            <input 
                type="text" 
                placeholder="Search stock for analysis..." 
                value={searchQuery} 
                onChange={(e) => setSearchQuery(e.target.value)} 
                onKeyDown={handleKeyDown}
                style={{
                    padding: "5px",
                    borderRadius: "5px",
                    border: "1px solid #ccc",
                    outline: "none",
                    width: "200px"
                }}
            />
            <button onClick={handleSearch} style={{ padding: "5px 10px", cursor: "pointer" }}>Search</button>
        </div>
    </div>


        <AgGridReact 
            ref={gridRef}
            theme={themeDarkBlue}
            rowData={analysisData}
            defaultColDef={defaultColDef}
            pagination={true} 
            paginationPageSize={100} 
            rowSelection="multiple"
            animateRows={true}
            modules={[ClientSideRowModelModule]} 
            columnDefs={columnDefs}
        />
    </div>
);

export default AnalysisUI;
