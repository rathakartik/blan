import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  ChartBarIcon,
  GlobeAltIcon,
  UsersIcon,
  ChatBubbleLeftRightIcon,
  CodeBracketIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon
} from '@heroicons/react/24/outline';

const AdminDashboard = () => {
  const [stats, setStats] = useState(null);
  const [systemHealth, setSystemHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDashboardData();
    
    // Set up periodic refresh
    const interval = setInterval(fetchDashboardData, 30000); // 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [statsResponse, healthResponse] = await Promise.all([
        axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/analytics/dashboard`),
        axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/health`)
      ]);
      
      setStats(statsResponse.data);
      setSystemHealth(healthResponse.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num) => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num?.toString() || '0';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy':
      case 'connected':
        return 'text-green-500';
      case 'degraded':
      case 'demo_mode':
        return 'text-yellow-500';
      case 'error':
      case 'disconnected':
        return 'text-red-500';
      default:
        return 'text-gray-500';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy':
      case 'connected':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'degraded':
      case 'demo_mode':
        return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />;
      case 'error':
      case 'disconnected':
        return <XCircleIcon className="h-5 w-5 text-red-500" />;
      default:
        return <ClockIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  if (loading) {
    return (
      <div className="p-4 sm:p-6 lg:p-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-300 rounded w-1/4 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-white rounded-lg shadow p-6">
                <div className="h-4 bg-gray-300 rounded w-3/4 mb-2"></div>
                <div className="h-8 bg-gray-300 rounded w-1/2"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 sm:p-6 lg:p-8">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
            <p className="text-gray-600">Monitor your AI Voice Assistant platform</p>
          </div>
          
          <div className="flex items-center gap-2">
            <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm ${
              systemHealth?.status === 'healthy' 
                ? 'bg-green-100 text-green-800' 
                : 'bg-yellow-100 text-yellow-800'
            }`}>
              {getStatusIcon(systemHealth?.status)}
              <span className="capitalize">{systemHealth?.status || 'Unknown'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <GlobeAltIcon className="h-8 w-8 text-blue-500" />
            </div>
            <div className="ml-4">
              <div className="text-2xl font-bold text-gray-900">
                {formatNumber(stats?.total_sites || 0)}
              </div>
              <div className="text-sm text-gray-600">Active Sites</div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ChatBubbleLeftRightIcon className="h-8 w-8 text-green-500" />
            </div>
            <div className="ml-4">
              <div className="text-2xl font-bold text-gray-900">
                {formatNumber(stats?.total_interactions || 0)}
              </div>
              <div className="text-sm text-gray-600">Total Interactions</div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <UsersIcon className="h-8 w-8 text-purple-500" />
            </div>
            <div className="ml-4">
              <div className="text-2xl font-bold text-gray-900">
                {formatNumber(stats?.total_conversations || 0)}
              </div>
              <div className="text-sm text-gray-600">Conversations</div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ChartBarIcon className="h-8 w-8 text-orange-500" />
            </div>
            <div className="ml-4">
              <div className="text-2xl font-bold text-gray-900">
                {formatNumber(stats?.active_sessions || 0)}
              </div>
              <div className="text-sm text-gray-600">Active Sessions</div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        {/* Main Content */}
        <div className="xl:col-span-2 space-y-6">
          {/* System Health */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-6">System Health</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Database Status */}
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-600">MongoDB</span>
                  {getStatusIcon(systemHealth?.services?.mongodb?.status)}
                </div>
                <div className={`text-xs ${getStatusColor(systemHealth?.services?.mongodb?.status)}`}>
                  {systemHealth?.services?.mongodb?.status || 'Unknown'}
                </div>
                {systemHealth?.services?.mongodb?.response_time && (
                  <div className="text-xs text-gray-500 mt-1">
                    {systemHealth.services.mongodb.response_time}
                  </div>
                )}
              </div>

              {/* GROQ API Status */}
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-600">GROQ API</span>
                  {getStatusIcon(systemHealth?.services?.groq?.status)}
                </div>
                <div className={`text-xs ${getStatusColor(systemHealth?.services?.groq?.status)}`}>
                  {systemHealth?.services?.groq?.status || 'Unknown'}
                </div>
                {systemHealth?.services?.groq?.model && (
                  <div className="text-xs text-gray-500 mt-1">
                    {systemHealth.services.groq.model}
                  </div>
                )}
              </div>

              {/* Rate Limiting */}
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-600">Rate Limiting</span>
                  <CheckCircleIcon className="h-5 w-5 text-green-500" />
                </div>
                <div className="text-xs text-green-500">Active</div>
                <div className="text-xs text-gray-500 mt-1">
                  {systemHealth?.rate_limiting?.active_connections || 0} connections
                </div>
              </div>
            </div>
          </div>

          {/* Top Performing Sites */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-6">Top Performing Sites</h2>
            
            <div className="space-y-4">
              {stats?.site_performance?.slice(0, 5).map((site, index) => (
                <div key={index} className="flex items-center">
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center text-sm font-semibold text-blue-600">
                    {index + 1}
                  </div>
                  <div className="ml-4 flex-1">
                    <div className="text-sm font-medium text-gray-900">{site.site_name}</div>
                    <div className="text-xs text-gray-500">{site.site_id}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium text-gray-900">{site.interactions}</div>
                    <div className="text-xs text-gray-500">interactions</div>
                  </div>
                </div>
              )) || (
                <p className="text-sm text-gray-500">No site data available</p>
              )}
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Quick Actions */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
            
            <div className="space-y-3">
              <button className="w-full flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700">
                <GlobeAltIcon className="h-4 w-4 mr-2" />
                Add New Site
              </button>
              
              <button className="w-full flex items-center justify-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
                <CodeBracketIcon className="h-4 w-4 mr-2" />
                Generate Embed Code
              </button>
              
              <button className="w-full flex items-center justify-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
                <ChartBarIcon className="h-4 w-4 mr-2" />
                View Analytics
              </button>
            </div>
          </div>

          {/* Recent Activity */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
            
            <div className="space-y-3">
              {stats?.recent_interactions?.slice(0, 5).map((interaction, index) => (
                <div key={index} className="flex items-start gap-3">
                  <div className="h-2 w-2 bg-blue-400 rounded-full mt-2 flex-shrink-0"></div>
                  <div className="flex-1">
                    <div className="text-sm text-gray-900 capitalize">
                      {interaction.interaction_type?.replace('_', ' ') || 'Unknown'}
                    </div>
                    <div className="text-xs text-gray-500">
                      {new Date(interaction.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              )) || (
                <p className="text-sm text-gray-500">No recent activity</p>
              )}
            </div>
          </div>

          {/* System Metrics */}
          <div className="bg-gray-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">System Metrics</h3>
            
            <div className="space-y-4">
              {systemHealth?.metrics?.memory_usage && (
                <div>
                  <div className="text-sm text-gray-600">Memory Usage</div>
                  <div className="text-lg font-bold text-blue-600">
                    {systemHealth.metrics.memory_usage}
                  </div>
                </div>
              )}
              
              {systemHealth?.metrics?.cpu_usage && (
                <div>
                  <div className="text-sm text-gray-600">CPU Usage</div>
                  <div className="text-lg font-bold text-green-600">
                    {systemHealth.metrics.cpu_usage}
                  </div>
                </div>
              )}
              
              <div>
                <div className="text-sm text-gray-600">Uptime</div>
                <div className="text-lg font-bold text-purple-600">99.9%</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;