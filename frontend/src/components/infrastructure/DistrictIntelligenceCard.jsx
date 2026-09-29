import React, { useState } from 'react';
import { MapPin, ChevronDown, ChevronUp } from 'lucide-react';
import DemandMetricCard from './DemandMetricCard';
import InfrastructureMetricCard from './InfrastructureMetricCard';
import GapSignalCard from './GapSignalCard';
import DataProvenance from './DataProvenance';

export default function DistrictIntelligenceCard({ intelligence }) {
  const [showProvenance, setShowProvenance] = useState(false);

  if (!intelligence) return null;

  const {
    district_name,
    sector = 'healthcare',
    population = null,
    population_source = 'Census of India 2011',
    total_requests = 0,
    requests_last_7_days = 0,
    request_growth_percentage = 0,
    requests_per_10000 = null,
    demand_percentile = null,
    infrastructure_percentile = null,
    infrastructure_metrics = {},
    investment_metrics = {},
    mismatch_signal = 'balanced',
    gap_signal = {},
    data_sources = []
  } = intelligence;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden p-5 space-y-4">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-gray-100 dark:border-gray-700/60 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-indigo-50 dark:bg-indigo-900/40 text-indigo-600 dark:text-indigo-400 rounded-lg">
            <MapPin className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-gray-900 dark:text-white capitalize">
              {district_name || 'District Intelligence'}
            </h3>
            <span className="text-xs text-gray-500 dark:text-gray-400">
              Sector:{' '}
              <span className="font-semibold text-gray-700 dark:text-gray-300 capitalize">
                {sector}
              </span>
              {population && (
                <span className="ml-2">
                  • Pop: {Number(population).toLocaleString()} ({population_source})
                </span>
              )}
            </span>
          </div>
        </div>

        <button
          onClick={() => setShowProvenance(!showProvenance)}
          className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1"
        >
          {showProvenance ? 'Hide Sources' : 'View Sources'}
          {showProvenance ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>
      </div>

      {/* Grid of Demand vs Infrastructure */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <DemandMetricCard
          totalRequests={total_requests}
          requestsLast7Days={requests_last_7_days}
          requestGrowth={request_growth_percentage}
          requestsPer10000={requests_per_10000}
          demandPercentile={demand_percentile}
          sector={sector}
        />
        <InfrastructureMetricCard
          sector={sector}
          infraMetrics={infrastructure_metrics}
          investmentMetrics={investment_metrics}
          infraPercentile={infrastructure_percentile}
        />
      </div>

      {/* Explainable Gap Signal */}
      <GapSignalCard
        mismatchSignal={mismatch_signal}
        gapSignal={gap_signal}
      />

      {/* Provenance Metadata */}
      {showProvenance && <DataProvenance dataSources={data_sources} />}
    </div>
  );
}
