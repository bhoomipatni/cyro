import React, { useEffect, useState } from 'react'
import { MapContainer, TileLayer, Circle, Marker, Popup, useMap, useMapEvents } from 'react-leaflet'
import L from 'leaflet'
import HeatmapLayer from './HeatmapLayer'
import RiskZonesLayer from './RiskZonesLayer'
import axios from 'axios'
import './MapView.css'

// Fix for default marker icons in React-Leaflet
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

// Police station icon
const policeIcon = new L.Icon({
    iconUrl: 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSIjMDA3OGQ0Ij48cGF0aCBkPSJNMTIgMkw0IDVWMTFDNCAxNi41NSA3LjgzIDIxLjc0IDEyIDIzQzE2LjE3IDIxLjc0IDIwIDE2LjU1IDIwIDExVjVMMTIgMk0xMiA1QzEzLjEgNSAxNCAwNS45IDE0IDdDMTQgOC4xIDEzLjEgOSAxMiA5QzEwLjkgOSAxMCA4LjEgMTAgN0MxMCA1LjkgMTAuOSA1IDEyIDVNMTYuMTMgMTQuNjRDMTQuNzYgMTYuNzUgMTMuNDUgMTggMTIgMThDMTAuNTUgMTggOS4yNCAxNi43NSA3Ljg3IDE0LjY0QzcuNTEgMTQuMTcgNy4yOCAxMy42MyA3LjEyIDEzLjA2QzguNDQgMTEuODQgMTAuMTEgMTEgMTIgMTFDMTMuODkgMTEgMTUuNTYgMTEuODQgMTYuODggMTMuMDZDMTYuNzIgMTMuNjMgMTYuNDkgMTQuMTcgMTYuMTMgMTQuNjRaIi8+PC9zdmc+',
    iconSize: [32, 32],
    iconAnchor: [16, 32],
    popupAnchor: [0, -32]
})

// Map click handler component
function MapClickHandler({ onMapClick }) {
    useMapEvents({
        click: (e) => {
            onMapClick({ lat: e.latlng.lat, lng: e.latlng.lng })
        }
    })
    return null
}

function MapFlyTo({ center, radius }) {
    const map = useMap()

    useEffect(() => {
        if (!center) return
        let zoom = 13
        if (radius <= 1) zoom = 14
        else if (radius <= 2) zoom = 13
        else if (radius <= 5) zoom = 12
        else if (radius <= 10) zoom = 11
        else if (radius <= 20) zoom = 10
        else if (radius <= 30) zoom = 9
        else zoom = 8

        map.setView([center.lat, center.lng], zoom, { animate: true })
    }, [center, radius, map])

    return null
}

