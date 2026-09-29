import React from 'react';
import { Building2, Percent, DollarSign, Layers } from 'lucide-react';

export default function InfrastructureMetricCard({
  sector = 'healthcare',
  infraMetrics = {},
  investmentMetrics = {},
  infraPercentile = null
}) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700 shadow-sm">
      <div className="flex items-center justify-between pb-3 border-b border-gray-100 dark:border-gray-700">
        <div className="flex items-center gap-2">
          <Building2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
          <h4 className="font-semibold text-gray-800 dark:text-gray-100 text-sm">
            Infrastructure Supply ({sector})
          </h4>
        </div>
        {infraPercentile !== null && (
          <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-emerald-50 text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-300">
            P{Math.round(infraPercentile)} Rank
          </span>
        )}
      </div>

      <div className="space-y-2 mt-3 text-xs">
        {sector === 'healthcare' && (
          <>
            <div className="flex justify-between items-center py-1 border-b border-gray-100 dark:border-gray-700/50">
              <span className="text-gray-500 dark:text-gray-400">Total Facilities:</span>
              <span className="font-medium text-gray-800 dark:text-gray-200">
                {infraMetrics.total_facilities ?? 0}
              </span>
            </div>
            <div className="flex justify-between items-center py-1 border-b border-gray-100 dark:border-gray-700/50">
              <span className="text-gray-500 dark:text-gray-400">Facilities / 100k Population:</span>
              <span className="font-medium text-gray-800 dark:text-gray-200">
                {infraMetrics.facilities_per_100k !== null && infraMetrics.facilities_per_100k !== undefined
                  ? Number(infraMetrics.facilities_per_100k).toFixed(2)
                  : 'N/A'}
              </span>
            </div>
            <div className="flex justify-between items-center py-1 border-b border-gray-100 dark:border-gray-700/50">
              <span className="text-gray-500 dark:text-gray-400">Doctors / 10k Population:</span>
              <span className="font-medium text-gray-800 dark:text-gray-200">
                {infraMetrics.doctors_per_10k !== null && infraMetrics.doctors_per_10k !== undefined
                  ? Number(infraMetrics.doctors_per_10k).toFixed(2)
                  : 'N/A'}
              </span>
            </div>
            <div className="flex justify-between items-center py-1">
              <span className="text-gray-500 dark:text-gray-400">Hospital Beds / 10k:</span>
              <span className="font-medium text-gray-800 dark:text-gray-200">
                {infraMetrics.beds_per_10k !== null && infraMetrics.beds_per_10k !== undefined
                  ? Number(infraMetrics.beds_per_10k).toFixed(2)
                  : 'N/A'}
              </span>
            </div>
          </>
        )}

        {sector === 'water' && (
          <>
            <div className="flex justify-between items-center py-1 border-b border-gray-100 dark:border-gray-700/50">
              <span className="text-gray-500 dark:text-gray-400">Tap Water Coverage:</span>
              <span className="font-medium text-gray-800 dark:text-gray-200">
                {infraMetrics.tap_water_coverage_pct !== null && infraMetrics.tap_water_coverage_pct !== undefined
                  ? `${Number(infraMetrics.tap_water_coverage_pct).toFixed(1)}%`
                  : 'N/A'}
              </span>
            </div>
            <div className="flex justify-between items-center py-1">
              <span className="text-gray-500 dark:text-gray-400">Clean Water Coverage:</span>
              <span className="font-medium text-gray-800 dark:text-gray-200">
                {infraMetrics.clean_water_coverage_pct !== null && infraMetrics.clean_water_coverage_pct !== undefined
                  ? `${Number(infraMetrics.clean_water_coverage_pct).toFixed(1)}%`
                  : 'N/A'}
              </span>
            </div>
          </>
        )}

        {sector === 'education' && (
          <>
            <div className="flex justify-between items-center py-1 border-b border-gray-100 dark:border-gray-700/50">
              <span className="text-gray-500 dark:text-gray-400">Schools / 10k Population:</span>
              <span className="font-medium text-gray-800 dark:text-gray-200">
                {infraMetrics.schools_per_10k !== null && infraMetrics.schools_per_10k !== undefined
                  ? Number(infraMetrics.schools_per_10k).toFixed(2)
                  : 'N/A'}
              </span>
            </div>
            <div className="flex justify-between items-center py-1">
              <span className="text-gray-500 dark:text-gray-400">School Electrification:</span>
              <span className="font-medium text-gray-800 dark:text-gray-200">
                {infraMetrics.school_electrification_pct !== null && infraMetrics.school_electrification_pct !== undefined
                  ? `${Number(infraMetrics.school_electrification_pct).toFixed(1)}%`
                  : 'N/A'}
              </span>
            </div>
          </>
        )}

        {sector === 'roads' && (
          <div className="flex justify-between items-center py-1">
            <span className="text-gray-500 dark:text-gray-400">Road Density (km/km²):</span>
            <span className="font-medium text-gray-800 dark:text-gray-200">
              {infraMetrics.road_density_km_per_sqkm !== null && infraMetrics.road_density_km_per_sqkm !== undefined
                ? Number(infraMetrics.road_density_km_per_sqkm).toFixed(2)
                : 'N/A'}
            </span>
          </div>
        )}

        {investmentMetrics && investmentMetrics.total_projects > 0 && (
          <div className="mt-2 pt-2 border-t border-gray-100 dark:border-gray-700 flex justify-between items-center text-gray-600 dark:text-gray-300">
            <span className="flex items-center gap-1 text-[11px]">
              <DollarSign className="w-3 h-3 text-emerald-500" />
              Active Projects:
            </span>
            <span className="font-semibold text-xs">
              {investmentMetrics.total_projects} (₹{investmentMetrics.total_budget_crores?.toFixed(1)} Cr)
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
