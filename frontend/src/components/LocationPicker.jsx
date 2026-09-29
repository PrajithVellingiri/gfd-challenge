import React, { useState } from 'react';
import { MapPin, Navigation, CheckCircle2, AlertCircle } from 'lucide-react';

const CANONICAL_DISTRICTS = [
  "Bengaluru Urban", "Mysuru", "Belagavi", "Kalaburagi",
  "Chennai", "Coimbatore", "Madurai", "Kanchipuram",
  "Thiruvananthapuram", "Ernakulam", "Wayanad",
  "Mumbai Suburban", "Pune", "Nagpur", "Gadchiroli",
  "Ahmedabad", "Surat", "Rajkot", "Vadodara",
  "Varanasi", "Lucknow", "Gorakhpur", "Bahraich",
  "Patna", "Gaya", "Muzaffarpur", "Purnia",
  "Jaipur", "Jodhpur", "Udaipur", "Jaisalmer",
  "Kolkata", "Darjeeling", "Murshidabad",
  "Bhopal", "Indore", "Jabalpur", "Balaghat",
  "Khurda", "Cuttack", "Kalahandi",
  "Kamrup Metropolitan", "Dibrugarh", "Cachar"
].sort();

export default function LocationPicker({
  latitude, setLatitude,
  longitude, setLongitude,
  locationName, setLocationName,
  selectedDistrict, setSelectedDistrict
}) {
  const [detecting, setDetecting] = useState(false);
  const [geoStatus, setGeoStatus] = useState(null);

  const detectLocation = () => {
    if (!navigator.geolocation) {
      setGeoStatus({ type: 'error', message: 'Geolocation is not supported by your browser. Please enter manually.' });
      return;
    }

    setDetecting(true);
    setGeoStatus(null);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = parseFloat(position.coords.latitude.toFixed(6));
        const lon = parseFloat(position.coords.longitude.toFixed(6));
        setLatitude(lat);
        setLongitude(lon);
        setDetecting(false);
        setGeoStatus({
          type: 'success',
          message: `Location detected: ${lat}° N, ${lon}° E (Accuracy: ±${Math.round(position.coords.accuracy)}m)`
        });
        if (!locationName) {
          setLocationName('GPS Pinpoint Location');
        }
      },
      (error) => {
        setDetecting(false);
        let msg = 'Unable to detect location. Please enter your location manually.';
        if (error.code === error.PERMISSION_DENIED) {
          msg = 'Location permission denied. Please select your district or landmark below.';
        }
        setGeoStatus({ type: 'error', message: msg });
      },
      { timeout: 10000, enableHighAccuracy: true }
    );
  };

  const handleDistrictChange = (e) => {
    const val = e.target.value;
    setSelectedDistrict(val);
    if (val && !locationName) {
      setLocationName(val);
    }
  };

  return (
    <div className="card" style={{ padding: '1.25rem', marginBottom: '1.25rem' }}>
      <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
        <MapPin size={18} color="#2563eb" />
        <span>Incident Location</span>
      </label>
      <p className="form-hint" style={{ marginBottom: '1rem' }}>
        Provide GPS coordinates or select your administrative district to assist local governance authorities.
      </p>

      {/* Geolocation Button */}
      <div style={{ marginBottom: '1rem' }}>
        <button
          type="button"
          className="btn btn-secondary"
          onClick={detectLocation}
          disabled={detecting}
          style={{ width: '100%', justifyContent: 'center' }}
        >
          <Navigation size={16} color="#2563eb" />
          <span>{detecting ? 'Detecting GPS Coordinates...' : 'Detect My Current Location (GPS)'}</span>
        </button>

        {geoStatus && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            fontSize: '0.8125rem',
            marginTop: '0.5rem',
            color: geoStatus.type === 'success' ? '#16a34a' : '#b91c1c'
          }}>
            {geoStatus.type === 'success' ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
            <span>{geoStatus.message}</span>
          </div>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
        {/* District Selector */}
        <div className="form-group" style={{ marginBottom: 0 }}>
          <label className="form-label" htmlFor="districtSelect">
            Administrative District
          </label>
          <select
            id="districtSelect"
            className="form-control"
            value={selectedDistrict || ''}
            onChange={handleDistrictChange}
          >
            <option value="">-- Select District (Optional) --</option>
            {CANONICAL_DISTRICTS.map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
        </div>

        {/* Location / Village / Landmark */}
        <div className="form-group" style={{ marginBottom: 0 }}>
          <label className="form-label" htmlFor="landmarkInput">
            Village / Ward / Landmark
          </label>
          <input
            id="landmarkInput"
            type="text"
            className="form-control"
            placeholder="e.g. Near Bus Stand, Ward 12"
            value={locationName || ''}
            onChange={(e) => setLocationName(e.target.value)}
          />
        </div>
      </div>

      {latitude && longitude && (
        <div style={{ marginTop: '0.75rem', fontSize: '0.75rem', color: '#64748b' }}>
          Coordinates: <strong>{latitude}, {longitude}</strong> (will be automatically resolved against PostGIS boundaries)
        </div>
      )}
    </div>
  );
}
