import { useEffect } from 'react'
import { useMap } from 'react-leaflet'
import L from 'leaflet'
import axios from 'axios'

function RiskZonesLayer() {
    const map = useMap()

    useEffect(() => {
        // Load all risk zones for entire Capital Region
        const loadAllRiskZones = async () => {
            try {
                // Use a large center point and massive radius to get entire region
                const response = await axios.get('http://localhost:8000/api/risk-zones', {
                    params: {
                        lat: 42.8,
                        lon: -73.7,
                        radius: 50  // 50 miles covers entire Capital Region
                    }
                })

                const zones = response.data
                console.log(`Loaded ${zones.length} risk zones for Capital Region`)

                // Create circle markers for each zone
                const circleGroup = L.featureGroup()

                zones.forEach(zone => {
                    let color
                    if (zone.risk_level === 'High') {
                        color = '#c0392b'  // Dark red
                    } else if (zone.risk_level === 'Medium') {
                        color = '#e67e22'  // Dark orange
                    } else {
                        color = '#1abc9c'  // Teal
                    }

                    // Create circle marker
                    const circle = L.circleMarker(
                        [zone.center_lat, zone.center_lon],
                        {
                            radius: 25,
                            fillColor: color,
                            color: color,
                            weight: 2,
                            opacity: 1,
                            fillOpacity: 0.5
                        }
                    )

                    // Add popup with risk info
                    circle.bindPopup(`
                        <strong>Risk Score: ${zone.risk_score.toFixed(1)}</strong><br/>
                        Level: ${zone.risk_level}<br/>
                        Cell: ${zone.cell_id}
                    `)

                    circleGroup.addLayer(circle)
                })

                // Add to map
                circleGroup.addTo(map)

                // Cleanup
                return () => {
                    map.removeLayer(circleGroup)
                }
            } catch (error) {
                console.error('Error loading risk zones:', error)
            }
        }

        loadAllRiskZones()
    }, [map])

    return null
}

export default RiskZonesLayer
