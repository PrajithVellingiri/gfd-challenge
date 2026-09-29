import React from 'react';
import { Database, Info } from 'lucide-react';

export default function DataProvenance({ dataSources = [] }) {
  if (!dataSources || dataSources.length === 0) {
    return (
      <div className="text-xs text-gray-500 italic flex items-center gap-1.5 mt-2">
        <Info className="w-3.5 h-3.5" />
        No provenance metadata recorded.
      </div>
    );
  }

  return (
    <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-800 text-xs">
      <div className="flex items-center gap-1.5 font-medium text-gray-600 dark:text-gray-300 mb-2">
        <Database className="w-3.5 h-3.5 text-blue-500" />
        <span>Data Provenance & Source References</span>
      </div>
      <div className="space-y-1.5">
        {dataSources.map((ds, index) => (
          <div
            key={index}
            className="flex flex-wrap items-center justify-between gap-1 text-[11px] bg-gray-50 dark:bg-gray-800/60 px-2 py-1 rounded"
          >
            <span className="font-semibold text-gray-700 dark:text-gray-200">
              {ds.dataset_name || ds.dataset || 'Dataset'}
            </span>
            <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
              {ds.reference_year && <span>Baseline: {ds.reference_year}</span>}
              {ds.source && <span>({ds.source})</span>}
              {ds.is_synthetic ? (
                <span className="px-1.5 py-0.5 rounded text-[10px] bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300 font-medium">
                  Synthetic
                </span>
              ) : (
                <span className="px-1.5 py-0.5 rounded text-[10px] bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300 font-medium">
                  Authoritative
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
