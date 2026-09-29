import React from 'react';
import { AlertCircle, CheckCircle2, AlertTriangle, HelpCircle, FileText } from 'lucide-react';

const SIGNAL_CONFIG = {
  potential_gap: {
    label: 'Potential Gap',
    bg: 'bg-red-50 dark:bg-red-950/40',
    border: 'border-red-200 dark:border-red-800',
    text: 'text-red-700 dark:text-red-300',
    badge: 'bg-red-100 text-red-800 dark:bg-red-900/60 dark:text-red-200',
    icon: AlertCircle
  },
  infrastructure_pressure: {
    label: 'Infrastructure Pressure',
    bg: 'bg-amber-50 dark:bg-amber-950/40',
    border: 'border-amber-200 dark:border-amber-800',
    text: 'text-amber-700 dark:text-amber-300',
    badge: 'bg-amber-100 text-amber-800 dark:bg-amber-900/60 dark:text-amber-200',
    icon: AlertTriangle
  },
  demand_supply_signal: {
    label: 'Demand-Supply Signal',
    bg: 'bg-blue-50 dark:bg-blue-950/40',
    border: 'border-blue-200 dark:border-blue-800',
    text: 'text-blue-700 dark:text-blue-300',
    badge: 'bg-blue-100 text-blue-800 dark:bg-blue-900/60 dark:text-blue-200',
    icon: AlertTriangle
  },
  balanced: {
    label: 'Demand & Supply In Range',
    bg: 'bg-emerald-50 dark:bg-emerald-950/40',
    border: 'border-emerald-200 dark:border-emerald-800',
    text: 'text-emerald-700 dark:text-emerald-300',
    badge: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/60 dark:text-emerald-200',
    icon: CheckCircle2
  },
  insufficient_data: {
    label: 'Insufficient Data',
    bg: 'bg-gray-50 dark:bg-gray-800/40',
    border: 'border-gray-200 dark:border-gray-700',
    text: 'text-gray-600 dark:text-gray-400',
    badge: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
    icon: HelpCircle
  }
};

export default function GapSignalCard({ gapSignal = {}, mismatchSignal = 'balanced' }) {
  const signalKey = mismatchSignal in SIGNAL_CONFIG ? mismatchSignal : 'insufficient_data';
  const cfg = SIGNAL_CONFIG[signalKey];
  const IconComponent = cfg.icon;

  const rationale = gapSignal.rationale || {};
  const confidence = gapSignal.confidence || 'moderate';

  return (
    <div className={`rounded-lg p-4 border ${cfg.bg} ${cfg.border} shadow-sm space-y-3`}>
      <div className="flex items-center justify-between pb-2 border-b border-gray-200/60 dark:border-gray-700/60">
        <div className="flex items-center gap-2">
          <IconComponent className={`w-5 h-5 ${cfg.text}`} />
          <h4 className={`font-semibold text-sm ${cfg.text}`}>
            Decision-Support Indicator: {cfg.label}
          </h4>
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${cfg.badge}`}>
            Confidence: {confidence}
          </span>
        </div>
      </div>

      <div className="space-y-2 text-xs">
        {rationale.what_was_observed && (
          <div>
            <span className="font-semibold text-gray-700 dark:text-gray-300">Demand Observation: </span>
            <span className="text-gray-600 dark:text-gray-400">{rationale.what_was_observed}</span>
          </div>
        )}

        {rationale.infrastructure_observed && (
          <div>
            <span className="font-semibold text-gray-700 dark:text-gray-300">Infrastructure Supply: </span>
            <span className="text-gray-600 dark:text-gray-400">{rationale.infrastructure_observed}</span>
          </div>
        )}

        {rationale.why_signal_generated && (
          <div className="bg-white/70 dark:bg-gray-900/40 p-2.5 rounded border border-gray-100 dark:border-gray-800 text-xs">
            <span className="font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-1 mb-1">
              <FileText className="w-3.5 h-3.5 text-gray-500" />
              Explainable Rationale:
            </span>
            <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
              {rationale.why_signal_generated}
            </p>
          </div>
        )}

        {gapSignal.data_sources && gapSignal.data_sources.length > 0 && (
          <div className="text-[11px] text-gray-500 dark:text-gray-400 pt-1">
            <span className="font-medium">Datasets Consulted:</span>{' '}
            {gapSignal.data_sources.join(', ')}
          </div>
        )}
      </div>
    </div>
  );
}
