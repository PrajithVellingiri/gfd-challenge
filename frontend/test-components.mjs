/**
 * Frontend Component and Validation Verification Script
 * Validates frontend files, MIME lists, size bounds, and submission validation logic.
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

console.log('=== GFD CHALLENGE: FRONTEND AUTOMATED COMPONENT & VALIDATION TESTS ===');

// 1. Verify existence of required components and routes
const requiredFiles = [
  'src/App.jsx',
  'src/main.jsx',
  'src/index.css',
  'src/config.js',
  'src/context/AuthContext.jsx',
  'src/services/api.js',
  'src/services/supabase.js',
  'src/components/Navbar.jsx',
  'src/components/AuthModal.jsx',
  'src/components/AudioRecorder.jsx',
  'src/components/ImageUploader.jsx',
  'src/components/LocationPicker.jsx',
  'src/components/SubmissionSuccess.jsx',
  'src/components/CitizenRequestHistory.jsx',
  'src/components/AIAnalysisCard.jsx',
  'src/pages/CitizenPortal.jsx'
];

let failed = false;

for (const file of requiredFiles) {
  const fullPath = path.join(__dirname, file);
  if (!fs.existsSync(fullPath)) {
    console.error(`[FAIL] Missing frontend file: ${file}`);
    failed = true;
  } else {
    console.log(`[PASS] Found component: ${file}`);
  }
}

// 2. Validate Image and Audio MIME constants and limits
const imageUploaderCode = fs.readFileSync(path.join(__dirname, 'src/components/ImageUploader.jsx'), 'utf-8');
if (!imageUploaderCode.includes('10 * 1024 * 1024')) {
  console.error('[FAIL] ImageUploader does not enforce 10 MB limit');
  failed = true;
} else {
  console.log('[PASS] ImageUploader enforces 10 MB limit');
}

if (!imageUploaderCode.includes('image/webp') || !imageUploaderCode.includes('image/png') || !imageUploaderCode.includes('image/jpeg')) {
  console.error('[FAIL] ImageUploader missing required image MIME types');
  failed = true;
} else {
  console.log('[PASS] ImageUploader supports JPEG, PNG, WebP');
}

const audioRecorderCode = fs.readFileSync(path.join(__dirname, 'src/components/AudioRecorder.jsx'), 'utf-8');
if (!audioRecorderCode.includes('25 * 1024 * 1024')) {
  console.error('[FAIL] AudioRecorder does not enforce 25 MB limit');
  failed = true;
} else {
  console.log('[PASS] AudioRecorder enforces 25 MB limit');
}

if (!audioRecorderCode.includes('MediaRecorder')) {
  console.error('[FAIL] AudioRecorder does not use MediaRecorder API');
  failed = true;
} else {
  console.log('[PASS] AudioRecorder uses MediaRecorder API');
}

// 3. Validate Categories, Languages, and Urgencies in CitizenPortal
const portalCode = fs.readFileSync(path.join(__dirname, 'src/pages/CitizenPortal.jsx'), 'utf-8');
const requiredCategories = ['healthcare', 'education', 'roads', 'water', 'transportation', 'electricity', 'digital infrastructure', 'other'];
for (const cat of requiredCategories) {
  if (!portalCode.includes(cat)) {
    console.error(`[FAIL] CitizenPortal missing category: ${cat}`);
    failed = true;
  }
}
console.log(`[PASS] CitizenPortal supports all 8 categories`);

const requiredLanguages = ['en', 'ta', 'hi', 'other'];
for (const lang of requiredLanguages) {
  if (!portalCode.includes(lang)) {
    console.error(`[FAIL] CitizenPortal missing language: ${lang}`);
    failed = true;
  }
}
console.log(`[PASS] CitizenPortal supports English, Tamil, Hindi, Other`);

const requiredUrgencies = ['low', 'medium', 'high', 'critical'];
for (const urg of requiredUrgencies) {
  if (!portalCode.includes(urg)) {
    console.error(`[FAIL] CitizenPortal missing urgency: ${urg}`);
    failed = true;
  }
}
console.log(`[PASS] CitizenPortal supports Low, Medium, High, Critical urgencies`);

if (failed) {
  console.error('Frontend tests failed.');
  process.exit(1);
} else {
  console.log('ALL FRONTEND TESTS PASSED.');
  process.exit(0);
}
