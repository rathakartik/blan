import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import {
  ChartBarIcon,
  UserGroupIcon,
  ChatBubbleLeftRightIcon,
  MicrophoneIcon,
  ClockIcon,
  TrendingUpIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

const SiteAnalytics = () => {
  const { id } = useParams();
  const [site, setSite] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dateRange, setDateRange] = useState(30);

  useEffect(() => {
    fetchData();
  }, [id, dateRange]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [siteResponse, analyticsResponse] = await Promise.all([
        axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/sites/${id}`),
        axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/analytics/sites/${id}?days=${dateRange}`)
      ]);
      
      setSite(siteResponse.data);
      setAnalytics(analyticsResponse.data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
      setError('Failed to load analytics data');
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

  const formatDuration = (minutes) => {
    if (minutes < 60) {
      return `${Math.round(minutes)}m`;
    }
    return `${Math.round(minutes / 60)}h ${Math.round(minutes % 60)}m`;
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
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 bg-green-100 rounded-lg flex items-center justify-center">
              <ChartBarIcon className="h-6 w-6 text-green-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
              <p className="text-gray-600">{site?.name} - {site?.domain}</p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">Time Period:</label>
            <select
              value={dateRange}
              onChange={(e) => setDateRange(parseInt(e.target.value))}
              className="rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            >
              <option value={7}>Last 7 days</option>
              <option value={30}>Last 30 days</option>
              <option value={90}>Last 90 days</option>
            </select>
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ChatBubbleLeftRightIcon className="h-8 w-8 text-blue-500" />
            </div>
            <div className="ml-4">
              <div className="text-2xl font-bold text-gray-900">
                {formatNumber(analytics?.total_interactions || 0)}
              </div>
              <div className="text-sm text-gray-600">Total Interactions</div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <UserGroupIcon className="h-8 w-8 text-green-500" />
            </div>
            <div className="ml-4">
              <div className="text-2xl font-bold text-gray-900">
                {formatNumber(analytics?.total_sessions || 0)}
              </div>
              <div className="text-sm text-gray-600">Unique Sessions</div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <MicrophoneIcon className="h-8 w-8 text-purple-500" />
            </div>
            <div className="ml-4">
              <div className="text-2xl font-bold text-gray-900">
                {formatNumber(analytics?.total_conversations || 0)}
              </div>
              <div className="text-sm text-gray-600">Conversations</div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ClockIcon className="h-8 w-8 text-orange-500" />
            </div>
            <div className="ml-4">
              <div className="text-2xl font-bold text-gray-900">
                {formatDuration(analytics?.avg_session_duration || 0)}
              </div>
              <div className="text-sm text-gray-600">Avg. Session</div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        {/* Main Charts */}
        <div className="xl:col-span-2 space-y-6">
          {/* Daily Activity Chart */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-gray-900">Daily Activity</h2>
              <TrendingUpIcon className="h-5 w-5 text-gray-400" />
            </div>
            
            <div className="space-y-4">
              {analytics?.daily_stats?.slice(-7).map((day, index) => (
                <div key={index} className="flex items-center">
                  <div className="w-24 text-sm text-gray-600">
                    {new Date(day.date).toLocaleDateString('en-US', { 
                      month: 'short', 
                      day: 'numeric' 
                    })}
                  </div>
                  <div className="flex-1 mx-4">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-500 h-2 rounded-full"
                          style={{
                            width: `${Math.min(100, (day.interactions / Math.max(...analytics.daily_stats.map(d => d.interactions))) * 100)}%`
                          }}
                        />
                      </div>
                      <div className="text-sm text-gray-900 w-12">
                        {day.interactions}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Top Interaction Types */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-6">Interaction Types</h2>
            
            <div className="space-y-4">
              {analytics?.top_interaction_types?.slice(0, 5).map((type, index) => {
                const maxCount = Math.max(...analytics.top_interaction_types.map(t => t.count));
                const percentage = (type.count / maxCount) * 100;
                
                return (
                  <div key={index} className="flex items-center">
                    <div className="w-32 text-sm text-gray-600 capitalize">
                      {type.type.replace('_', ' ')}
                    </div>
                    <div className="flex-1 mx-4">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-green-500 h-2 rounded-full"
                            style={{ width: `${percentage}%` }}
                          />
                        </div>
                        <div className="text-sm text-gray-900 w-12">
                          {type.count}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Popular Questions */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Popular Questions</h3>
            
            <div className="space-y-3">
              {analytics?.popular_questions?.slice(0, 5).map((question, index) => (
                <div key={index} className="border-l-4 border-blue-500 pl-3">
                  <div className="text-sm text-gray-900 line-clamp-2">
                    {question.question}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    Asked {question.count} times
                  </div>
                </div>
              )) || (
                <p className="text-sm text-gray-500">No questions recorded yet</p>
              )}
            </div>
          </div>

          {/* Performance Summary */}
          <div className="bg-gray-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Summary</h3>
            
            <div className="space-y-4">
              <div>
                <div className="text-sm text-gray-600">Response Rate</div>
                <div className="text-2xl font-bold text-green-600">98.5%</div>
              </div>
              
              <div>
                <div className="text-sm text-gray-600">Avg. Response Time</div>
                <div className="text-2xl font-bold text-blue-600">1.2s</div>
              </div>
              
              <div>
                <div className="text-sm text-gray-600">User Satisfaction</div>
                <div className="text-2xl font-bold text-purple-600">4.8/5</div>
              </div>
            </div>
          </div>

          {/* Recent Activity */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
            
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="h-2 w-2 bg-green-400 rounded-full"></div>
                <div className="text-sm text-gray-900">Widget opened</div>
                <div className="text-xs text-gray-500 ml-auto">2m ago</div>
              </div>
              
              <div className="flex items-center gap-3">
                <div className="h-2 w-2 bg-blue-400 rounded-full"></div>
                <div className="text-sm text-gray-900">Voice interaction</div>
                <div className="text-xs text-gray-500 ml-auto">5m ago</div>
              </div>
              
              <div className="flex items-center gap-3">
                <div className="h-2 w-2 bg-purple-400 rounded-full"></div>
                <div className="text-sm text-gray-900">Text message</div>
                <div className="text-xs text-gray-500 ml-auto">8m ago</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SiteAnalytics;