function MapView({ center, radius, showHeatmap, onMapClick }) {
    const [riskZones, setRiskZones] = useState([])
    const [policeStations, setPoliceStations] = useState([])
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [highlightRisk, setHighlightRisk] = useState(null)

    // Fetch risk zones
    useEffect(() => {
        const fetchRiskZones = async () => {
            setLoading(true)
            setError(null)

            try {
                const response = await axios.get('http://localhost:8000/api/risk-zones', {
                    params: {
                        lat: center.lat,
                        lon: center.lng,
                        radius: radius
                    }
                })
                setRiskZones(response.data)
            } catch (err) {
                console.error('Error fetching risk zones:', err)
                setError('Failed to load risk data. Is the backend running?')
                setRiskZones([])
            } finally {
                setLoading(false)
            }
        }

        fetchRiskZones()
    }, [center, radius])

    // Fetch risk at selected point (for search highlight)
    useEffect(() => {
        const fetchRiskAtPoint = async () => {
            try {
                const response = await axios.get('http://localhost:8000/api/risk-at-point', {
                    params: {
                        lat: center.lat,
                        lon: center.lng
                    }
                })
                setHighlightRisk(response.data)
            } catch (err) {
                console.error('Error fetching risk at point:', err)
                setHighlightRisk(null)
            }
        }

        if (center) {
            fetchRiskAtPoint()
        }
    }, [center])

    // Fetch police stations
    useEffect(() => {
        const fetchPoliceStations = async () => {
            // Calculate bounding box
            const latOffset = radius / 69 // ~69 miles per degree latitude
            const lonOffset = radius / (69 * Math.cos(center.lat * Math.PI / 180))

            try {
                const response = await axios.get('http://localhost:8000/api/police-stations', {
                    params: {
                        min_lat: center.lat - latOffset,
                        max_lat: center.lat + latOffset,
                        min_lon: center.lng - lonOffset,
                        max_lon: center.lng + lonOffset
                    }
                })
                setPoliceStations(response.data)
            } catch (err) {
                console.error('Error fetching police stations:', err)
            }
        }

        fetchPoliceStations()
    }, [center, radius])

    // Convert radius from miles to meters for Leaflet
    const radiusInMeters = radius * 1609.34

    // Get color for risk level
    const getRiskColor = (level) => {
        switch (level) {
            case 'Low': return '#27ae60'
            case 'Medium': return '#f39c12'
            case 'High': return '#e74c3c'
            default: return '#95a5a6'
        }
    }

    return (
        <div className="map-container">
            {loading && (
                <div className="map-loading">
                    <div className="spinner"></div>
                    <p>Loading risk data...</p>
                </div>
            )}

            {error && (
                <div className="map-error">
                    <p>{error}</p>
                </div>
            )}

            <MapContainer
                center={[center.lat, center.lng]}
                zoom={12}
                className="map"
                key={`${center.lat}-${center.lng}`}
            >
                <MapFlyTo center={center} radius={radius} />
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />

                <MapClickHandler onMapClick={onMapClick} />

                {/* Search radius circle */}
                <Circle
                    center={[center.lat, center.lng]}
                    radius={radiusInMeters}
                    pathOptions={{
                        color: '#3498db',
                        fillColor: '#3498db',
                        fillOpacity: 0.1,
                        weight: 2,
                        dashArray: '5, 5'
                    }}
                />

                {/* Center marker */}
                <Marker position={[center.lat, center.lng]}>
                    <Popup>
                        <strong>Search Center</strong>
                        <br />
                        Lat: {center.lat.toFixed(4)}
                        <br />
                        Lng: {center.lng.toFixed(4)}
                    </Popup>
                </Marker>

                {/* Risk zones for entire Capital Region */}
                <RiskZonesLayer />

                {/* Heatmap (kept for optional use) */}
                {showHeatmap && riskZones.length > 0 && (
                    <HeatmapLayer zones={riskZones} />
                )}

                {/* Highlight searched point risk */}
                {highlightRisk && (
                    <Circle
                        center={[center.lat, center.lng]}
                        radius={350}
                        pathOptions={{
                            color: getRiskColor(highlightRisk.risk_level),
                            fillColor: getRiskColor(highlightRisk.risk_level),
                            fillOpacity: 0.45,
                            stroke: false
                        }}
                    >
                        <Popup>
                            <div className="risk-popup">
                                <h3>{highlightRisk.risk_level} Risk</h3>
                                <p><strong>Score:</strong> {highlightRisk.risk_score.toFixed(1)}/100</p>
                                <p><strong>Nearest Cell:</strong> {highlightRisk.cell_id}</p>
                            </div>
                        </Popup>
                    </Circle>
                )}

                {/* Risk zone circles */}
                {!showHeatmap && riskZones.map((zone) => (
                    <Circle
                        key={zone.cell_id}
                        center={[zone.center_lat, zone.center_lon]}
                        radius={100}
                        pathOptions={{
                            color: getRiskColor(zone.risk_level),
                            fillColor: getRiskColor(zone.risk_level),
                            fillOpacity: 0.4,
                            weight: 1
                        }}
                    >
                        <Popup>
                            <div className="risk-popup">
                                <h3>{zone.risk_level} Risk</h3>
                                <p><strong>Score:</strong> {zone.risk_score.toFixed(1)}/100</p>
                                <p><strong>Location:</strong> {zone.center_lat.toFixed(4)}, {zone.center_lon.toFixed(4)}</p>
                                <p className="popup-note">
                                    Click for detailed factors
                                </p>
                            </div>
                        </Popup>
                    </Circle>
                ))}

                {/* Police stations */}
                {policeStations.map((station) => (
                    <Marker
                        key={station.station_id}
                        position={[station.latitude, station.longitude]}
                        icon={policeIcon}
                    >
                        <Popup>
                            <div className="police-popup">
                                <h3>🚔 {station.name}</h3>
                                {station.address && <p>{station.address}</p>}
                            </div>
                        </Popup>
                    </Marker>
                ))}
            </MapContainer>
        </div>
    )
}

export default MapView
