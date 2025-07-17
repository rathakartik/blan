import React, { useState } from 'react';
import { useQuery } from 'react-query';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import { 
  Plus, 
  Globe, 
  Search, 
  Filter,
  MoreVertical,
  Edit,
  Trash2,
  ExternalLink,
  Activity,
  Users,
  MessageCircle,
  Eye,
  EyeOff
} from 'lucide-react';
import { format } from 'date-fns';
import toast from 'react-hot-toast';

const SitesPage = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterActive, setFilterActive] = useState('all');
  const [showDropdown, setShowDropdown] = useState(null);

  const { data: sites, isLoading, error, refetch } = useQuery(
    'sites',
    () => api.getSites(),
    {
      onError: (error) => {
        toast.error('Failed to load sites');
      }
    }
  );

  const handleDeleteSite = async (siteId) => {
    if (window.confirm('Are you sure you want to delete this site? This action cannot be undone.')) {
      try {
        await api.deleteSite(siteId);
        toast.success('Site deleted successfully');
        refetch();
      } catch (error) {
        toast.error('Failed to delete site');
      }
    }
  };

  const handleToggleSite = async (siteId, isActive) => {
    try {
      await api.updateSite(siteId, { is_active: !isActive });
      toast.success(isActive ? 'Site disabled' : 'Site enabled');
      refetch();
    } catch (error) {
      toast.error('Failed to update site');
    }
  };

  const filteredSites = sites?.filter(site => {
    const matchesSearch = site.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         site.domain.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterActive === 'all' || 
                         (filterActive === 'active' && site.is_active) ||
                         (filterActive === 'inactive' && !site.is_active);
    return matchesSearch && matchesFilter;
  }) || [];

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
          <Globe className="h-12 w-12 mx-auto" />
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">Failed to load sites</h3>
        <p className="text-gray-600 mb-4">Please try refreshing the page</p>
        <button onClick={() => refetch()} className="btn btn-primary">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Sites</h1>
          <p className="text-gray-600 mt-1">
            Manage your AI voice assistant widgets across different websites
          </p>
        </div>
        <Link to="/sites/new" className="btn btn-primary">
          <Plus className="h-4 w-4 mr-2" />
          Add Site
        </Link>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="p-4 border-b border-gray-200">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
            <div className="flex items-center space-x-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search sites..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                />
              </div>
              <div className="flex items-center space-x-2">
                <Filter className="h-4 w-4 text-gray-400" />
                <select
                  value={filterActive}
                  onChange={(e) => setFilterActive(e.target.value)}
                  className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-primary-500 focus:border-primary-500"
                >
                  <option value="all">All Sites</option>
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                </select>
              </div>
            </div>
            <div className="text-sm text-gray-500">
              {filteredSites.length} of {sites?.length || 0} sites
            </div>
          </div>
        </div>
      </div>

      {/* Sites List */}
      {filteredSites.length === 0 ? (
        <div className="text-center py-12">
          <Globe className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            {searchTerm ? 'No sites found' : 'No sites yet'}
          </h3>
          <p className="text-gray-600 mb-4">
            {searchTerm 
              ? 'Try adjusting your search or filter criteria'
              : 'Create your first site to get started with AI voice assistants'
            }
          </p>
          {!searchTerm && (
            <Link to="/sites/new" className="btn btn-primary">
              <Plus className="h-4 w-4 mr-2" />
              Create your first site
            </Link>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredSites.map((site) => (
            <div key={site.id} className="card hover:shadow-md transition-shadow duration-200">
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-start space-x-3">
                    <div className={`p-2 rounded-lg ${site.is_active ? 'bg-success-100' : 'bg-gray-100'}`}>
                      <Globe className={`h-5 w-5 ${site.is_active ? 'text-success-600' : 'text-gray-400'}`} />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-lg font-medium text-gray-900 mb-1">
                        {site.name}
                      </h3>
                      <p className="text-sm text-gray-500 mb-2">{site.domain}</p>
                      <div className="flex items-center space-x-4 text-xs text-gray-500">
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          site.is_active 
                            ? 'bg-success-100 text-success-800' 
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {site.is_active ? 'Active' : 'Inactive'}
                        </span>
                        <span>Created {format(new Date(site.created_at), 'MMM d, yyyy')}</span>
                      </div>
                    </div>
                  </div>
                  <div className="relative">
                    <button
                      onClick={() => setShowDropdown(showDropdown === site.id ? null : site.id)}
                      className="p-2 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100"
                    >
                      <MoreVertical className="h-4 w-4" />
                    </button>
                    {showDropdown === site.id && (
                      <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg border border-gray-200 py-1 z-10">
                        <Link
                          to={`/sites/${site.id}`}
                          className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                          onClick={() => setShowDropdown(null)}
                        >
                          <ExternalLink className="h-4 w-4 mr-3" />
                          View Details
                        </Link>
                        <Link
                          to={`/sites/${site.id}/edit`}
                          className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                          onClick={() => setShowDropdown(null)}
                        >
                          <Edit className="h-4 w-4 mr-3" />
                          Edit
                        </Link>
                        <button
                          onClick={() => {
                            handleToggleSite(site.id, site.is_active);
                            setShowDropdown(null);
                          }}
                          className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                        >
                          {site.is_active ? (
                            <>
                              <EyeOff className="h-4 w-4 mr-3" />
                              Disable
                            </>
                          ) : (
                            <>
                              <Eye className="h-4 w-4 mr-3" />
                              Enable
                            </>
                          )}
                        </button>
                        <div className="border-t border-gray-100 my-1" />
                        <button
                          onClick={() => {
                            handleDeleteSite(site.id);
                            setShowDropdown(null);
                          }}
                          className="flex items-center w-full px-4 py-2 text-sm text-error-600 hover:bg-error-50"
                        >
                          <Trash2 className="h-4 w-4 mr-3" />
                          Delete
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                {site.description && (
                  <p className="text-sm text-gray-600 mb-4">{site.description}</p>
                )}

                {/* Stats */}
                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div className="text-center">
                    <div className="text-lg font-semibold text-gray-900">
                      {site.total_interactions || 0}
                    </div>
                    <div className="text-xs text-gray-500 flex items-center justify-center">
                      <MessageCircle className="h-3 w-3 mr-1" />
                      Interactions
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-semibold text-gray-900">
                      {site.total_conversations || 0}
                    </div>
                    <div className="text-xs text-gray-500 flex items-center justify-center">
                      <Users className="h-3 w-3 mr-1" />
                      Conversations
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-semibold text-gray-900">
                      {site.last_interaction ? format(new Date(site.last_interaction), 'MMM d') : 'Never'}
                    </div>
                    <div className="text-xs text-gray-500 flex items-center justify-center">
                      <Activity className="h-3 w-3 mr-1" />
                      Last Activity
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex space-x-2">
                  <Link
                    to={`/sites/${site.id}`}
                    className="btn btn-secondary flex-1 text-sm"
                  >
                    View Details
                  </Link>
                  <Link
                    to={`/analytics?site=${site.id}`}
                    className="btn btn-primary flex-1 text-sm"
                  >
                    Analytics
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SitesPage;