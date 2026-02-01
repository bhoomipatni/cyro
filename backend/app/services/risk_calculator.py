from typing import Dict
from datetime import datetime
import numpy as np
from sqlalchemy import text
from ..core.database import SessionLocal


class RiskCalculator:
    """
    Explainable, place-based crime risk calculator.
    Uses normalized environmental features + percentile calibration.
    """

    WEIGHTS = {
        'bars_count': 0.25,
        'nightclubs_count': 0.20,
        'liquor_stores_count': 0.15,
        'nearest_subway_meters': -0.15,   # normalized → closer = riskier
        'street_lights_count': -0.12,
        'abandoned_buildings_count': 0.30,
        'population_density': 0.35,
        'unemployment_rate': 0.18,
        'median_income': -0.20,
    }

    TIME_MULTIPLIERS = {
        0: 1.3, 1: 1.4, 2: 1.3, 3: 1.1,
        4: 0.9, 5: 0.7, 6: 0.6, 7: 0.7,
        8: 0.8, 9: 0.85, 10: 0.9, 11: 0.95,
        12: 1.0, 13: 1.0, 14: 1.05, 15: 1.1,
        16: 1.15, 17: 1.2, 18: 1.2, 19: 1.15,
        20: 1.15, 21: 1.15, 22: 1.2, 23: 1.25,
    }

    def __init__(self):
        self._feature_ranges = None
        self._score_percentiles = None

    # -----------------------------
    # Feature normalization helpers
    # -----------------------------

    def _normalize(self, value, min_val, max_val):
        if max_val == min_val:
            return 0.0
        return (value - min_val) / (max_val - min_val)

    def _load_feature_ranges(self):
        if self._feature_ranges is not None:
            return self._feature_ranges

        db = SessionLocal()
        result = db.execute(text("""
            SELECT bars_count,
                   nightclubs_count,
                   liquor_stores_count,
                   nearest_subway_meters,
                   street_lights_count,
                   abandoned_buildings_count,
                   population_density,
                   unemployment_rate,
                   median_income
            FROM grid_features
        """))

        values = {f: [] for f in self.WEIGHTS}
        for row in result:
            for f in values:
                values[f].append(row._mapping[f])

        db.close()

        self._feature_ranges = {
            f: {
                'min': min(vals),
                'max': max(vals)
            }
            for f, vals in values.items()
        }

        return self._feature_ranges

    # -----------------------------
    # Percentile calibration
    # -----------------------------

    def _load_score_percentiles(self):
        if self._score_percentiles is not None:
            return self._score_percentiles

        db = SessionLocal()
        ranges = self._load_feature_ranges()

        result = db.execute(text("""
            SELECT bars_count,
                   nightclubs_count,
                   liquor_stores_count,
                   nearest_subway_meters,
                   street_lights_count,
                   abandoned_buildings_count,
                   population_density,
                   unemployment_rate,
                   median_income
            FROM grid_features
        """))

        scores = []
        for row in result:
            score = 0.0
            for f, w in self.WEIGHTS.items():
                norm = self._normalize(
                    row._mapping[f],
                    ranges[f]['min'],
                    ranges[f]['max']
                )
                score += norm * w
            scores.append(score)

        db.close()

        self._score_percentiles = {
            'p33': np.percentile(scores, 33),
            'p66': np.percentile(scores, 66),
            'min': min(scores),
            'max': max(scores)
        }
from typing import Dict
from datetime import datetime
import numpy as np
from sqlalchemy import text
from ..core.database import SessionLocal


