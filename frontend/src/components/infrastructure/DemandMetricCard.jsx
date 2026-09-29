import React from 'react';
import { Users, TrendingUp, Activity, BarChart2 } from 'lucide-react';

export default function DemandMetricCard({
  totalRequests = 0,
  requestsLast7Days = 0,
  requestGrowth = 0,
  requestsPer10000 = null,
  demandPercentile = null,
  sector = 'General'
}) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700 shadow-sm">
      <div className="flex items-center justify-between pb-3 border-b border-gray-100 dark:border-gray-700">
        <div className="flex items-center gap-2">
          <Users className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
          <h4 className="font-semibold text-gray-800 dark:text-gray-100 text-sm">
            Citizen Demand ({sector})
          </h4>
        </div>
        {demandPercentile !== null && (
          <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-indigo-50 text-indigo-700 dark:bg-indigo-900/50 dark:text-indigo-300">
            P{Math.round(demandPercentile)} Rank
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3 mt-3 text-sm">
        <div>
          <span className="text-xs text-gray-500 dark:text-gray-400">Total Requests</span>
          <p className="text-lg font-bold text-gray-900 dark:text-white mt-0.5">
            {totalRequests.toLocaleString()}
          </p>
        </div>

        <div>
          <span className="text-xs text-gray-500 dark:text-gray-400">Past 7 Days</span>
          <div className="flex items-center gap-1.5 mt-0.5">
            <p className="text-lg font-bold text-gray-900 dark:text-white">
              {requestsLast7Days.toLocaleString()}
            </p>
            {requestGrowth !== null && requestGrowth !== 0 && (
              <span
                className={`text-xs flex items-center font-medium ${
                  requestGrowth > 0 ? 'text-red-500' : 'text-emerald-500'
                }`}
              >
                <TrendingUp className="w-3 h-3 mr-0.5" />
                {requestGrowth > 0 ? `+${requestGrowth}%` : `${requestGrowth}%`}
              </span>
            )}
          </div>
        </div>

        <div className="col-span-2 pt-2 border-t border-gray-100 dark:border-gray-700/60 flex items-center justify-between">
          <div className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
            <Activity className="w-3.5 h-3.5 text-gray-400" />
            <span>Per 10,000 Residents:</span>
          </div>
          <span className="text-sm font-semibold text-gray-800 dark:text-gray-200">
            {requestsPer10000 !== null ? Number(requestsPer10000).toFixed(2) : 'N/A'}
          </span>
        </div>
      </div>
    </div>
  );
}
