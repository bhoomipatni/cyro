# Optional API Keys for Production Deployment

## Current Status: No API Keys Required ✅

The system currently uses free, open-source services:
- OpenStreetMap for map tiles (free)
- Nominatim for geocoding (free)
- PostgreSQL (local)

## Optional Enhancements for Production

### 1. Mapbox (Recommended)
**Purpose**: Better maps and geocoding
**Cost**: Free tier - 50,000 map loads/month
**Sign up**: https://account.mapbox.com/

Add to `frontend/.env`:
```
VITE_MAPBOX_TOKEN=your_mapbox_token_here
```

Update `frontend/src/components/MapView.jsx`:
```javascript
<TileLayer
  attribution='© Mapbox'
  url="https://api.mapbox.com/styles/v1/mapbox/streets-v12/tiles/{z}/{x}/{y}?access_token={accessToken}"
  accessToken={import.meta.env.VITE_MAPBOX_TOKEN}
/>
```

### 2. Google Maps API (Alternative)
**Purpose**: Premium mapping and geocoding
**Cost**: $200 free credit/month
**Sign up**: https://console.cloud.google.com/

### 3. OpenCage Geocoding (Alternative)
**Purpose**: More reliable geocoding than Nominatim
**Cost**: Free tier - 2,500 requests/day
**Sign up**: https://opencagedata.com/

### 4. Weather API (Future Enhancement)
**Purpose**: Add weather factors to risk model
**Options**: OpenWeatherMap (free tier available)

## For Development/Hackathon

**No API keys needed!** The current implementation works out of the box.

## Rate Limits to Consider

**Nominatim (Current)**:
- Limit: 1 request/second
- Requires: User-Agent header (already implemented)
- Good for: Development, low-traffic apps

If you expect high traffic, upgrade to a paid geocoding service.