class RiskCalculator:
    """
    Explainable, place-based crime risk calculator.
    Uses normalized environmental features + percentile calibration.
    """

    WEIGHTS = {
        'bars_count': 0.25,
        'nightclubs_count': 0.20,
        'liquor_stores_count': 0.15,
        'nearest_subway_meters': -0.15,   # normalized → closer = riskier
        'street_lights_count': -0.12,
        'abandoned_buildings_count': 0.30,
        'population_density': 0.35,
        'unemployment_rate': 0.18,
        'median_income': -0.20,
    }

    TIME_MULTIPLIERS = {
        0: 1.3, 1: 1.4, 2: 1.3, 3: 1.1,
        4: 0.9, 5: 0.7, 6: 0.6, 7: 0.7,
        8: 0.8, 9: 0.85, 10: 0.9, 11: 0.95,
        12: 1.0, 13: 1.0, 14: 1.05, 15: 1.1,
        16: 1.15, 17: 1.2, 18: 1.2, 19: 1.15,
        20: 1.15, 21: 1.15, 22: 1.2, 23: 1.25,
    }

    def __init__(self):
        self._feature_ranges = None
        self._score_percentiles = None

    # -----------------------------
    # Feature normalization helpers
    # -----------------------------

    def _normalize(self, value, min_val, max_val):
        if max_val == min_val:
            return 0.0
        return (value - min_val) / (max_val - min_val)

    def _load_feature_ranges(self):
        if self._feature_ranges is not None:
            return self._feature_ranges

        db = SessionLocal()
        result = db.execute(text("""
            SELECT bars_count,
                   nightclubs_count,
                   liquor_stores_count,
                   nearest_subway_meters,
                   street_lights_count,
                   abandoned_buildings_count,
                   population_density,
                   unemployment_rate,
                   median_income
            FROM grid_features
        """))

        values = {f: [] for f in self.WEIGHTS}
        for row in result:
            for f in values:
                values[f].append(row._mapping[f])

        db.close()

        self._feature_ranges = {
            f: {
                'min': min(vals),
                'max': max(vals)
            }
            for f, vals in values.items()
        }

        return self._feature_ranges

    # -----------------------------
    # Percentile calibration
    # -----------------------------

    def _load_score_percentiles(self):
        if self._score_percentiles is not None:
            return self._score_percentiles

        db = SessionLocal()
        ranges = self._load_feature_ranges()

        result = db.execute(text("""
            SELECT bars_count,
                   nightclubs_count,
                   liquor_stores_count,
                   nearest_subway_meters,
                   street_lights_count,
                   abandoned_buildings_count,
                   population_density,
                   unemployment_rate,
                   median_income
            FROM grid_features
        """))

        scores = []
        for row in result:
            score = 0.0
            for f, w in self.WEIGHTS.items():
                norm = self._normalize(
                    row._mapping[f],
                    ranges[f]['min'],
                    ranges[f]['max']
                )
                score += norm * w
            scores.append(score)

        db.close()

        self._score_percentiles = {
            'p33': np.percentile(scores, 33),
            'p66': np.percentile(scores, 66),
            'min': min(scores),
            'max': max(scores)
        }

        return self._score_percentiles

    # -----------------------------
    # Main risk calculation
    # -----------------------------

    def calculate_risk(
        self,
        features: Dict[str, float],
        prediction_time: datetime
    ) -> Dict:

        ranges = self._load_feature_ranges()
        percentiles = self._load_score_percentiles()

        base_score = 0.0
        contributions = {}

        for f, w in self.WEIGHTS.items():
            norm = self._normalize(
                features.get(f, 0),
                ranges[f]['min'],
                ranges[f]['max']
            )
            contrib = norm * w
            base_score += contrib
            contributions[self._group_feature(f)] = contrib

        # Time adjustment
        multiplier = self.TIME_MULTIPLIERS.get(prediction_time.hour, 1.0)
        adjusted = base_score * multiplier

        # Percentile-based normalization
        if adjusted <= percentiles['p33']:
            score = self._scale(adjusted, percentiles['min'], percentiles['p33'], 0, 33)
            level = "Low"
        elif adjusted <= percentiles['p66']:
            score = self._scale(adjusted, percentiles['p33'], percentiles['p66'], 33, 66)
            level = "Medium"
        else:
            score = self._scale(adjusted, percentiles['p66'], percentiles['max'], 66, 100)
            level = "High"

        score = float(np.clip(score, 0, 100))

        explanation = self._explain(contributions, level, prediction_time)

        return {
            "risk_score": round(score, 2),
            "risk_level": level,
            "contributions": contributions,
            "explanation": explanation,
            "prediction_time": prediction_time.isoformat()
        }

    # -----------------------------
    # Utility helpers
    # -----------------------------

    def _scale(self, val, min_v, max_v, out_min, out_max):
        if max_v == min_v:
            return out_min
        return (val - min_v) / (max_v - min_v) * (out_max - out_min) + out_min

    def _group_feature(self, f):
        if f in ['bars_count', 'nightclubs_count', 'liquor_stores_count']:
            return 'alcohol_density'
        if 'subway' in f:
            return 'transit_proximity'
        if 'light' in f:
            return 'lighting'
        if 'abandoned' in f:
            return 'vacancy'
        if 'population' in f:
            return 'population'
        return 'socioeconomic'

    def _explain(self, contributions, level, time):
        hour = time.hour
        tod = "night" if hour >= 22 or hour < 6 else "day"
        top = sorted(contributions.items(), key=lambda x: abs(x[1]), reverse=True)[:3]
        factors = ", ".join([f"{k} ({abs(v):.0%})" for k, v in top])
        return f"{level} risk area during {tod}. Main factors: {factors}"


# Singleton
risk_calculator = RiskCalculator()
