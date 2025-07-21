import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import {
  DocumentDuplicateIcon,
  CheckIcon,
  CodeBracketIcon,
  GlobeAltIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';

const EmbedCode = () => {
  const { id } = useParams();
  const [site, setSite] = useState(null);
  const [embedScript, setEmbedScript] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);
  const [selectedTheme, setSelectedTheme] = useState('blue');
  const [selectedPosition, setSelectedPosition] = useState('bottom-right');

  useEffect(() => {
    fetchSiteAndEmbed();
  }, [id]);

  const fetchSiteAndEmbed = async () => {
    try {
      const [siteResponse, embedResponse] = await Promise.all([
        axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/sites/${id}`),
        axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/sites/${id}/embed`)
      ]);
      
      setSite(siteResponse.data);
      setEmbedScript(embedResponse.data.script_content);
    } catch (error) {
      console.error('Error fetching data:', error);
      setError('Failed to load embed code');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = async () => {
    try {
      const customizedScript = generateCustomizedScript();
      await navigator.clipboard.writeText(customizedScript);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
    }
  };

  const generateCustomizedScript = () => {
    return embedScript
      .replace(/data-theme="[^"]*"/g, `data-theme="${selectedTheme}"`)
      .replace(/data-position="[^"]*"/g, `data-position="${selectedPosition}"`);
  };

  const themes = [
    { value: 'blue', name: 'Blue', color: '#3B82F6' },
    { value: 'green', name: 'Green', color: '#10B981' },
    { value: 'purple', name: 'Purple', color: '#8B5CF6' },
    { value: 'red', name: 'Red', color: '#EF4444' },
    { value: 'orange', name: 'Orange', color: '#F59E0B' }
  ];

  const positions = [
    { value: 'bottom-right', name: 'Bottom Right', description: 'Default position' },
    { value: 'bottom-left', name: 'Bottom Left', description: 'Left corner' },
    { value: 'top-right', name: 'Top Right', description: 'Upper corner' },
    { value: 'top-left', name: 'Top Left', description: 'Upper left corner' }
  ];

  if (loading) {
    return (
      <div className="p-4 sm:p-6 lg:p-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-300 rounded w-1/4 mb-6"></div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="h-4 bg-gray-300 rounded w-3/4 mb-4"></div>
            <div className="h-32 bg-gray-300 rounded mb-4"></div>
            <div className="h-10 bg-gray-300 rounded w-1/2"></div>
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
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 bg-purple-100 rounded-lg flex items-center justify-center">
            <CodeBracketIcon className="h-6 w-6 text-purple-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Embed Code</h1>
            <p className="text-gray-600">{site?.name} - {site?.domain}</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        {/* Main Content */}
        <div className="xl:col-span-2 space-y-6">
          {/* Customization Options */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Customization</h2>
            
            {/* Theme Selection */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Color Theme
              </label>
              <div className="grid grid-cols-5 gap-3">
                {themes.map((theme) => (
                  <button
                    key={theme.value}
                    onClick={() => setSelectedTheme(theme.value)}
                    className={`relative p-3 rounded-lg border-2 transition-all ${
                      selectedTheme === theme.value
                        ? 'border-gray-900 ring-2 ring-gray-900'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div
                      className="w-8 h-8 rounded-full mx-auto mb-2"
                      style={{ backgroundColor: theme.color }}
                    />
                    <div className="text-xs font-medium text-center">{theme.name}</div>
                    {selectedTheme === theme.value && (
                      <div className="absolute -top-1 -right-1">
                        <CheckIcon className="h-5 w-5 text-gray-900 bg-white rounded-full" />
                      </div>
                    )}
                  </button>
                ))}
              </div>
            </div>

            {/* Position Selection */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Widget Position
              </label>
              <div className="grid grid-cols-2 gap-3">
                {positions.map((position) => (
                  <button
                    key={position.value}
                    onClick={() => setSelectedPosition(position.value)}
                    className={`p-4 text-left rounded-lg border-2 transition-all ${
                      selectedPosition === position.value
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="font-medium text-gray-900">{position.name}</div>
                    <div className="text-sm text-gray-500 mt-1">{position.description}</div>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Embed Code */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Embed Code</h2>
              <button
                onClick={copyToClipboard}
                className={`inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md transition-colors ${
                  copied
                    ? 'text-green-700 bg-green-100 hover:bg-green-200'
                    : 'text-gray-700 bg-gray-100 hover:bg-gray-200'
                }`}
              >
                {copied ? (
                  <>
                    <CheckIcon className="h-4 w-4 mr-2" />
                    Copied!
                  </>
                ) : (
                  <>
                    <DocumentDuplicateIcon className="h-4 w-4 mr-2" />
                    Copy Code
                  </>
                )}
              </button>
            </div>

            <div className="relative">
              <pre className="bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto text-sm font-mono">
                <code>{generateCustomizedScript()}</code>
              </pre>
            </div>
          </div>

          {/* Installation Instructions */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Installation Instructions</h2>
            
            <div className="space-y-4">
              <div className="flex items-start">
                <div className="flex-shrink-0 w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-semibold">
                  1
                </div>
                <div className="ml-4">
                  <h3 className="text-sm font-semibold text-gray-900">Copy the embed code</h3>
                  <p className="text-sm text-gray-600 mt-1">
                    Click the "Copy Code" button above to copy the embed script to your clipboard.
                  </p>
                </div>
              </div>

              <div className="flex items-start">
                <div className="flex-shrink-0 w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-semibold">
                  2
                </div>
                <div className="ml-4">
                  <h3 className="text-sm font-semibold text-gray-900">Add to your website</h3>
                  <p className="text-sm text-gray-600 mt-1">
                    Paste the script before the closing <code className="bg-gray-100 px-1 rounded">&lt;/body&gt;</code> tag in your website's HTML.
                  </p>
                </div>
              </div>

              <div className="flex items-start">
                <div className="flex-shrink-0 w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-semibold">
                  3
                </div>
                <div className="ml-4">
                  <h3 className="text-sm font-semibold text-gray-900">Test the widget</h3>
                  <p className="text-sm text-gray-600 mt-1">
                    Refresh your website and look for the AI assistant button in the selected position.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Site Info */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center gap-3 mb-4">
              <GlobeAltIcon className="h-5 w-5 text-gray-400" />
              <h3 className="text-lg font-semibold text-gray-900">Site Details</h3>
            </div>
            
            <div className="space-y-3">
              <div>
                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Site Name
                </label>
                <div className="text-sm text-gray-900 mt-1">{site?.name}</div>
              </div>
              
              <div>
                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Domain
                </label>
                <div className="text-sm text-gray-900 mt-1">{site?.domain}</div>
              </div>
              
              <div>
                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Bot Name
                </label>
                <div className="text-sm text-gray-900 mt-1">{site?.bot_name}</div>
              </div>
              
              <div>
                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </label>
                <div className="flex items-center gap-2 mt-1">
                  <div className={`h-2 w-2 rounded-full ${site?.is_active ? 'bg-green-400' : 'bg-red-400'}`} />
                  <span className={`text-sm ${site?.is_active ? 'text-green-600' : 'text-red-600'}`}>
                    {site?.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Requirements */}
          <div className="bg-blue-50 rounded-lg p-6">
            <div className="flex items-center gap-3 mb-4">
              <InformationCircleIcon className="h-5 w-5 text-blue-500" />
              <h3 className="text-lg font-semibold text-blue-900">Requirements</h3>
            </div>
            
            <div className="space-y-3 text-sm text-blue-800">
              <div className="flex items-center gap-2">
                <CheckIcon className="h-4 w-4 text-green-500 flex-shrink-0" />
                <span>Modern browser (Chrome, Firefox, Safari, Edge)</span>
              </div>
              
              <div className="flex items-center gap-2">
                <CheckIcon className="h-4 w-4 text-green-500 flex-shrink-0" />
                <span>HTTPS required for voice features</span>
              </div>
              
              <div className="flex items-center gap-2">
                <CheckIcon className="h-4 w-4 text-green-500 flex-shrink-0" />
                <span>No additional dependencies</span>
              </div>
            </div>
          </div>

          {/* Performance Tips */}
          <div className="bg-yellow-50 rounded-lg p-6">
            <div className="flex items-center gap-3 mb-4">
              <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />
              <h3 className="text-lg font-semibold text-yellow-900">Performance Tips</h3>
            </div>
            
            <div className="space-y-2 text-sm text-yellow-800">
              <p>• Widget loads asynchronously without blocking your page</p>
              <p>• Minimal impact on page load speed</p>
              <p>• Optimized for mobile devices</p>
              <p>• Uses efficient event listeners</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmbedCode;