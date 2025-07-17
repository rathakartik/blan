import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import {
  PlusIcon,
  EyeIcon,
  PencilIcon,
  TrashIcon,
  GlobeAltIcon,
  ChartBarIcon,
  CodeBracketIcon
} from '@heroicons/react/24/outline';

const SiteList = () => {
  const [sites, setSites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchSites();
  }, []);

  const fetchSites = async () => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/sites`);
      setSites(response.data);
    } catch (error) {
      console.error('Error fetching sites:', error);
      setError('Failed to load sites');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (siteId) => {
    if (!window.confirm('Are you sure you want to delete this site?')) {
      return;
    }

    try {
      await axios.delete(`${process.env.REACT_APP_BACKEND_URL}/api/sites/${siteId}`);
      setSites(sites.filter(site => site.id !== siteId));
    } catch (error) {
      console.error('Error deleting site:', error);
      alert('Failed to delete site');
    }
  };

  if (loading) {
    return (
      <div className="p-4 sm:p-6 lg:p-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-300 rounded w-1/4 mb-6"></div>
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="bg-white rounded-lg shadow p-6">
                <div className="h-4 bg-gray-300 rounded w-3/4 mb-2"></div>
                <div className="h-4 bg-gray-300 rounded w-1/2"></div>
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
          <p className="text-red-800">{error}</p>
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
            <h1 className="text-2xl font-bold text-gray-900">Sites</h1>
            <p className="text-gray-600">Manage your AI voice assistant sites</p>
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

      {/* Sites List */}
      {sites.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {sites.map((site) => (
            <div key={site.id} className="bg-white rounded-lg shadow hover:shadow-md transition-shadow">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center">
                    <div className="h-10 w-10 bg-blue-100 rounded-lg flex items-center justify-center">
                      <GlobeAltIcon className="h-6 w-6 text-blue-600" />
                    </div>
                    <div className="ml-3">
                      <h3 className="text-lg font-medium text-gray-900">{site.name}</h3>
                      <p className="text-sm text-gray-500">{site.domain}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className={`h-2 w-2 rounded-full ${site.is_active ? 'bg-green-400' : 'bg-red-400'}`} />
                    <span className={`text-xs font-medium ${site.is_active ? 'text-green-600' : 'text-red-600'}`}>
                      {site.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                </div>

                <div className="mb-4">
                  <p className="text-sm text-gray-600 line-clamp-2">{site.description || 'No description'}</p>
                </div>

                <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
                  <div className="flex items-center">
                    <ChartBarIcon className="h-4 w-4 mr-1" />
                    <span>{site.total_interactions || 0} interactions</span>
                  </div>
                  <div className="flex items-center">
                    <EyeIcon className="h-4 w-4 mr-1" />
                    <span>{site.total_conversations || 0} conversations</span>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Link
                      to={`/dashboard/sites/${site.id}/edit`}
                      className="p-2 text-gray-400 hover:text-blue-600 transition-colors"
                      title="Edit site"
                    >
                      <PencilIcon className="h-4 w-4" />
                    </Link>
                    <Link
                      to={`/dashboard/sites/${site.id}/analytics`}
                      className="p-2 text-gray-400 hover:text-green-600 transition-colors"
                      title="View analytics"
                    >
                      <ChartBarIcon className="h-4 w-4" />
                    </Link>
                    <Link
                      to={`/dashboard/sites/${site.id}/embed`}
                      className="p-2 text-gray-400 hover:text-purple-600 transition-colors"
                      title="Get embed code"
                    >
                      <CodeBracketIcon className="h-4 w-4" />
                    </Link>
                    <button
                      onClick={() => handleDelete(site.id)}
                      className="p-2 text-gray-400 hover:text-red-600 transition-colors"
                      title="Delete site"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  </div>
                  <div className="text-xs text-gray-500">
                    Created {new Date(site.created_at).toLocaleDateString()}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <GlobeAltIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No sites yet</h3>
          <p className="text-gray-500 mb-6">Get started by creating your first AI voice assistant site</p>
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
  );
};

export default SiteList;