import React, { useState, useRef, useEffect } from 'react';
import { Mic, Square, Play, Trash2, RotateCcw, AlertCircle } from 'lucide-react';

export default function AudioRecorder({ audioBlob, setAudioBlob, audioUrl, setAudioUrl }) {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [errorMessage, setErrorMessage] = useState(null);

  const mediaRecorderRef = useRef(null);
  const timerRef = useRef(null);
  const streamRef = useRef(null);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  const startRecording = async () => {
    setErrorMessage(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      const chunks = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          chunks.push(e.data);
        }
      };

      mediaRecorder.onstop = () => {
        const mimeType = mediaRecorder.mimeType || 'audio/webm';
        const blob = new Blob(chunks, { type: mimeType });

        // Enforce 25 MB limit
        if (blob.size > 25 * 1024 * 1024) {
          setErrorMessage('Audio recording exceeds 25 MB limit.');
          return;
        }

        const url = URL.createObjectURL(blob);
        setAudioBlob(blob);
        setAudioUrl(url);

        // Stop media stream tracks
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);

      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);
    } catch (err) {
      console.error('Microphone access denied:', err);
      setErrorMessage('Microphone access denied or not available. Please allow microphone permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    }
  };

  const discardAudio = () => {
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
    }
    setAudioBlob(null);
    setAudioUrl(null);
    setRecordingTime(0);
    setErrorMessage(null);
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="form-group" style={{ padding: '1rem', backgroundColor: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
      <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <Mic size={18} color="#2563eb" />
        <span>Voice Recording (Optional)</span>
      </label>
      <p className="form-hint" style={{ marginBottom: '0.75rem' }}>
        Record a voice note describing your infrastructure issue in your native language (Max 25 MB).
      </p>

      {errorMessage && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#b91c1c', fontSize: '0.8125rem', marginBottom: '0.75rem' }}>
          <AlertCircle size={16} />
          <span>{errorMessage}</span>
        </div>
      )}

      {!audioBlob && !isRecording && (
        <button
          type="button"
          className="btn btn-secondary"
          onClick={startRecording}
        >
          <Mic size={16} />
          <span>Start Recording</span>
        </button>
      )}

      {isRecording && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ display: 'inline-block', width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#ef4444', animation: 'pulse 1s infinite' }} />
            <span style={{ fontWeight: 600, color: '#dc2626', fontSize: '0.875rem' }}>
              Recording: {formatTime(recordingTime)}
            </span>
          </div>
          <button
            type="button"
            className="btn btn-danger"
            onClick={stopRecording}
          >
            <Square size={16} />
            <span>Stop Recording</span>
          </button>
        </div>
      )}

      {audioBlob && !isRecording && (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap', marginBottom: '0.5rem' }}>
            <audio controls src={audioUrl} style={{ height: '40px', flex: 1, minWidth: '240px' }} />
            <button
              type="button"
              className="btn btn-secondary"
              onClick={discardAudio}
              title="Delete and re-record"
            >
              <RotateCcw size={16} />
              <span>Re-record</span>
            </button>
            <button
              type="button"
              className="btn btn-danger"
              onClick={discardAudio}
              title="Delete recording"
            >
              <Trash2 size={16} />
              <span>Delete</span>
            </button>
          </div>
          <span style={{ fontSize: '0.75rem', color: '#16a34a', fontWeight: 500 }}>
            Audio captured ({(audioBlob.size / 1024).toFixed(1)} KB)
          </span>
        </div>
      )}
    </div>
  );
}
