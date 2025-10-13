import React, { useState, useEffect } from 'react';
import { Card } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import api from '../utils/api';
import { ScrollText, Search, Filter } from 'lucide-react';

const Logs = () => {
  const [logs, setLogs] = useState([]);
  const [filteredLogs, setFilteredLogs] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [chargerFilter, setChargerFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [chargers, setChargers] = useState([]);

  const fetchLogs = async () => {
    try {
      const [logsRes, chargersRes] = await Promise.all([
        api.get('/api/logs'),
        api.get('/api/chargers')
      ]);
      setLogs(logsRes.data.logs || []);
      setFilteredLogs(logsRes.data.logs || []);
      setChargers(chargersRes.data.chargers || []);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching logs:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
    const interval = setInterval(fetchLogs, 10000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    let filtered = logs;

    // Filter by charger
    if (chargerFilter !== 'all') {
      filtered = filtered.filter((log) => log.chargerName === chargerFilter);
    }

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(
        (log) =>
          log.userName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          log.chargerName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          log.ID?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    setFilteredLogs(filtered);
  }, [searchTerm, chargerFilter, logs]);

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-slate-600 dark:text-slate-400">Loading logs...</div>
      </div>
    );
  }

  const chargerOptions = ['all', ...new Set(chargers.map((c) => c.name))];

  return (
    <div className="space-y-6" data-testid="logs-page">
      {/* Header */}
      <div className="flex items-center space-x-3">
        <ScrollText className="h-6 w-6 text-slate-600 dark:text-slate-400" />
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Energy Logs</h2>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Real-time meter data readings from all chargers
          </p>
        </div>
      </div>

      {/* Filters */}
      <Card className="p-6 border-slate-200 dark:border-slate-800">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700 dark:text-slate-300 flex items-center">
              <Search className="h-4 w-4 mr-2" />
              Search
            </label>
            <Input
              placeholder="Search by user, charger, or ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              data-testid="logs-search-input"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700 dark:text-slate-300 flex items-center">
              <Filter className="h-4 w-4 mr-2" />
              Filter by Charger
            </label>
            <Select value={chargerFilter} onValueChange={setChargerFilter}>
              <SelectTrigger data-testid="logs-charger-filter">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {chargerOptions.map((option) => (
                  <SelectItem key={option} value={option}>
                    {option === 'all' ? 'All Chargers' : option}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        <div className="mt-4 flex items-center justify-between">
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Showing {filteredLogs.length} of {logs.length} logs
          </p>
          <Badge variant="secondary">{filteredLogs.length} Results</Badge>
        </div>
      </Card>

      {/* Logs Table */}
      <Card className="border-slate-200 dark:border-slate-800">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Timestamp</TableHead>
                <TableHead>ID</TableHead>
                <TableHead>User</TableHead>
                <TableHead>Charger</TableHead>
                <TableHead className="text-right">Power (W)</TableHead>
                <TableHead className="text-right">Energy (Wh)</TableHead>
                <TableHead className="text-right">Frequency (Hz)</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredLogs.map((log) => (
                <TableRow key={log.ID}>
                  <TableCell className="text-sm">{formatTimestamp(log.timestamp)}</TableCell>
                  <TableCell>
                    <code className="text-xs bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">
                      {log.ID}
                    </code>
                  </TableCell>
                  <TableCell className="font-medium">{log.userName}</TableCell>
                  <TableCell>
                    <Badge variant="outline">{log.chargerName}</Badge>
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    {log.totalPower.toFixed(0)}
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    {log.deliveredEnergy.toFixed(2)}
                  </TableCell>
                  <TableCell className="text-right font-mono">{log.frequency}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
        {filteredLogs.length === 0 && (
          <div className="text-center py-12 text-slate-500 dark:text-slate-400">
            <ScrollText className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No logs found matching your criteria</p>
          </div>
        )}
      </Card>
    </div>
  );
};

export default Logs;