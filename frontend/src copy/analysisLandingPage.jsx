import { useState, useEffect, useMemo, useRef } from "react";
import { AllCommunityModule, ModuleRegistry, ClientSideRowModelModule} from "ag-grid-community";
import { themeAlpine, themeBalham, themeQuartz, themeMaterial} from 'ag-grid-community';
import { colorSchemeDarkBlue, colorSchemeDarkWarm, colorSchemeLightCold, colorSchemeLightWarm, colorSchemeDark} from 'ag-grid-community';
import { RowGroupingModule } from "ag-grid-enterprise";
import "./analysis.css";
import AnalysisUI from "./analysisUI"; 
ModuleRegistry.registerModules([ClientSideRowModelModule, AllCommunityModule,RowGroupingModule]);

const Analysis = () => {
    const [analysisData, setanalysisData] = useState([]);
    const [error, setError] = useState(null);
    const themeLightWarm = themeBalham.withPart(colorSchemeLightWarm);
    const themeLightCold = themeBalham.withPart(colorSchemeLightCold);
    const themeDarkWarm = themeBalham.withPart(colorSchemeDarkWarm);
    const themeDarkBlue = themeBalham.withPart(colorSchemeDarkBlue);
    const matrixTheme = themeAlpine
        .withPart(colorSchemeDark)
        .withParams({
            backgroundColor: '#000000',
            foregroundColor: '#00ff41',       
            accentColor: '#008f11',         
            borderColor: '#003b00',           
            chromeBackgroundColor: '#000000',
            headerTextColor: '#00ff41',
            fontFamily: 'Courier New, monospace', 
            iconColor: '#00ff41',            
        });
    const gridRef = useRef();
    const [searchQuery, setSearchQuery] = useState("");
        
      const [columnDefs] = useState([
        { field: "stock", headerName: "Scrip"},
        { field: "fiiHolding", headerName: "FII Holding"},
        { field: "diiHolding", headerName: "DII Holding"}
        ]);

      const defaultColDef = useMemo(() => ({
        resizable: true,
        sortable: true,
        filter: true,
        flex: 1
      }), []);

      const handleSearch = async() => {
        if (!searchQuery.trim()) return;  

        const stockExists = analysisData.some(row => row.stock.toLowerCase() === searchQuery.toLowerCase());
        if (stockExists) return;
        setSearchQuery("");
        try {
          const response = await fetch(`api/fetchStockAnalysis?stock=${searchQuery}`);
          const stockData = await response.json();
  
          if (!stockData) throw new Error("Stock data not found");
          const newStockEntry = {
            stock: stockData.symbol || searchQuery.toUpperCase(),
            fiiHolding: stockData[0], 
            diiHolding: stockData[1]
          };
          setanalysisData(prevData => [...prevData, newStockEntry]);
        }catch (error) {
          console.error("Error fetching stock data:", error);
          alert("Failed to retrieve stock data. Please try again.");
        }
      };

      const handleKeyDown = (event) => {
        if (event.key === "Enter") {
          handleSearch();
        }
      };

    if (error) return <p>{error}</p>;


    return <AnalysisUI
            gridRef={gridRef}
            themeDarkBlue={matrixTheme}
            analysisData={analysisData}
            columnDefs={columnDefs}
            defaultColDef={defaultColDef}
            ClientSideRowModelModule={ClientSideRowModelModule}
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
            handleSearch={handleSearch}
            handleKeyDown={handleKeyDown}
          />
};

export default Analysis; 