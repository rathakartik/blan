import React, { useState } from 'react';
import { useQuery } from 'react-query';
import { api } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import StatsCard from '../components/StatsCard';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { 
  Calendar,
  Download,
  Filter,
  TrendingUp,
  MessageCircle,
  Users,
  Activity,
  Mic,
  Globe,
  BarChart3
} from 'lucide-react';
import { format, subDays } from 'date-fns';

const AnalyticsPage = () => {
  const [selectedSite, setSelectedSite] = useState('all');
  const [dateRange, setDateRange] = useState('30');

  const { data: sites, isLoading: sitesLoading } = useQuery(
    'sites',
    () => api.getSites()
  );

  const { data: dashboardStats, isLoading: dashboardLoading } = useQuery(
    'dashboardStats',
    () => api.getDashboardStats()
  );

  const { data: siteAnalytics, isLoading: analyticsLoading } = useQuery(
    ['siteAnalytics', selectedSite, dateRange],
    () => selectedSite === 'all' 
      ? null 
      : api.getSiteAnalytics(selectedSite, parseInt(dateRange)),
    {
      enabled: selectedSite !== 'all'
    }
  );

  const isLoading = sitesLoading || dashboardLoading || analyticsLoading;

  // Colors for charts
  const colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4'];

  // Prepare chart data
  const interactionTypesData = siteAnalytics?.top_interaction_types?.map((type, index) => ({
    name: type.type.replace('_', ' ').toUpperCase(),
    value: type.count,
    color: colors[index % colors.length]
  })) || [];

  const dailyStatsData = siteAnalytics?.daily_stats?.map(stat => ({
    date: format(new Date(stat.date), 'MMM d'),
    interactions: stat.interactions,
    sessions: stat.sessions
  })) || [];

  const popularQuestionsData = siteAnalytics?.popular_questions?.slice(0, 10).map((q, index) => ({
    question: q.question.length > 30 ? q.question.substring(0, 30) + '...' : q.question,
    count: q.count,
    color: colors[index % colors.length]
  })) || [];

  // Calculate growth percentages (mock data for now)
  const getGrowthPercentage = (current, previous) => {
    if (!previous) return 0;
    return ((current - previous) / previous * 100).toFixed(1);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
          <p className="text-gray-600 mt-1">
            Detailed insights and performance metrics for your AI voice assistants
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button className="btn btn-secondary">
            <Download className="h-4 w-4 mr-2" />
            Export Report
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="p-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Globe className="h-4 w-4 text-gray-400" />
                <select
                  value={selectedSite}
                  onChange={(e) => setSelectedSite(e.target.value)}
                  className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-primary-500 focus:border-primary-500"
                >
                  <option value="all">All Sites</option>
                  {sites?.map(site => (
                    <option key={site.id} value={site.id}>{site.name}</option>
                  ))}
                </select>
              </div>
              <div className="flex items-center space-x-2">
                <Calendar className="h-4 w-4 text-gray-400" />
                <select
                  value={dateRange}
                  onChange={(e) => setDateRange(e.target.value)}
                  className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-primary-500 focus:border-primary-500"
                >
                  <option value="7">Last 7 days</option>
                  <option value="30">Last 30 days</option>
                  <option value="90">Last 90 days</option>
                  <option value="365">Last year</option>
                </select>
              </div>
            </div>
            <div className="text-sm text-gray-500">
              Updated {format(new Date(), 'MMM d, yyyy HH:mm')}
            </div>
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center min-h-96">
          <LoadingSpinner size="large" />
        </div>
      ) : (
        <>
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatsCard
              title="Total Interactions"
              value={selectedSite === 'all' 
                ? dashboardStats?.total_interactions || 0 
                : siteAnalytics?.total_interactions || 0}
              change="+12.5% from last month"
              changeType="positive"
              icon={MessageCircle}
              color="primary"
            />
            <StatsCard
              title="Total Sessions"
              value={selectedSite === 'all' 
                ? dashboardStats?.active_sessions || 0 
                : siteAnalytics?.total_sessions || 0}
              change="+8.3% from last month"
              changeType="positive"
              icon={Users}
              color="success"
            />
            <StatsCard
              title="Conversations"
              value={selectedSite === 'all' 
                ? dashboardStats?.total_conversations || 0 
                : siteAnalytics?.total_conversations || 0}
              change="+15.2% from last month"
              changeType="positive"
              icon={Activity}
              color="warning"
            />
            <StatsCard
              title="Avg Session Duration"
              value={`${siteAnalytics?.avg_session_duration?.toFixed(1) || 0}min`}
              change="+2.1% from last month"
              changeType="positive"
              icon={TrendingUp}
              color="secondary"
            />
          </div>

          {selectedSite === 'all' ? (
            /* All Sites Overview */
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Site Performance */}
              <div className="card">
                <div className="p-6 border-b border-gray-200">
                  <h3 className="text-lg font-medium text-gray-900 flex items-center">
                    <BarChart3 className="h-5 w-5 mr-2" />
                    Site Performance
                  </h3>
                </div>
                <div className="p-6">
                  {dashboardStats?.site_performance?.length > 0 ? (
                    <div className="space-y-4">
                      {dashboardStats.site_performance.map((site, index) => (
                        <div key={site.site_id} className="flex items-center justify-between">
                          <div className="flex items-center space-x-3">
                            <div className={`w-3 h-3 rounded-full`} style={{ backgroundColor: colors[index % colors.length] }}></div>
                            <span className="font-medium">{site.site_name}</span>
                          </div>
                          <span className="text-gray-600">{site.interactions} interactions</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-500 text-center py-8">No site data available</p>
                  )}
                </div>
              </div>

              {/* Quick Stats */}
              <div className="card">
                <div className="p-6 border-b border-gray-200">
                  <h3 className="text-lg font-medium text-gray-900">Quick Stats</h3>
                </div>
                <div className="p-6">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-gray-900">{dashboardStats?.total_sites || 0}</div>
                      <div className="text-sm text-gray-600">Total Sites</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-gray-900">{dashboardStats?.active_sessions || 0}</div>
                      <div className="text-sm text-gray-600">Active Sessions</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-gray-900">
                        {sites?.filter(s => s.is_active).length || 0}
                      </div>
                      <div className="text-sm text-gray-600">Active Sites</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-gray-900">
                        {sites?.filter(s => s.voice_enabled).length || 0}
                      </div>
                      <div className="text-sm text-gray-600">Voice Enabled</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            /* Individual Site Analytics */
            <div className="space-y-6">
              {/* Daily Activity Chart */}
              <div className="card">
                <div className="p-6 border-b border-gray-200">
                  <h3 className="text-lg font-medium text-gray-900">Daily Activity</h3>
                </div>
                <div className="p-6">
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={dailyStatsData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" />
                        <YAxis />
                        <Tooltip />
                        <Line 
                          type="monotone" 
                          dataKey="interactions" 
                          stroke="#3B82F6" 
                          strokeWidth={2}
                          name="Interactions"
                        />
                        <Line 
                          type="monotone" 
                          dataKey="sessions" 
                          stroke="#10B981" 
                          strokeWidth={2}
                          name="Sessions"
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Interaction Types */}
                <div className="card">
                  <div className="p-6 border-b border-gray-200">
                    <h3 className="text-lg font-medium text-gray-900">Interaction Types</h3>
                  </div>
                  <div className="p-6">
                    <div className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={interactionTypesData}
                            cx="50%"
                            cy="50%"
                            outerRadius={80}
                            dataKey="value"
                            label={({name, percent}) => `${name} ${(percent * 100).toFixed(0)}%`}
                          >
                            {interactionTypesData.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                          </Pie>
                          <Tooltip />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </div>

                {/* Popular Questions */}
                <div className="card">
                  <div className="p-6 border-b border-gray-200">
                    <h3 className="text-lg font-medium text-gray-900">Popular Questions</h3>
                  </div>
                  <div className="p-6">
                    <div className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={popularQuestionsData} layout="horizontal">
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis type="number" />
                          <YAxis dataKey="question" type="category" width={150} />
                          <Tooltip />
                          <Bar dataKey="count" fill="#3B82F6" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default AnalyticsPage;