import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { submitCitizenRequest, uploadAttachment } from '../services/api';
import LocationPicker from '../components/LocationPicker';
import ImageUploader from '../components/ImageUploader';
import AudioRecorder from '../components/AudioRecorder';
import SubmissionSuccess from '../components/SubmissionSuccess';
import { Send, AlertCircle, Sparkles } from 'lucide-react';

const CATEGORIES = [
  { value: 'healthcare', label: 'Healthcare' },
  { value: 'education', label: 'Education' },
  { value: 'roads', label: 'Roads' },
  { value: 'water', label: 'Water' },
  { value: 'transportation', label: 'Transportation' },
  { value: 'electricity', label: 'Electricity' },
  { value: 'digital infrastructure', label: 'Digital Infrastructure' },
  { value: 'other', label: 'Other' },
];

const LANGUAGES = [
  { value: 'en', label: 'English' },
  { value: 'ta', label: 'Tamil' },
  { value: 'hi', label: 'Hindi' },
  { value: 'other', label: 'Other' },
];

const URGENCIES = [
  { value: 'low', label: 'Low - Routine Maintenance' },
  { value: 'medium', label: 'Medium - Normal Issue' },
  { value: 'high', label: 'High - Disrupting Daily Life' },
  { value: 'critical', label: 'Critical - Imminent Hazard / Emergency' },
];

