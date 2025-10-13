import React, { useState, useEffect } from 'react';
import { Card } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import api from '../utils/api';
import { Zap, Users, Battery, TrendingUp, Activity, BarChart3 } from 'lucide-react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [usageHistory, setUsageHistory] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [statsRes, historyRes, transactionsRes] = await Promise.all([
        api.get('/api/stats'),
        api.get('/api/usage/history'),
        api.get('/api/transactions')
      ]);
      
      setStats(statsRes.data);
      setUsageHistory(historyRes.data.history);
      setTransactions(Object.entries(transactionsRes.data.transactions));
      setLoading(false);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000); // Poll every 10 seconds
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-slate-600 dark:text-slate-400">Loading dashboard...</div>
      </div>
    );
  }

  const statCards = [
    {
      title: 'Energy Today',
      value: `${stats?.total_energy_today || 0} kWh`,
      icon: Zap,
      color: 'from-emerald-500 to-teal-600',
      bgColor: 'bg-emerald-50 dark:bg-emerald-900/20',
      textColor: 'text-emerald-600 dark:text-emerald-400'
    },
    {
      title: 'Active Sessions',
      value: stats?.active_sessions || 0,
      icon: Activity,
      color: 'from-blue-500 to-cyan-600',
      bgColor: 'bg-blue-50 dark:bg-blue-900/20',
      textColor: 'text-blue-600 dark:text-blue-400'
    },
    {
      title: 'Total Users',
      value: stats?.total_users || 0,
      icon: Users,
      color: 'from-violet-500 to-purple-600',
      bgColor: 'bg-violet-50 dark:bg-violet-900/20',
      textColor: 'text-violet-600 dark:text-violet-400'
    },
    {
      title: 'Active Chargers',
      value: `${stats?.active_chargers || 0} / ${stats?.total_chargers || 0}`,
      icon: Battery,
      color: 'from-amber-500 to-orange-600',
      bgColor: 'bg-amber-50 dark:bg-amber-900/20',
      textColor: 'text-amber-600 dark:text-amber-400'
    }
  ];

  return (
    <div className="space-y-6" data-testid="dashboard-page">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <Card key={index} className="p-6 border-slate-200 dark:border-slate-800 hover:shadow-lg transition-shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-600 dark:text-slate-400 mb-1">{stat.title}</p>
                  <p className="text-3xl font-bold text-slate-900 dark:text-white" data-testid={`stat-${stat.title.toLowerCase().replace(/\s+/g, '-')}`}>{stat.value}</p>
                </div>
                <div className={`p-3 ${stat.bgColor} rounded-xl`}>
                  <Icon className={`h-6 w-6 ${stat.textColor}`} />
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Energy Usage Chart */}
        <Card className="p-6 border-slate-200 dark:border-slate-800">
          <div className="flex items-center space-x-2 mb-6">
            <TrendingUp className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Energy Usage Trend</h3>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={usageHistory}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="date" stroke="#64748b" style={{ fontSize: '12px' }} />
              <YAxis stroke="#64748b" style={{ fontSize: '12px' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#fff',
                  border: '1px solid #e2e8f0',
                  borderRadius: '8px',
                }}
              />
              <Line type="monotone" dataKey="energy" stroke="#10b981" strokeWidth={2} dot={{ fill: '#10b981' }} />
            </LineChart>
          </ResponsiveContainer>
        </Card>

        {/* Total Energy Delivered */}
        <Card className="p-6 border-slate-200 dark:border-slate-800">
          <div className="flex items-center space-x-2 mb-6">
            <BarChart3 className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Total Energy Delivered</h3>
          </div>
          <div className="flex flex-col items-center justify-center h-[300px]">
            <div className="text-6xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-emerald-500 to-teal-600">
              {stats?.total_energy_delivered || 0}
            </div>
            <div className="text-2xl font-medium text-slate-600 dark:text-slate-400 mt-2">kWh</div>
            <div className="text-sm text-slate-500 dark:text-slate-500 mt-4">Lifetime Total</div>
          </div>
        </Card>
      </div>

      {/* Active Sessions */}
      <Card className="p-6 border-slate-200 dark:border-slate-800">
        <div className="flex items-center space-x-2 mb-6">
          <Activity className="h-5 w-5 text-blue-600 dark:text-blue-400" />
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Active Charging Sessions</h3>
          <Badge variant="secondary" className="ml-auto">{transactions.length} Active</Badge>
        </div>
        
        {transactions.length > 0 ? (
          <div className="space-y-4">
            {transactions.map(([txId, tx]) => (
              <div key={txId} className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                <div className="flex items-center space-x-4">
                  <div className="p-2 bg-emerald-100 dark:bg-emerald-900/30 rounded-lg">
                    <Zap className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
                  </div>
                  <div>
                    <p className="font-medium text-slate-900 dark:text-white">{tx.full_name}</p>
                    <p className="text-sm text-slate-600 dark:text-slate-400">{tx.charger_id}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-semibold text-slate-900 dark:text-white">{tx.last_meter.toFixed(2)} kWh</p>
                  <p className="text-xs text-slate-500 dark:text-slate-500">Transaction #{txId}</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12 text-slate-500 dark:text-slate-400">
            No active charging sessions
          </div>
        )}
      </Card>
    </div>
  );
};

export default Dashboard;