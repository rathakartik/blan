import React from 'react';
import { useQuery } from 'react-query';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import StatsCard from '../components/StatsCard';
import { 
  Globe, 
  MessageCircle, 
  Users, 
  Activity,
  Plus,
  ExternalLink,
  TrendingUp
} from 'lucide-react';
import { format } from 'date-fns';

const DashboardPage = () => {
  const { data: stats, isLoading, error } = useQuery(
    'dashboardStats',
    () => api.getDashboardStats(),
    {
      refetchInterval: 30000, // Refresh every 30 seconds
    }
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-error-600 mb-4">
          <Activity className="h-12 w-12 mx-auto" />
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">Failed to load dashboard</h3>
        <p className="text-gray-600">Please try refreshing the page</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-1">Welcome back! Here's what's happening with your voice assistants.</p>
        </div>
        <Link
          to="/sites/new"
          className="btn btn-primary"
        >
          <Plus className="h-4 w-4 mr-2" />
          Add Site
        </Link>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard
          title="Total Sites"
          value={stats?.total_sites || 0}
          icon={Globe}
          color="primary"
        />
        <StatsCard
          title="Total Interactions"
          value={stats?.total_interactions || 0}
          icon={MessageCircle}
          color="success"
        />
        <StatsCard
          title="Active Sessions"
          value={stats?.active_sessions || 0}
          icon={Users}
          color="warning"
        />
        <StatsCard
          title="Conversations"
          value={stats?.total_conversations || 0}
          icon={Activity}
          color="secondary"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Recent Interactions */}
        <div className="card">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Recent Interactions</h3>
          </div>
          <div className="p-6">
            {stats?.recent_interactions?.length > 0 ? (
              <div className="space-y-4">
                {stats.recent_interactions.slice(0, 5).map((interaction) => (
                  <div key={interaction.id} className="flex items-center justify-between py-2">
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">
                        {interaction.interaction_type?.replace('_', ' ').toUpperCase()}
                      </p>
                      <p className="text-sm text-gray-500">
                        {interaction.user_message ? 
                          `"${interaction.user_message.substring(0, 50)}${interaction.user_message.length > 50 ? '...' : ''}"`
                          : 'System interaction'
                        }
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-gray-500">
                        {format(new Date(interaction.timestamp), 'MMM d, HH:mm')}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <MessageCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">No interactions yet</p>
              </div>
            )}
          </div>
        </div>

        {/* Site Performance */}
        <div className="card">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-900">Site Performance</h3>
              <Link
                to="/analytics"
                className="text-primary-600 hover:text-primary-500 text-sm font-medium"
              >
                View all
              </Link>
            </div>
          </div>
          <div className="p-6">
            {stats?.site_performance?.length > 0 ? (
              <div className="space-y-4">
                {stats.site_performance.slice(0, 5).map((site) => (
                  <div key={site.site_id} className="flex items-center justify-between py-2">
                    <div className="flex items-center space-x-3">
                      <div className="h-8 w-8 bg-primary-100 rounded-full flex items-center justify-center">
                        <Globe className="h-4 w-4 text-primary-600" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {site.site_name}
                        </p>
                        <p className="text-sm text-gray-500">
                          {site.interactions} interactions
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <TrendingUp className="h-4 w-4 text-success-600" />
                      <Link
                        to={`/sites/${site.site_id}`}
                        className="text-primary-600 hover:text-primary-500"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <Globe className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500 mb-4">No sites created yet</p>
                <Link
                  to="/sites/new"
                  className="btn btn-primary"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Create your first site
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Quick Actions</h3>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Link
              to="/sites/new"
              className="flex items-center p-4 border-2 border-dashed border-gray-200 rounded-lg hover:border-primary-300 hover:bg-primary-50 transition-colors duration-200"
            >
              <Plus className="h-8 w-8 text-gray-400 mr-3" />
              <div>
                <p className="font-medium text-gray-900">Add New Site</p>
                <p className="text-sm text-gray-500">Create a new voice assistant</p>
              </div>
            </Link>
            
            <Link
              to="/analytics"
              className="flex items-center p-4 border-2 border-dashed border-gray-200 rounded-lg hover:border-primary-300 hover:bg-primary-50 transition-colors duration-200"
            >
              <TrendingUp className="h-8 w-8 text-gray-400 mr-3" />
              <div>
                <p className="font-medium text-gray-900">View Analytics</p>
                <p className="text-sm text-gray-500">Check performance metrics</p>
              </div>
            </Link>
            
            <Link
              to="/settings"
              className="flex items-center p-4 border-2 border-dashed border-gray-200 rounded-lg hover:border-primary-300 hover:bg-primary-50 transition-colors duration-200"
            >
              <Activity className="h-8 w-8 text-gray-400 mr-3" />
              <div>
                <p className="font-medium text-gray-900">Settings</p>
                <p className="text-sm text-gray-500">Configure your account</p>
              </div>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;