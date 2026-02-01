import React, { useState } from 'react'
import axios from 'axios'
import RiskTrendChart from './RiskTrendChart'
import './ControlPanel.css'

function ControlPanel({
    radius,
    onRadiusChange,
    selectedAddress,
    onAddressChange,
    onLocationSelect,
    showHeatmap,
    onToggleHeatmap
}) {
    const [searchResults, setSearchResults] = useState([])
    const [searching, setSearching] = useState(false)
    const [selectedLat, setSelectedLat] = useState(null)
    const [selectedLon, setSelectedLon] = useState(null)

    // Search for address using backend geocoding proxy
    const handleAddressSearch = async () => {
        if (!selectedAddress.trim()) return

        setSearching(true)
        try {
            // Use backend proxy to avoid CORS issues
            const response = await axios.get('http://localhost:8000/api/geocode', {
                params: {
                    q: selectedAddress
                }
            })

            console.log('Search results:', response.data)
            if (response.data && response.data.length > 0) {
                setSearchResults(response.data)
            } else {
                alert('No locations found. Try a different address.')
                setSearchResults([])
            }
        } catch (error) {
            console.error('Geocoding error:', error)
            alert('Search failed. Please try again.')
        } finally {
            setSearching(false)
        }
    }

    const handleSelectResult = (result) => {
        const lat = parseFloat(result.lat)
        const lon = parseFloat(result.lon)
        setSelectedLat(lat)
        setSelectedLon(lon)
        onLocationSelect({
            lat: lat,
            lng: lon
        })
        setSearchResults([])
        onAddressChange(result.display_name)
    }

    const handleKeyPress = (e) => {
        if (e.key === 'Enter') {
            handleAddressSearch()
        }
    }

    return (
        <div className="control-panel">
            <div className="control-section">
                <label className="control-label">
                    <span className="label-icon"></span>
                    Search Address
                </label>
                <div className="search-box">
                    <input
                        type="text"
                        className="search-input"
                        placeholder="Enter address in Capital Region, NY"
                        value={selectedAddress}
                        onChange={(e) => onAddressChange(e.target.value)}
                        onKeyPress={handleKeyPress}
                    />
                    <button
                        className="search-button"
                        onClick={handleAddressSearch}
                        disabled={searching || !selectedAddress.trim()}
                    >
                        {searching ? '⏳' : '🔍'}
                    </button>
                </div>

                {/* Search results dropdown */}
                {searchResults.length > 0 && (
                    <div className="search-results">
                        {searchResults.map((result, index) => (
                            <div
                                key={index}
                                className="search-result-item"
                                onClick={() => handleSelectResult(result)}
                            >
                                <span className="result-icon"></span>
                                <span className="result-text">{result.display_name}</span>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            <div className="control-section">
                <label className="control-label">
                    <span className="label-icon"></span>
                    Search Radius: {radius} mile{radius !== 1 ? 's' : ''}
                </label>
                <input
                    type="range"
                    className="radius-slider"
                    min="0.5"
                    max="50"
                    step="0.5"
                    value={radius}
                    onChange={(e) => onRadiusChange(parseFloat(e.target.value))}
                />
                <div className="slider-labels">
                    <span>0.5 mi</span>
                    <span>50 mi</span>
                </div>
            </div>

            <div className="control-section">
                <label className="control-label">
                </label>
                <div className="toggle-group">
                    <button
                        className={`toggle-button ${showHeatmap ? 'active' : ''}`}
                        onClick={() => onToggleHeatmap(true)}
                    >
                        Heatmap
                    </button>
                    <button
                        className={`toggle-button ${!showHeatmap ? 'active' : ''}`}
                        onClick={() => onToggleHeatmap(false)}
                    >
                        Zones
                    </button>
                </div>
            </div>

            <div className="control-hint">
                Click anywhere on the map to set a new search center.
            </div>

            {/* Risk Trend Chart */}
            <RiskTrendChart lat={selectedLat} lon={selectedLon} />
        </div>
    )
}

export default ControlPanel
