import { useState, useEffect, useCallback } from "react";
import HeatmapUI from "./heatmapUI"; 
import applicationConfig from "./config/applicationConfig";

const Heatmap = () => {
    const [heatmapData, setHeatmapData] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    
    // Config options
    const options = applicationConfig.heatmapDropdownOptions || ["SECTORAL INDICES", "NIFTY 50", "BANK NIFTY"];
    const [selectedOption, setSelectedOption] = useState("SECTORAL INDICES");

    // Memoized fetch function to prevent infinite loops
    const fetchHeatmapData = useCallback(async (heatmapName) => {
      setLoading(true);
      setError(null);
      try {
          const response = await fetch(`api/fetchHeatmapData?heatmap=${heatmapName}`);
          if (!response.ok) throw new Error("Failed to connect to server");
          const responseData = await response.json();
          if (!responseData) throw new Error("No data received");
          const formattedData = Object.entries(responseData);
          const sortedData = formattedData.sort((a, b) => b[1][1] - a[1][1]);
          
          setHeatmapData(sortedData);
      } catch (err) {
          console.error("Error:", err);
          setError("Failed to load market data.");
      } finally {
          setLoading(false);
      }
    }, []);

    // Initial Load
    useEffect(() => {
        fetchHeatmapData(selectedOption);
    }, [fetchHeatmapData, selectedOption]);

    const handleDropdownChange = (e) => {
        setSelectedOption(e.target.value);
    };

    const handleTileClick = (indexName) => {
        if (options.includes(indexName)) {
            setSelectedOption(indexName);
        }
    };

    return (
        <HeatmapUI
            heatmapData={heatmapData}
            loading={loading}
            error={error}
            options={options}
            selectedOption={selectedOption}
            handleDropdownChange={handleDropdownChange}
            handleTileClick={handleTileClick}
        />
    );
};

export default Heatmap;
