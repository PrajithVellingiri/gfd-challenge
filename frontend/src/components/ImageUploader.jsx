import React, { useState } from 'react';
import { Image, Upload, X, AlertCircle } from 'lucide-react';

const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/jpg'];
const MAX_IMAGE_SIZE = 10 * 1024 * 1024; // 10 MB

export default function ImageUploader({ imageFile, setImageFile, imagePreview, setImagePreview }) {
  const [errorMessage, setErrorMessage] = useState(null);

  const handleFileChange = (e) => {
    setErrorMessage(null);
    const file = e.target.files?.[0];
    if (!file) return;

    if (!ALLOWED_TYPES.includes(file.type)) {
      setErrorMessage('Unsupported format. Allowed image formats: JPEG, PNG, WebP.');
      return;
    }

    if (file.size > MAX_IMAGE_SIZE) {
      setErrorMessage(`Image exceeds 10 MB limit (${(file.size / (1024 * 1024)).toFixed(1)} MB).`);
      return;
    }

    setImageFile(file);
    const previewUrl = URL.createObjectURL(file);
    setImagePreview(previewUrl);
  };

  const removeImage = () => {
    if (imagePreview) {
      URL.revokeObjectURL(imagePreview);
    }
    setImageFile(null);
    setImagePreview(null);
    setErrorMessage(null);
  };

  return (
    <div className="form-group" style={{ padding: '1rem', backgroundColor: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
      <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <Image size={18} color="#2563eb" />
        <span>Infrastructure Photo (Optional)</span>
      </label>
      <p className="form-hint" style={{ marginBottom: '0.75rem' }}>
        Attach a photo of the damaged infrastructure, pothole, leak, or facility (JPEG, PNG, WebP up to 10 MB).
      </p>

      {errorMessage && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#b91c1c', fontSize: '0.8125rem', marginBottom: '0.75rem' }}>
          <AlertCircle size={16} />
          <span>{errorMessage}</span>
        </div>
      )}

      {!imagePreview ? (
        <label style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          border: '2px dashed #cbd5e1',
          borderRadius: '8px',
          padding: '1.5rem',
          cursor: 'pointer',
          backgroundColor: '#ffffff'
        }}>
          <Upload size={28} color="#94a3b8" style={{ marginBottom: '0.5rem' }} />
          <span style={{ fontSize: '0.875rem', fontWeight: 500, color: '#2563eb' }}>Click to upload an image</span>
          <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>JPEG, PNG, WebP (Max 10 MB)</span>
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={handleFileChange}
            style={{ display: 'none' }}
          />
        </label>
      ) : (
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
          <div style={{ position: 'relative', width: '120px', height: '120px', borderRadius: '8px', overflow: 'hidden', border: '1px solid #cbd5e1' }}>
            <img
              src={imagePreview}
              alt="Uploaded issue preview"
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: '0.875rem', fontWeight: 600, color: '#334155' }}>{imageFile?.name}</div>
            <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
              {(imageFile.size / 1024).toFixed(1)} KB • {imageFile.type}
            </div>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={removeImage}
              style={{ marginTop: '0.5rem', padding: '0.375rem 0.75rem', fontSize: '0.75rem' }}
            >
              <X size={14} />
              <span>Remove Photo</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
