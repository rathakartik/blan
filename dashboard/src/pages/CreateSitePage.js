import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { api } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import { ArrowLeft, Globe, Palette, Settings, Mic, Eye } from 'lucide-react';
import toast from 'react-hot-toast';

const CreateSitePage = () => {
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('basic');
  const [previewTheme, setPreviewTheme] = useState({
    primary_color: '#3B82F6',
    secondary_color: '#1E40AF',
    text_color: '#1F2937',
    background_color: '#FFFFFF',
    danger_color: '#EF4444'
  });

  const navigate = useNavigate();
  
  const { register, handleSubmit, formState: { errors }, watch, setValue } = useForm({
    defaultValues: {
      name: '',
      domain: '',
      description: '',
      greeting_message: "Hi there! I'm your virtual assistant. How can I help you today?",
      bot_name: 'AI Assistant',
      position: 'bottom-right',
      auto_greet: true,
      voice_enabled: true,
      language: 'en-US',
      theme: previewTheme,
      groq_api_key: '',
    }
  });

  const tabs = [
    { id: 'basic', name: 'Basic Info', icon: Globe },
    { id: 'appearance', name: 'Appearance', icon: Palette },
    { id: 'behavior', name: 'Behavior', icon: Settings },
    { id: 'voice', name: 'Voice', icon: Mic },
  ];

  const onSubmit = async (data) => {
    setLoading(true);
    try {
      const siteData = {
        ...data,
        theme: previewTheme
      };
      
      const response = await api.createSite(siteData);
      toast.success('Site created successfully!');
      navigate(`/sites/${response.id}`);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create site');
    } finally {
      setLoading(false);
    }
  };

  const handleThemeChange = (field, value) => {
    const newTheme = { ...previewTheme, [field]: value };
    setPreviewTheme(newTheme);
    setValue('theme', newTheme);
  };

  const languages = [
    { code: 'en-US', name: 'English (US)' },
    { code: 'en-GB', name: 'English (UK)' },
    { code: 'es-ES', name: 'Spanish' },
    { code: 'fr-FR', name: 'French' },
    { code: 'de-DE', name: 'German' },
    { code: 'it-IT', name: 'Italian' },
    { code: 'pt-PT', name: 'Portuguese' },
    { code: 'ru-RU', name: 'Russian' },
    { code: 'ja-JP', name: 'Japanese' },
    { code: 'ko-KR', name: 'Korean' },
    { code: 'zh-CN', name: 'Chinese (Simplified)' },
    { code: 'ar-SA', name: 'Arabic' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-4">
        <Link
          to="/sites"
          className="p-2 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100"
        >
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Create New Site</h1>
          <p className="text-gray-600 mt-1">
            Set up your AI voice assistant for a new website
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Form */}
          <div className="lg:col-span-2">
            <div className="card">
              {/* Tabs */}
              <div className="border-b border-gray-200">
                <nav className="flex space-x-8 px-6">
                  {tabs.map((tab) => {
                    const Icon = tab.icon;
                    return (
                      <button
                        key={tab.id}
                        type="button"
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
                {activeTab === 'basic' && (
                  <div className="space-y-4">
                    <div>
                      <label className="label">Site Name *</label>
                      <input
                        {...register('name', { required: 'Site name is required' })}
                        className={`input mt-1 ${errors.name ? 'border-error-500' : ''}`}
                        placeholder="My Awesome Website"
                      />
                      {errors.name && (
                        <p className="mt-1 text-sm text-error-600">{errors.name.message}</p>
                      )}
                    </div>

                    <div>
                      <label className="label">Domain *</label>
                      <input
                        {...register('domain', { 
                          required: 'Domain is required',
                          pattern: {
                            value: /^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/,
                            message: 'Please enter a valid domain'
                          }
                        })}
                        className={`input mt-1 ${errors.domain ? 'border-error-500' : ''}`}
                        placeholder="example.com"
                      />
                      {errors.domain && (
                        <p className="mt-1 text-sm text-error-600">{errors.domain.message}</p>
                      )}
                      <p className="mt-1 text-sm text-gray-500">
                        Enter your website's domain without http:// or https://
                      </p>
                    </div>

                    <div>
                      <label className="label">Description</label>
                      <textarea
                        {...register('description')}
                        rows={3}
                        className="input mt-1"
                        placeholder="Brief description of your website (optional)"
                      />
                    </div>

                    <div>
                      <label className="label">GROQ API Key</label>
                      <input
                        {...register('groq_api_key')}
                        type="password"
                        className="input mt-1"
                        placeholder="Enter your GROQ API key for AI responses"
                      />
                      <p className="mt-1 text-sm text-gray-500">
                        Optional. If not provided, demo responses will be used.
                      </p>
                    </div>
                  </div>
                )}

                {activeTab === 'appearance' && (
                  <div className="space-y-4">
                    <div>
                      <label className="label">Bot Name</label>
                      <input
                        {...register('bot_name')}
                        className="input mt-1"
                        placeholder="AI Assistant"
                      />
                    </div>

                    <div>
                      <label className="label">Widget Position</label>
                      <select {...register('position')} className="input mt-1">
                        <option value="bottom-right">Bottom Right</option>
                        <option value="bottom-left">Bottom Left</option>
                      </select>
                    </div>

                    <div>
                      <label className="label">Theme Colors</label>
                      <div className="grid grid-cols-2 gap-4 mt-2">
                        <div>
                          <label className="block text-sm text-gray-600 mb-1">Primary Color</label>
                          <input
                            type="color"
                            value={previewTheme.primary_color}
                            onChange={(e) => handleThemeChange('primary_color', e.target.value)}
                            className="h-10 w-full rounded border border-gray-300"
                          />
                        </div>
                        <div>
                          <label className="block text-sm text-gray-600 mb-1">Secondary Color</label>
                          <input
                            type="color"
                            value={previewTheme.secondary_color}
                            onChange={(e) => handleThemeChange('secondary_color', e.target.value)}
                            className="h-10 w-full rounded border border-gray-300"
                          />
                        </div>
                        <div>
                          <label className="block text-sm text-gray-600 mb-1">Text Color</label>
                          <input
                            type="color"
                            value={previewTheme.text_color}
                            onChange={(e) => handleThemeChange('text_color', e.target.value)}
                            className="h-10 w-full rounded border border-gray-300"
                          />
                        </div>
                        <div>
                          <label className="block text-sm text-gray-600 mb-1">Background Color</label>
                          <input
                            type="color"
                            value={previewTheme.background_color}
                            onChange={(e) => handleThemeChange('background_color', e.target.value)}
                            className="h-10 w-full rounded border border-gray-300"
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {activeTab === 'behavior' && (
                  <div className="space-y-4">
                    <div>
                      <label className="label">Greeting Message</label>
                      <textarea
                        {...register('greeting_message')}
                        rows={3}
                        className="input mt-1"
                        placeholder="Hi there! I'm your virtual assistant. How can I help you today?"
                      />
                    </div>

                    <div className="space-y-3">
                      <div className="flex items-center">
                        <input
                          {...register('auto_greet')}
                          type="checkbox"
                          className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                        />
                        <label className="ml-2 block text-sm text-gray-900">
                          Auto-greet users when widget opens
                        </label>
                      </div>
                      
                      <div className="flex items-center">
                        <input
                          {...register('voice_enabled')}
                          type="checkbox"
                          className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                        />
                        <label className="ml-2 block text-sm text-gray-900">
                          Enable voice features
                        </label>
                      </div>
                    </div>
                  </div>
                )}

                {activeTab === 'voice' && (
                  <div className="space-y-4">
                    <div>
                      <label className="label">Language</label>
                      <select {...register('language')} className="input mt-1">
                        {languages.map((lang) => (
                          <option key={lang.code} value={lang.code}>
                            {lang.name}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                      <h4 className="text-sm font-medium text-blue-900 mb-2">Voice Features</h4>
                      <ul className="text-sm text-blue-800 space-y-1">
                        <li>• Speech-to-text for user input</li>
                        <li>• Text-to-speech for AI responses</li>
                        <li>• Browser-based voice recognition</li>
                        <li>• Requires HTTPS in production</li>
                        <li>• Microphone permission required</li>
                      </ul>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Preview */}
          <div className="lg:col-span-1">
            <div className="card sticky top-6">
              <div className="p-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900 flex items-center">
                  <Eye className="h-5 w-5 mr-2" />
                  Preview
                </h3>
              </div>
              <div className="p-4">
                <div className="relative bg-gray-100 rounded-lg p-4 h-64">
                  <div className="absolute bottom-4 right-4">
                    <div 
                      className="w-12 h-12 rounded-full shadow-lg flex items-center justify-center cursor-pointer"
                      style={{ backgroundColor: previewTheme.primary_color }}
                    >
                      <Mic className="h-6 w-6 text-white" />
                    </div>
                  </div>
                  
                  <div className="absolute bottom-20 right-4 w-64 h-48 bg-white rounded-lg shadow-xl border">
                    <div 
                      className="px-4 py-3 border-b"
                      style={{ 
                        backgroundColor: previewTheme.primary_color,
                        color: previewTheme.background_color 
                      }}
                    >
                      <h4 className="font-medium">{watch('bot_name') || 'AI Assistant'}</h4>
                    </div>
                    <div className="p-4 space-y-2">
                      <div className="bg-gray-100 rounded-lg p-2 text-sm">
                        {watch('greeting_message') || "Hi there! I'm your virtual assistant. How can I help you today?"}
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="mt-4 space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Position:</span>
                    <span className="font-medium">{watch('position') === 'bottom-right' ? 'Bottom Right' : 'Bottom Left'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Voice:</span>
                    <span className="font-medium">{watch('voice_enabled') ? 'Enabled' : 'Disabled'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Auto-greet:</span>
                    <span className="font-medium">{watch('auto_greet') ? 'Yes' : 'No'}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-end space-x-3">
          <Link to="/sites" className="btn btn-secondary">
            Cancel
          </Link>
          <button
            type="submit"
            disabled={loading}
            className="btn btn-primary"
          >
            {loading ? (
              <>
                <LoadingSpinner size="small" />
                <span className="ml-2">Creating Site...</span>
              </>
            ) : (
              'Create Site'
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default CreateSitePage;