import React, { useState } from 'react'
import MapView from './components/MapView'
import ControlPanel from './components/ControlPanel'
import Legend from './components/Legend'
import './App.css'

function App() {
    const [center, setCenter] = useState({ lat: 42.6526, lng: -73.7562 }) // Albany, NY
    const [radius, setRadius] = useState(2) // miles
    const [selectedAddress, setSelectedAddress] = useState('')
    const [showHeatmap, setShowHeatmap] = useState(true)

    return (
        <div className="app">
            <header className="app-header">
                <img src="/logo.png" alt="CYRO Logo" className="app-logo" />
                <p className="subtitle">Crime Yield & Reporting Overview · Capital Region, NY</p>
            </header>

            <ControlPanel
                radius={radius}
                onRadiusChange={setRadius}
                selectedAddress={selectedAddress}
                onAddressChange={setSelectedAddress}
                onLocationSelect={setCenter}
                showHeatmap={showHeatmap}
                onToggleHeatmap={setShowHeatmap}
            />

            <MapView
                center={center}
                radius={radius}
                showHeatmap={showHeatmap}
                onMapClick={setCenter}
            />

            <Legend />
        </div>
    )
}

export default App
