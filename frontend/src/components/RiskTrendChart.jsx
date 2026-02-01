import React, { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import axios from 'axios'
import './RiskTrendChart.css'

function RiskTrendChart({ lat, lon }) {
    const [trendData, setTrendData] = useState([])
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)

    useEffect(() => {
        if (!lat || !lon) {
            setTrendData([])
            setError(null)
            return
        }

        fetchRiskTrend()
    }, [lat, lon])

    const fetchRiskTrend = async () => {
        setLoading(true)
        setError(null)

        try {
            const today = new Date()

            // Create 24 promises, one per hour
            const promises = Array.from({ length: 24 }, (_, hour) => {
                const predictionTime = new Date(today)
                predictionTime.setHours(hour, 0, 0, 0)

                return axios
                    .get('http://localhost:8000/api/risk-zones', {
                        params: {
                            lat,
                            lon,
                            radius: 1.0,
                            prediction_time: predictionTime.toISOString()
                        }
                    })
                    .then(res => {
                        let riskScore = 0

                        if (res.data && res.data.length > 0) {
                            // pick closest zone to lat/lon
                            const closestZone = res.data.reduce((prev, curr) => {
                                const prevDist = Math.hypot(prev.center_lat - lat, prev.center_lon - lon)
                                const currDist = Math.hypot(curr.center_lat - lat, curr.center_lon - lon)
                                return currDist < prevDist ? curr : prev
                            })
                            riskScore = Math.round(closestZone.risk_score)
                        }

                        return {
                            hour,
                            hourLabel: `${hour.toString().padStart(2, '0')}:00`,
                            risk: riskScore
                        }
                    })
                    .catch(err => {
                        console.error(`Error fetching hour ${hour}:`, err)
                        return { hour, hourLabel: `${hour.toString().padStart(2, '0')}:00`, risk: 0 }
                    })
            })

            const results = await Promise.all(promises)
            setTrendData(results)
        } catch (err) {
            console.error('Error fetching risk trend:', err)
            setError('Failed to load risk trend.')
        } finally {
            setLoading(false)
        }
    }

    if (loading) {
        return (
            <div className="risk-trend-chart">
                <p className="trend-placeholder">Loading trend data...</p>
            </div>
        )
    }

    if (error) {
        return (
            <div className="risk-trend-chart">
                <p className="trend-error">{error}</p>
            </div>
        )
    }

    if (!trendData || trendData.length === 0) {
        return (
            <div className="risk-trend-chart">
                <p className="trend-placeholder">No data available</p>
            </div>
        )
    }

    return (
        <div className="risk-trend-chart">
            <h3 className="trend-title">24-Hour Risk Trend</h3>
            <ResponsiveContainer width="100%" height={180}>
                <LineChart data={trendData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                    <XAxis
                        dataKey="hourLabel"
                        stroke="#aaa"
                        style={{ fontSize: '12px' }}
                        tick={{ fill: '#aaa' }}
                    />
                    <YAxis
                        stroke="#aaa"
                        style={{ fontSize: '12px' }}
                        tick={{ fill: '#aaa' }}
                        domain={[0, 100]}
                    />
                    <Tooltip
                        contentStyle={{
                            backgroundColor: '#2a2a2a',
                            border: '1px solid #444',
                            borderRadius: '4px',
                            color: '#fff'
                        }}
                        formatter={(value) => `${value}%`}
                    />
                    <Line
                        type="monotone"
                        dataKey="risk"
                        stroke="#e74c3c"
                        dot={false}
                        strokeWidth={2}
                        isAnimationActive={true}
                    />
                </LineChart>
            </ResponsiveContainer>
        </div>
    )
}

export default RiskTrendChart
