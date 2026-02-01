import { useEffect } from 'react'
import { useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet.heat'

function HeatmapLayer({ zones }) {
    const map = useMap()

    useEffect(() => {
        if (!zones || zones.length === 0) return

        const heatmapPoints = zones.map(zone => {
            const intensity = Math.max(
                0,
                Math.min(zone.risk_score / 100, 1)
            )

            return [
                zone.center_lat,
                zone.center_lon,
                intensity
            ]
        })

        const heatLayer = L.heatLayer(heatmapPoints, {
            radius: 35,
            blur: 20,
            maxZoom: 14,
            minOpacity: 0.2,
            gradient: {
                0.0: '#1abc9c',
                0.4: '#1abc9c',
                0.55: '#e67e22',
                0.75: '#c0392b',
                1.0: '#8b0000'
            }
        })

        heatLayer.addTo(map)

        return () => {
            map.removeLayer(heatLayer)
        }
    }, [map, zones])

    return null
}

export default HeatmapLayer
