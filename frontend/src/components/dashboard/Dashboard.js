import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../../contexts/AuthContext';
import {
  GlobeAltIcon,
  ChatBubbleLeftRightIcon,
  UserGroupIcon,
  EyeIcon,
  PlusIcon,
  ArrowTrendingUpIcon,
  CurrencyDollarIcon,
  BoltIcon
} from '@heroicons/react/24/outline';

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [roiHighlights, setROIHighlights] = useState(null);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  useEffect(() => {
    fetchDashboardStats();
    fetchROIHighlights();
  }, []);

  const fetchDashboardStats = async () => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/analytics/dashboard`);
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchROIHighlights = async () => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/analytics/dashboard`);
      if (response.data?.site_performance?.length > 0) {
        // Get ROI data for the top performing site
        const topSite = response.data.site_performance[0];
        try {
          const roiResponse = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/sites/${topSite.site_id}/roi-report?days=30`);
          setROIHighlights(roiResponse.data);
        } catch (roiError) {
          console.log('ROI data not available for top site');
        }
      }
    } catch (error) {
      console.error('Error fetching ROI highlights:', error);
    }
  };

  const statCards = [
    {
      name: 'Total Sites',
      value: stats?.total_sites || 0,
      icon: GlobeAltIcon,
      color: 'blue',
      href: '/dashboard/sites'
    },
    {
      name: 'Total Interactions',
      value: stats?.total_interactions || 0,
      icon: ChatBubbleLeftRightIcon,
      color: 'green',
      href: '/dashboard/analytics'
    },
    {
      name: 'Total Conversations',
      value: stats?.total_conversations || 0,
      icon: UserGroupIcon,
      color: 'purple',
      href: '/dashboard/analytics'
    },
    {
      name: 'Active Sessions',
      value: stats?.active_sessions || 0,
      icon: EyeIcon,
      color: 'yellow',
      href: '/dashboard/analytics'
    }
  ];

  const getColorClasses = (color) => {
    const colors = {
      blue: 'bg-blue-500 text-blue-100',
      green: 'bg-green-500 text-green-100',
      purple: 'bg-purple-500 text-purple-100',
      yellow: 'bg-yellow-500 text-yellow-100'
    };
    return colors[color] || colors.blue;
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

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-gray-600">Welcome back, {user?.full_name}</p>
          </div>
          <Link
            to="/dashboard/sites/new"
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            <PlusIcon className="h-4 w-4 mr-2" />
            New Site
          </Link>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {statCards.map((card) => (
          <Link
            key={card.name}
            to={card.href}
            className="bg-white rounded-lg shadow hover:shadow-md transition-shadow p-6"
          >
            <div className="flex items-center">
              <div className={`p-3 rounded-md ${getColorClasses(card.color)}`}>
                <card.icon className="h-6 w-6" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">{card.name}</p>
                <p className="text-2xl font-semibold text-gray-900">{card.value}</p>
              </div>
            </div>
          </Link>
        ))}
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Interactions */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Interactions</h3>
            {stats?.recent_interactions?.length > 0 ? (
              <div className="space-y-3">
                {stats.recent_interactions.slice(0, 5).map((interaction, index) => (
                  <div key={index} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                    <div className="flex-1">
                      <p className="text-sm text-gray-900">{interaction.interaction_type}</p>
                      <p className="text-xs text-gray-500">
                        {new Date(interaction.timestamp).toLocaleDateString()} {new Date(interaction.timestamp).toLocaleTimeString()}
                      </p>
                    </div>
                    <div className="text-sm text-gray-500">
                      Session: {interaction.session_id.slice(0, 8)}...
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-sm">No recent interactions</p>
            )}
          </div>
        </div>

        {/* Site Performance */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Site Performance</h3>
            {stats?.site_performance?.length > 0 ? (
              <div className="space-y-3">
                {stats.site_performance.slice(0, 5).map((site, index) => (
                  <div key={index} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">{site.site_name}</p>
                      <p className="text-xs text-gray-500">Site ID: {site.site_id.slice(0, 8)}...</p>
                    </div>
                    <div className="flex items-center text-sm text-gray-500">
                      <ArrowTrendingUpIcon className="h-4 w-4 mr-1" />
                      {site.interactions} interactions
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <GlobeAltIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500 text-sm mb-4">No sites created yet</p>
                <Link
                  to="/dashboard/sites/new"
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                >
                  <PlusIcon className="h-4 w-4 mr-2" />
                  Create Your First Site
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;