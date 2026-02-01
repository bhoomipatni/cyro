import React from 'react'
import './Legend.css'

function Legend() {
    return (
        <div className="legend">
            <h3 className="legend-title">Risk Levels</h3>

            <div className="legend-items">
                <div className="legend-item">
                    <div className="legend-color legend-low"></div>
                    <div className="legend-text">
                        <strong>Low</strong>
                        <span>Score 0-33</span>
                    </div>
                </div>

                <div className="legend-item">
                    <div className="legend-color legend-medium"></div>
                    <div className="legend-text">
                        <strong>Medium</strong>
                        <span>Score 34-66</span>
                    </div>
                </div>

                <div className="legend-item">
                    <div className="legend-color legend-high"></div>
                    <div className="legend-text">
                        <strong>High</strong>
                        <span>Score 67-100</span>
                    </div>
                </div>
            </div>

        </div>
    )
}

export default Legend
