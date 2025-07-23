import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import {
  ChartBarIcon,
  CurrencyDollarIcon,
  UserGroupIcon,
  BoltIcon,
  TrendingUpIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  GlobeAltIcon,
  ChatBubbleLeftRightIcon,
  HeartIcon,
  MagnifyingGlassIcon
} from '@heroicons/react/24/outline';

const ROIDashboard = () => {
  const { id: siteId } = useParams();
  const [roiData, setROIData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [timeframe, setTimeframe] = useState(30);

  useEffect(() => {
    if (siteId) {
      fetchROIData();
    }
  }, [siteId, timeframe]);

  const fetchROIData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [roiResponse, journeysResponse, intelligenceResponse] = await Promise.all([
        axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/sites/${siteId}/roi-report?days=${timeframe}`),
        axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/sites/${siteId}/user-journeys?days=${timeframe}`),
        axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/sites/${siteId}/intelligence`)
      ]);
      
      setROIData({
        roi: roiResponse.data,
        journeys: journeysResponse.data,
        intelligence: intelligenceResponse.data
      });
    } catch (error) {
      console.error('Error fetching ROI data:', error);
      setError(error.response?.data?.detail || 'Failed to fetch ROI data');
    } finally {
      setLoading(false);
    }
  };

  const triggerCrawl = async () => {
    try {
      setLoading(true);
      await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/sites/${siteId}/crawl`);
      // Refresh data after crawl
      setTimeout(() => {
        fetchROIData();
      }, 5000);
    } catch (error) {
      console.error('Error triggering crawl:', error);
      setError('Failed to start website crawl');
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(value || 0);
  };

  const formatPercentage = (value) => {
    return `${(value || 0).toFixed(1)}%`;
  };

  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4'];

  if (loading) {
    return (
      <div className="p-6">
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
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error Loading ROI Data</h3>
              <p className="mt-2 text-sm text-red-700">{error}</p>
              {error.includes('No intelligence data') && (
                <button
                  onClick={triggerCrawl}
                  className="mt-3 bg-red-600 text-white px-4 py-2 rounded-md text-sm hover:bg-red-700"
                >
                  Start Website Analysis
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  const roi = roiData?.roi;
  const journeys = roiData?.journeys;
  const intelligence = roiData?.intelligence;

  // Prepare chart data
  const intentData = roi?.detailed_metrics?.intent_analytics?.intent_distribution?.map(item => ({
    name: item.intent.replace('_', ' ').toTitleCase(),
    value: item.count,
    confidence: item.avg_confidence * 100
  })) || [];

  const journeyStageData = roi?.detailed_metrics?.intent_analytics?.journey_distribution?.map(item => ({
    name: item.stage.charAt(0).toUpperCase() + item.stage.slice(1),
    value: item.count
  })) || [];

  const roiMetrics = roi?.roi_summary || {};
  const engagementMetrics = roi?.detailed_metrics?.engagement_metrics || {};
  const conversionMetrics = roi?.detailed_metrics?.conversion_metrics || {};

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">ROI Intelligence Dashboard</h1>
            <p className="text-gray-600">Website intelligence and ROI metrics for your AI assistant</p>
          </div>
          <div className="flex items-center space-x-4">
            <select
              value={timeframe}
              onChange={(e) => setTimeframe(Number(e.target.value))}
              className="border border-gray-300 rounded-md px-3 py-2 bg-white"
            >
              <option value={7}>Last 7 days</option>
              <option value={30}>Last 30 days</option>
              <option value={90}>Last 90 days</option>
            </select>
            <button
              onClick={triggerCrawl}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 flex items-center"
            >
              <MagnifyingGlassIcon className="h-4 w-4 mr-2" />
              Refresh Analysis
            </button>
          </div>
        </div>
      </div>

      {/* ROI Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-md bg-green-500 text-green-100">
              <CurrencyDollarIcon className="h-6 w-6" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Monthly Value</p>
              <p className="text-2xl font-semibold text-gray-900">
                {formatCurrency(roiMetrics.total_monthly_value)}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-md bg-blue-500 text-blue-100">
              <UserGroupIcon className="h-6 w-6" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">User Satisfaction</p>
              <p className="text-2xl font-semibold text-gray-900">
                {formatPercentage(roiMetrics.user_satisfaction)}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-md bg-purple-500 text-purple-100">
              <TrendingUpIcon className="h-6 w-6" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Conversion Rate</p>
              <p className="text-2xl font-semibold text-gray-900">
                {formatPercentage(roiMetrics.conversion_rate)}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-md bg-yellow-500 text-yellow-100">
              <BoltIcon className="h-6 w-6" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">AI Effectiveness</p>
              <p className="text-2xl font-semibold text-gray-900">
                {formatPercentage(roiMetrics.ai_effectiveness)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* User Intent Distribution */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">User Intent Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={intentData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {intentData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Journey Stage Analysis */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">User Journey Stages</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={journeyStageData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#3B82F6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Detailed Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Engagement Metrics */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
            <HeartIcon className="h-5 w-5 mr-2 text-red-500" />
            Engagement Metrics
          </h3>
          <div className="space-y-4">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Total Visitors</span>
              <span className="font-semibold">{engagementMetrics.total_visitors || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Page Views</span>
              <span className="font-semibold">{engagementMetrics.total_page_views || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Pages per Session</span>
              <span className="font-semibold">{(engagementMetrics.pages_per_session || 0).toFixed(1)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Avg Session Duration</span>
              <span className="font-semibold">{Math.round(engagementMetrics.avg_session_duration || 0)}s</span>
            </div>
          </div>
        </div>

        {/* Conversion Metrics */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
            <CheckCircleIcon className="h-5 w-5 mr-2 text-green-500" />
            Conversion Metrics
          </h3>
          <div className="space-y-4">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Total Conversions</span>
              <span className="font-semibold">{conversionMetrics.total_conversions || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">AI Interactions</span>
              <span className="font-semibold">{conversionMetrics.ai_interactions || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Intent Accuracy</span>
              <span className="font-semibold">{formatPercentage(conversionMetrics.intent_accuracy)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Conversion Rate</span>
              <span className="font-semibold text-green-600">{formatPercentage(conversionMetrics.conversion_rate)}</span>
            </div>
          </div>
        </div>

        {/* Cost Savings */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
            <CurrencyDollarIcon className="h-5 w-5 mr-2 text-green-500" />
            Cost Savings
          </h3>
          <div className="space-y-4">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Support Savings</span>
              <span className="font-semibold text-green-600">
                {formatCurrency(roiMetrics.support_cost_savings)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Tickets Prevented</span>
              <span className="font-semibold">{roi?.detailed_metrics?.roi_metrics?.estimated_tickets_prevented || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Navigation Efficiency</span>
              <span className="font-semibold">{formatPercentage(roi?.detailed_metrics?.roi_metrics?.navigation_efficiency)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">AI Resolution Rate</span>
              <span className="font-semibold">{formatPercentage(roi?.detailed_metrics?.roi_metrics?.ai_resolution_rate)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Recommendations */}
      {roi?.recommendations && roi.recommendations.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
            <InformationCircleIcon className="h-5 w-5 mr-2 text-blue-500" />
            ROI Improvement Recommendations
          </h3>
          <div className="space-y-3">
            {roi.recommendations.map((recommendation, index) => (
              <div key={index} className="flex items-start">
                <div className="flex-shrink-0 w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center mr-3">
                  <span className="text-blue-600 text-sm font-medium">{index + 1}</span>
                </div>
                <p className="text-sm text-gray-700">{recommendation}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Website Intelligence Summary */}
      {intelligence?.intelligence_data && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
            <GlobeAltIcon className="h-5 w-5 mr-2 text-blue-500" />
            Website Intelligence Summary
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {intelligence.intelligence_data.total_pages || 0}
              </div>
              <div className="text-sm text-gray-600">Pages Analyzed</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {Object.keys(intelligence.intelligence_data.intent_mapping || {}).length}
              </div>
              <div className="text-sm text-gray-600">Intent Categories</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {intelligence.intelligence_data.roi_metrics?.navigation_efficiency?.toFixed(0) || 0}%
              </div>
              <div className="text-sm text-gray-600">Navigation Score</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">
                {intelligence.intelligence_data.roi_metrics?.content_optimization_score?.toFixed(0) || 0}%
              </div>
              <div className="text-sm text-gray-600">Content Quality</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Helper function to convert to title case
String.prototype.toTitleCase = function() {
  return this.replace(/\w\S*/g, (txt) => txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase());
};

export default ROIDashboard;