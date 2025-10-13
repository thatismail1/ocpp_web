import React, { useState, useEffect } from 'react';
import { Card } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import api from '../utils/api';
import { Zap, Clock, Activity, Filter } from 'lucide-react';

const Chargers = () => {
  const [chargers, setChargers] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);

  const fetchChargers = async () => {
    try {
      const response = await api.get('/api/chargers');
      setChargers(response.data.chargers || []);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching chargers:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchChargers();
    const interval = setInterval(fetchChargers, 10000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status) => {
    switch (status) {
      case 'Charging':
        return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400';
      case 'Available':
        return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400';
      case 'Offline':
        return 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-400';
      case 'Faulted':
        return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400';
      default:
        return 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-400';
    }
  };

  const filteredChargers = chargers.filter((charger) => {
    if (filter === 'all') return true;
    return charger.brand === filter;
  });

  const brands = ['all', ...new Set(chargers.map((c) => c.brand))];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-slate-600 dark:text-slate-400">Loading chargers...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="chargers-page">
      {/* Filter Tabs */}
      <Card className="p-6 border-slate-200 dark:border-slate-800">
        <div className="flex items-center space-x-2 mb-4">
          <Filter className="h-5 w-5 text-slate-600 dark:text-slate-400" />
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Filter by Brand</h3>
        </div>
        <Tabs value={filter} onValueChange={setFilter} className="w-full">
          <TabsList className="grid grid-cols-4 w-full max-w-2xl">
            {brands.map((brand) => (
              <TabsTrigger key={brand} value={brand} className="capitalize">
                {brand === 'all' ? 'All Chargers' : brand}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
      </Card>

      {/* Chargers Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredChargers.map((charger) => {
          const isOnline = charger.status !== 'Offline';
          const lastHeartbeat = new Date(charger.last_heartbeat);
          const timeDiff = Math.floor((new Date() - lastHeartbeat) / 1000 / 60);

          return (
            <Card
              key={charger.name}
              className="p-6 border-slate-200 dark:border-slate-800 hover:shadow-lg transition-all"
              data-testid={`charger-card-${charger.name}`}
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className={`p-3 rounded-xl ${
                    charger.status === 'Charging'
                      ? 'bg-emerald-100 dark:bg-emerald-900/30'
                      : 'bg-blue-100 dark:bg-blue-900/30'
                  }`}>
                    <Zap
                      className={`h-6 w-6 ${
                        charger.status === 'Charging'
                          ? 'text-emerald-600 dark:text-emerald-400'
                          : 'text-blue-600 dark:text-blue-400'
                      }`}
                    />
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-900 dark:text-white">{charger.name}</h3>
                    <p className="text-sm text-slate-600 dark:text-slate-400">{charger.brand}</p>
                  </div>
                </div>
                <Badge className={getStatusColor(charger.status)} data-testid={`charger-status-${charger.name}`}>
                  {charger.status}
                </Badge>
              </div>

              {/* Stats */}
              <div className="space-y-3">
                <div className="flex items-center justify-between py-2 border-b border-slate-100 dark:border-slate-800">
                  <span className="text-sm text-slate-600 dark:text-slate-400">Total Energy</span>
                  <span className="font-semibold text-slate-900 dark:text-white">
                    {charger.total_energy_delivered.toFixed(1)} kWh
                  </span>
                </div>
                <div className="flex items-center justify-between py-2 border-b border-slate-100 dark:border-slate-800">
                  <span className="text-sm text-slate-600 dark:text-slate-400">Uptime</span>
                  <span className="font-semibold text-slate-900 dark:text-white">
                    {charger.uptime_hours} hrs
                  </span>
                </div>
                <div className="flex items-center justify-between py-2">
                  <span className="text-sm text-slate-600 dark:text-slate-400 flex items-center">
                    <Clock className="h-4 w-4 mr-1" />
                    Last Heartbeat
                  </span>
                  <span className="text-sm font-medium text-slate-900 dark:text-white">
                    {timeDiff < 1 ? 'Just now' : `${timeDiff}m ago`}
                  </span>
                </div>
              </div>

              {/* Online Status Indicator */}
              <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800">
                <div className="flex items-center space-x-2">
                  <div className={`w-2 h-2 rounded-full ${
                    isOnline ? 'bg-emerald-500 animate-pulse' : 'bg-slate-400'
                  }`} />
                  <span className="text-xs text-slate-600 dark:text-slate-400">
                    {isOnline ? 'Connected' : 'Disconnected'}
                  </span>
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      {filteredChargers.length === 0 && (
        <Card className="p-12 border-slate-200 dark:border-slate-800">
          <div className="text-center text-slate-500 dark:text-slate-400">
            <Activity className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No chargers found for selected filter</p>
          </div>
        </Card>
      )}
    </div>
  );
};

export default Chargers;