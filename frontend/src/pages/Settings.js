import React from 'react';
import { Card } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Settings as SettingsIcon, Server, Calendar, Info } from 'lucide-react';

const Settings = () => {
  const apiEndpoint = process.env.REACT_APP_BACKEND_URL;

  return (
    <div className="space-y-6" data-testid="settings-page">
      {/* Header */}
      <div className="flex items-center space-x-3">
        <SettingsIcon className="h-6 w-6 text-slate-600 dark:text-slate-400" />
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">System Settings</h2>
          <p className="text-sm text-slate-600 dark:text-slate-400">Configuration and system information</p>
        </div>
      </div>

      {/* API Configuration */}
      <Card className="p-6 border-slate-200 dark:border-slate-800">
        <div className="flex items-center space-x-2 mb-4">
          <Server className="h-5 w-5 text-slate-600 dark:text-slate-400" />
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">API Configuration</h3>
        </div>
        <div className="space-y-4">
          <div className="flex items-center justify-between py-3 border-b border-slate-100 dark:border-slate-800">
            <div>
              <p className="text-sm font-medium text-slate-700 dark:text-slate-300">Backend Endpoint</p>
              <code className="text-xs text-slate-600 dark:text-slate-400 mt-1 block">
                {apiEndpoint}/api
              </code>
            </div>
            <Badge variant="secondary" className="bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400">
              Connected
            </Badge>
          </div>
          <div className="flex items-center justify-between py-3 border-b border-slate-100 dark:border-slate-800">
            <div>
              <p className="text-sm font-medium text-slate-700 dark:text-slate-300">Protocol</p>
              <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">OCPP 1.6 JSON over WebSocket</p>
            </div>
            <Badge variant="outline">OCPP 1.6</Badge>
          </div>
          <div className="flex items-center justify-between py-3">
            <div>
              <p className="text-sm font-medium text-slate-700 dark:text-slate-300">Data Refresh Rate</p>
              <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">Auto-polling interval</p>
            </div>
            <Badge variant="outline">10 seconds</Badge>
          </div>
        </div>
      </Card>

      {/* Monthly Reset Schedule */}
      <Card className="p-6 border-slate-200 dark:border-slate-800">
        <div className="flex items-center space-x-2 mb-4">
          <Calendar className="h-5 w-5 text-slate-600 dark:text-slate-400" />
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Monthly Reset Schedule</h3>
        </div>
        <div className="space-y-4">
          <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <p className="text-sm text-blue-800 dark:text-blue-300 font-medium mb-2">
              🔄 Automatic Monthly Reset
            </p>
            <p className="text-xs text-blue-700 dark:text-blue-400">
              Energy usage counters are automatically reset on the 1st day of each month at 00:00 UTC.
              This ensures accurate monthly quota tracking for all users.
            </p>
          </div>
          <div className="flex items-center justify-between py-3">
            <div>
              <p className="text-sm font-medium text-slate-700 dark:text-slate-300">Next Reset Date</p>
              <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
                {new Date(new Date().getFullYear(), new Date().getMonth() + 1, 1).toLocaleDateString('en-US', {
                  month: 'long',
                  day: 'numeric',
                  year: 'numeric',
                })}
              </p>
            </div>
            <Badge variant="secondary">Scheduled</Badge>
          </div>
        </div>
      </Card>

      {/* System Information */}
      <Card className="p-6 border-slate-200 dark:border-slate-800">
        <div className="flex items-center space-x-2 mb-4">
          <Info className="h-5 w-5 text-slate-600 dark:text-slate-400" />
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">System Information</h3>
        </div>
        <div className="space-y-3">
          <div className="flex items-center justify-between py-2 border-b border-slate-100 dark:border-slate-800">
            <span className="text-sm text-slate-600 dark:text-slate-400">Dashboard Version</span>
            <span className="text-sm font-medium text-slate-900 dark:text-white">1.0.0</span>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-slate-100 dark:border-slate-800">
            <span className="text-sm text-slate-600 dark:text-slate-400">Supported Chargers</span>
            <span className="text-sm font-medium text-slate-900 dark:text-white">LIVOLTEK, SCHNEIDER</span>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-slate-100 dark:border-slate-800">
            <span className="text-sm text-slate-600 dark:text-slate-400">Authentication</span>
            <Badge variant="secondary">JWT Bearer Token</Badge>
          </div>
          <div className="flex items-center justify-between py-2">
            <span className="text-sm text-slate-600 dark:text-slate-400">Built With</span>
            <span className="text-sm font-medium text-slate-900 dark:text-white">React + FastAPI + MongoDB</span>
          </div>
        </div>
      </Card>

      {/* Data Files Information */}
      <Card className="p-6 border-slate-200 dark:border-slate-800">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Data Files</h3>
        <div className="space-y-2">
          <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
            <code className="text-xs text-slate-700 dark:text-slate-300">users1.csv</code>
            <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">User information, RFID tags, and quotas</p>
          </div>
          <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
            <code className="text-xs text-slate-700 dark:text-slate-300">energy_usage.json</code>
            <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">Energy consumption per user (kWh)</p>
          </div>
          <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
            <code className="text-xs text-slate-700 dark:text-slate-300">active_transactions.json</code>
            <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">Currently active charging sessions</p>
          </div>
          <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
            <code className="text-xs text-slate-700 dark:text-slate-300">meter_data_log.json</code>
            <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">Formatted energy readings history</p>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default Settings;