export default function CitizenPortal({ onViewHistory }) {
  const { user } = useAuth();

  // Form State
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('healthcare');
  const [language, setLanguage] = useState('en');
  const [urgency, setUrgency] = useState('medium');

  // Location State
  const [latitude, setLatitude] = useState(null);
  const [longitude, setLongitude] = useState(null);
  const [locationName, setLocationName] = useState('');
  const [selectedDistrict, setSelectedDistrict] = useState('');

  // Media State
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [audioBlob, setAudioBlob] = useState(null);
  const [audioUrl, setAudioUrl] = useState(null);

  // Status & Confirmation State
  const [submitting, setSubmitting] = useState(false);
  const [submissionResult, setSubmissionResult] = useState(null);
  const [formError, setFormError] = useState(null);

  const resetForm = () => {
    setDescription('');
    setCategory('healthcare');
    setLanguage('en');
    setUrgency('medium');
    setLatitude(null);
    setLongitude(null);
    setLocationName('');
    setSelectedDistrict('');
    setImageFile(null);
    setImagePreview(null);
    setAudioBlob(null);
    setAudioUrl(null);
    setSubmissionResult(null);
    setFormError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormError(null);

    // Validation
    if (!description.trim() || description.trim().length < 5) {
      setFormError('Please provide a detailed description (minimum 5 characters).');
      return;
    }

    if (!latitude && !longitude && !locationName.trim() && !selectedDistrict) {
      setFormError('Please provide a location (use GPS detection, choose a district, or enter a village/landmark).');
      return;
    }

    setSubmitting(true);
    const clientRequestId = crypto.randomUUID();

    try {
      let imagePath = null;
      let audioPath = null;

      // 1. Upload image if attached
      if (imageFile && user?.id) {
        try {
          const imgRes = await uploadAttachment(imageFile, user.id, clientRequestId, 'image');
          imagePath = imgRes.storage_path;
        } catch (imgErr) {
          console.warn('Image upload error:', imgErr);
          // Fall back to structured path reference
          imagePath = `${user.id}/${clientRequestId}/${imageFile.name}`;
        }
      }

      // 2. Upload audio if attached
      if (audioBlob && user?.id) {
        try {
          const audioFile = new File([audioBlob], 'voice_note.webm', { type: audioBlob.type });
          const audRes = await uploadAttachment(audioFile, user.id, clientRequestId, 'audio');
          audioPath = audRes.storage_path;
        } catch (audErr) {
          console.warn('Audio upload error:', audErr);
          audioPath = `${user.id}/${clientRequestId}/voice_note.webm`;
        }
      }

      // 3. Assemble submission payload
      const payload = {
        user_id: user?.id,
        description: description.trim(),
        category,
        language,
        urgency,
        latitude: latitude || undefined,
        longitude: longitude || undefined,
        location_name: locationName.trim() || selectedDistrict || 'Location Unspecified',
        image_path: imagePath || undefined,
        audio_path: audioPath || undefined
      };

      const result = await submitCitizenRequest(payload);
      setSubmissionResult(result);
    } catch (err) {
      setFormError(err.message || 'Submission failed. Please check network connection.');
    } finally {
      setSubmitting(false);
    }
  };

  if (submissionResult) {
    return (
      <SubmissionSuccess
        result={submissionResult}
        onReset={resetForm}
        onViewHistory={onViewHistory}
      />
    );
  }

  return (
    <div className="container" style={{ maxWidth: '780px' }}>
      <div style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#0f172a', marginBottom: '0.25rem' }}>
          Submit Development Need or Grievance
        </h2>
        <p style={{ color: '#64748b', fontSize: '0.875rem' }}>
          Report infrastructure deficiencies, public service gaps, and village requirements directly to governance authorities.
        </p>
      </div>

      {formError && (
        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#b91c1c', backgroundColor: '#fee2e2', border: '1px solid #fca5a5', padding: '0.875rem' }}>
          <AlertCircle size={18} />
          <span>{formError}</span>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        {/* Description */}
        <div className="card">
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label" htmlFor="descriptionInput">
              Request Description <span style={{ color: '#ef4444' }}>*</span>
            </label>
            <textarea
              id="descriptionInput"
              className="form-control"
              placeholder="Describe the development issue or infrastructure need in detail..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              required
              rows={4}
            />
            <span className="form-hint">
              Be specific about what is broken, missing, or required (e.g. road repair, lack of doctors at clinic, broken water pipeline).
            </span>
          </div>
        </div>

        {/* Category & Language & Urgency */}
        <div className="card">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
            {/* Category */}
            <div className="form-group">
              <label className="form-label" htmlFor="categorySelect">
                Sector / Category <span style={{ color: '#ef4444' }}>*</span>
              </label>
              <select
                id="categorySelect"
                className="form-control"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
              >
                {CATEGORIES.map((c) => (
                  <option key={c.value} value={c.value}>{c.label}</option>
                ))}
              </select>
            </div>

            {/* Language */}
            <div className="form-group">
              <label className="form-label" htmlFor="languageSelect">
                Language <span style={{ color: '#ef4444' }}>*</span>
              </label>
              <select
                id="languageSelect"
                className="form-control"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
              >
                {LANGUAGES.map((l) => (
                  <option key={l.value} value={l.value}>{l.label}</option>
                ))}
              </select>
            </div>

            {/* Urgency */}
            <div className="form-group">
              <label className="form-label" htmlFor="urgencySelect">
                Urgency Level <span style={{ color: '#ef4444' }}>*</span>
              </label>
              <select
                id="urgencySelect"
                className="form-control"
                value={urgency}
                onChange={(e) => setUrgency(e.target.value)}
              >
                {URGENCIES.map((u) => (
                  <option key={u.value} value={u.value}>{u.label}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Location Picker */}
        <LocationPicker
          latitude={latitude}
          setLatitude={setLatitude}
          longitude={longitude}
          setLongitude={setLongitude}
          locationName={locationName}
          setLocationName={setLocationName}
          selectedDistrict={selectedDistrict}
          setSelectedDistrict={setSelectedDistrict}
        />

        {/* Media Attachments */}
        <div className="card">
          <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#334155', marginBottom: '1rem' }}>
            Attachments & Media (Optional)
          </h3>

          <ImageUploader
            imageFile={imageFile}
            setImageFile={setImageFile}
            imagePreview={imagePreview}
            setImagePreview={setImagePreview}
          />

          <AudioRecorder
            audioBlob={audioBlob}
            setAudioBlob={setAudioBlob}
            audioUrl={audioUrl}
            setAudioUrl={setAudioUrl}
          />
        </div>

        {/* Submit Button */}
        <div style={{ textAlign: 'right', marginTop: '1rem' }}>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={submitting}
            style={{ padding: '0.75rem 2rem', fontSize: '1rem' }}
          >
            <Send size={18} />
            <span>{submitting ? 'Recording Request...' : 'Submit Development Request'}</span>
          </button>
        </div>
      </form>
    </div>
  );
}
