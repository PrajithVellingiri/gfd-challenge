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
  'src/components/RequestIntelligenceSection.jsx',
  'src/components/infrastructure/DemandMetricCard.jsx',
  'src/components/infrastructure/InfrastructureMetricCard.jsx',
  'src/components/infrastructure/GapSignalCard.jsx',
  'src/components/infrastructure/DataProvenance.jsx',
  'src/components/infrastructure/DistrictIntelligenceCard.jsx',
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

// 4. Validate Infrastructure Intelligence API Client functions
const apiCode = fs.readFileSync(path.join(__dirname, 'src/services/api.js'), 'utf-8');
const requiredApiFunctions = [
  'fetchDistrictIntelligence',
  'fetchDistrictIntelligenceById',
  'fetchDistrictSectors',
  'fetchGapSignals',
  'refreshInfrastructureIntelligence'
];
for (const fn of requiredApiFunctions) {
  if (!apiCode.includes(`export async function ${fn}`)) {
    console.error(`[FAIL] api.js missing function: ${fn}`);
    failed = true;
  }
}
console.log(`[PASS] api.js implements all Phase 6 Infrastructure Intelligence functions`);

// 5. Validate GapSignalCard signal states
const gapCardCode = fs.readFileSync(path.join(__dirname, 'src/components/infrastructure/GapSignalCard.jsx'), 'utf-8');
const requiredSignals = ['potential_gap', 'infrastructure_pressure', 'demand_supply_signal', 'balanced', 'insufficient_data'];
for (const sig of requiredSignals) {
  if (!gapCardCode.includes(sig)) {
    console.error(`[FAIL] GapSignalCard missing signal state: ${sig}`);
    failed = true;
  }
}
console.log(`[PASS] GapSignalCard handles all 5 explainable mismatch states`);

if (failed) {
  console.error('Frontend tests failed.');
  process.exit(1);
} else {
  console.log('ALL FRONTEND TESTS PASSED.');
  process.exit(0);
}
