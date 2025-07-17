import React, { useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { api } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import { 
  ArrowLeft, 
  Edit, 
  Trash2, 
  Copy, 
  ExternalLink,
  Eye,
  EyeOff,
  Code,
  BarChart3,
  Globe,
  Mic,
  MessageCircle,
  Users,
  Activity,
  Settings,
  Palette,
  Download
} from 'lucide-react';
import { format } from 'date-fns';
import toast from 'react-hot-toast';

const SiteDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('overview');
  const [showEmbedCode, setShowEmbedCode] = useState(false);

  const { data: site, isLoading, error } = useQuery(
    ['site', id],
    () => api.getSite(id),
    {
      onError: (error) => {
        if (error.response?.status === 404) {
          toast.error('Site not found');
          navigate('/sites');
        }
      }
    }
  );

  const { data: analytics, isLoading: analyticsLoading } = useQuery(
    ['siteAnalytics', id],
    () => api.getSiteAnalytics(id),
    {
      enabled: !!site,
      refetchInterval: 30000,
    }
  );

  const { data: embedScript, isLoading: embedLoading } = useQuery(
    ['embedScript', id],
    () => api.getEmbedScript(id),
    {
      enabled: !!site && showEmbedCode,
    }
  );

  const toggleSiteMutation = useMutation(
    (isActive) => api.updateSite(id, { is_active: !isActive }),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['site', id]);
        toast.success(site?.is_active ? 'Site disabled' : 'Site enabled');
      },
      onError: () => {
        toast.error('Failed to update site');
      }
    }
  );

  const deleteSiteMutation = useMutation(
    () => api.deleteSite(id),
    {
      onSuccess: () => {
        toast.success('Site deleted successfully');
        navigate('/sites');
      },
      onError: () => {
        toast.error('Failed to delete site');
      }
    }
  );

  const handleCopyEmbedCode = () => {
    if (embedScript?.script_content) {
      navigator.clipboard.writeText(embedScript.script_content);
      toast.success('Embed code copied to clipboard');
    }
  };

  const handleDeleteSite = () => {
    if (window.confirm('Are you sure you want to delete this site? This action cannot be undone.')) {
      deleteSiteMutation.mutate();
    }
  };

  const tabs = [
    { id: 'overview', name: 'Overview', icon: Globe },
    { id: 'analytics', name: 'Analytics', icon: BarChart3 },
    { id: 'settings', name: 'Settings', icon: Settings },
    { id: 'embed', name: 'Embed', icon: Code },
  ];

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
        <h3 className="text-lg font-medium text-gray-900 mb-2">Site not found</h3>
        <p className="text-gray-600 mb-4">The site you're looking for doesn't exist or has been deleted.</p>
        <Link to="/sites" className="btn btn-primary">
          Back to Sites
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link
            to="/sites"
            className="p-2 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center">
              {site.name}
              <span className={`ml-3 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                site.is_active 
                  ? 'bg-success-100 text-success-800' 
                  : 'bg-gray-100 text-gray-800'
              }`}>
                {site.is_active ? 'Active' : 'Inactive'}
              </span>
            </h1>
            <p className="text-gray-600 mt-1">{site.domain}</p>
          </div>
        </div>
        
        <div className="flex items-center space-x-3">
          <button
            onClick={() => toggleSiteMutation.mutate(site.is_active)}
            className={`btn ${site.is_active ? 'btn-secondary' : 'btn-success'}`}
            disabled={toggleSiteMutation.isLoading}
          >
            {toggleSiteMutation.isLoading ? (
              <LoadingSpinner size="small" />
            ) : (
              <>
                {site.is_active ? <EyeOff className="h-4 w-4 mr-2" /> : <Eye className="h-4 w-4 mr-2" />}
                {site.is_active ? 'Disable' : 'Enable'}
              </>
            )}
          </button>
          <Link to={`/sites/${id}/edit`} className="btn btn-secondary">
            <Edit className="h-4 w-4 mr-2" />
            Edit
          </Link>
          <button
            onClick={handleDeleteSite}
            className="btn btn-danger"
            disabled={deleteSiteMutation.isLoading}
          >
            {deleteSiteMutation.isLoading ? (
              <LoadingSpinner size="small" />
            ) : (
              <Trash2 className="h-4 w-4" />
            )}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="card">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors duration-200 ${
                    activeTab === tab.id
                      ? 'border-primary-500 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="h-4 w-4 mr-2 inline" />
                  {tab.name}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Stats */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="bg-primary-50 rounded-lg p-4">
                  <div className="flex items-center">
                    <MessageCircle className="h-8 w-8 text-primary-600" />
                    <div className="ml-3">
                      <p className="text-sm font-medium text-primary-600">Total Interactions</p>
                      <p className="text-2xl font-bold text-primary-900">
                        {analytics?.total_interactions || 0}
                      </p>
                    </div>
                  </div>
                </div>
                
                <div className="bg-success-50 rounded-lg p-4">
                  <div className="flex items-center">
                    <Users className="h-8 w-8 text-success-600" />
                    <div className="ml-3">
                      <p className="text-sm font-medium text-success-600">Sessions</p>
                      <p className="text-2xl font-bold text-success-900">
                        {analytics?.total_sessions || 0}
                      </p>
                    </div>
                  </div>
                </div>
                
                <div className="bg-warning-50 rounded-lg p-4">
                  <div className="flex items-center">
                    <Activity className="h-8 w-8 text-warning-600" />
                    <div className="ml-3">
                      <p className="text-sm font-medium text-warning-600">Conversations</p>
                      <p className="text-2xl font-bold text-warning-900">
                        {analytics?.total_conversations || 0}
                      </p>
                    </div>
                  </div>
                </div>
                
                <div className="bg-secondary-50 rounded-lg p-4">
                  <div className="flex items-center">
                    <Mic className="h-8 w-8 text-secondary-600" />
                    <div className="ml-3">
                      <p className="text-sm font-medium text-secondary-600">Voice Usage</p>
                      <p className="text-2xl font-bold text-secondary-900">
                        {analytics?.top_interaction_types?.find(t => t.type === 'voice_input')?.count || 0}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Site Info */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Site Information</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Domain:</span>
                      <span className="font-medium">{site.domain}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Bot Name:</span>
                      <span className="font-medium">{site.bot_name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Language:</span>
                      <span className="font-medium">{site.language}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Position:</span>
                      <span className="font-medium">{site.position}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Created:</span>
                      <span className="font-medium">{format(new Date(site.created_at), 'MMM d, yyyy')}</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Configuration</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Auto-greet:</span>
                      <span className={`font-medium ${site.auto_greet ? 'text-success-600' : 'text-gray-600'}`}>
                        {site.auto_greet ? 'Enabled' : 'Disabled'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Voice enabled:</span>
                      <span className={`font-medium ${site.voice_enabled ? 'text-success-600' : 'text-gray-600'}`}>
                        {site.voice_enabled ? 'Enabled' : 'Disabled'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">API Key:</span>
                      <span className="font-medium">
                        {site.groq_api_key ? '••••••••••••' : 'Demo mode'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Greeting Message */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Greeting Message</h3>
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-gray-700">{site.greeting_message}</p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'analytics' && (
            <div className="space-y-6">
              {analyticsLoading ? (
                <div className="flex items-center justify-center py-12">
                  <LoadingSpinner size="large" />
                </div>
              ) : (
                <>
                  {/* Top Interactions */}
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 mb-4">Top Interaction Types</h3>
                    <div className="space-y-3">
                      {analytics?.top_interaction_types?.map((type, index) => (
                        <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                          <span className="font-medium">{type.type.replace('_', ' ').toUpperCase()}</span>
                          <span className="text-gray-600">{type.count} interactions</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Popular Questions */}
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 mb-4">Popular Questions</h3>
                    <div className="space-y-3">
                      {analytics?.popular_questions?.length > 0 ? (
                        analytics.popular_questions.slice(0, 10).map((question, index) => (
                          <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                            <span className="font-medium">{question.question}</span>
                            <span className="text-gray-600">{question.count} times</span>
                          </div>
                        ))
                      ) : (
                        <p className="text-gray-500 text-center py-8">No questions asked yet</p>
                      )}
                    </div>
                  </div>
                </>
              )}
            </div>
          )}

          {activeTab === 'settings' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Theme Preview</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <div 
                      className="w-12 h-12 rounded-full mx-auto mb-2"
                      style={{ backgroundColor: site.theme.primary_color }}
                    ></div>
                    <p className="text-sm text-gray-600">Primary</p>
                  </div>
                  <div className="text-center">
                    <div 
                      className="w-12 h-12 rounded-full mx-auto mb-2"
                      style={{ backgroundColor: site.theme.secondary_color }}
                    ></div>
                    <p className="text-sm text-gray-600">Secondary</p>
                  </div>
                  <div className="text-center">
                    <div 
                      className="w-12 h-12 rounded-full mx-auto mb-2 border"
                      style={{ backgroundColor: site.theme.text_color }}
                    ></div>
                    <p className="text-sm text-gray-600">Text</p>
                  </div>
                  <div className="text-center">
                    <div 
                      className="w-12 h-12 rounded-full mx-auto mb-2 border"
                      style={{ backgroundColor: site.theme.background_color }}
                    ></div>
                    <p className="text-sm text-gray-600">Background</p>
                  </div>
                </div>
              </div>

              <div className="flex justify-end">
                <Link to={`/sites/${id}/edit`} className="btn btn-primary">
                  <Edit className="h-4 w-4 mr-2" />
                  Edit Settings
                </Link>
              </div>
            </div>
          )}

          {activeTab === 'embed' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Embed Code</h3>
                <p className="text-gray-600 mb-4">
                  Copy and paste this code into your website to add the AI voice assistant widget.
                </p>
                
                <div className="bg-gray-900 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-gray-300 text-sm">HTML</span>
                    <button
                      onClick={() => {
                        setShowEmbedCode(true);
                        setTimeout(handleCopyEmbedCode, 100);
                      }}
                      className="text-gray-300 hover:text-white"
                    >
                      <Copy className="h-4 w-4" />
                    </button>
                  </div>
                  {embedLoading ? (
                    <div className="flex items-center justify-center py-8">
                      <LoadingSpinner size="small" />
                    </div>
                  ) : (
                    <pre className="text-gray-100 text-sm overflow-x-auto">
                      <code>{embedScript?.script_content || 'Loading...'}</code>
                    </pre>
                  )}
                </div>
              </div>

              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Installation Instructions</h3>
                <div className="bg-gray-50 rounded-lg p-4">
                  <pre className="text-gray-700 text-sm whitespace-pre-wrap">
                    {embedScript?.installation_instructions || 'Loading...'}
                  </pre>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SiteDetailPage;