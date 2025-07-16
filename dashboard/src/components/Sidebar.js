import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { clsx } from 'clsx';
import { 
  Home, 
  Globe, 
  BarChart3, 
  Settings, 
  X,
  Plus,
  Mic
} from 'lucide-react';

const Sidebar = ({ open, onClose }) => {
  const location = useLocation();

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: Home },
    { name: 'Sites', href: '/sites', icon: Globe },
    { name: 'Analytics', href: '/analytics', icon: BarChart3 },
    { name: 'Settings', href: '/settings', icon: Settings },
  ];

  const isActive = (href) => {
    return location.pathname === href || location.pathname.startsWith(href + '/');
  };

  return (
    <>
      {/* Mobile backdrop */}
      {open && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-75 z-40 lg:hidden" onClick={onClose} />
      )}

      {/* Sidebar */}
      <div className={clsx(
        'fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-xl border-r border-gray-200 transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0',
        open ? 'translate-x-0' : '-translate-x-full'
      )}>
        <div className="flex items-center justify-between h-16 px-6 border-b border-gray-200">
          <div className="flex items-center space-x-2">
            <div className="h-8 w-8 bg-primary-600 rounded-lg flex items-center justify-center">
              <Mic className="h-5 w-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-gray-900">AI Voice</h1>
              <p className="text-xs text-gray-500">Assistant</p>
            </div>
          </div>
          
          <button
            onClick={onClose}
            className="lg:hidden p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="mt-8 px-6">
          <div className="space-y-1">
            {navigation.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.name}
                  to={item.href}
                  onClick={onClose}
                  className={clsx(
                    'group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors duration-200',
                    isActive(item.href)
                      ? 'bg-primary-50 text-primary-700 border-r-2 border-primary-600'
                      : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                  )}
                >
                  <Icon className={clsx(
                    'mr-3 h-5 w-5',
                    isActive(item.href)
                      ? 'text-primary-600'
                      : 'text-gray-400 group-hover:text-gray-500'
                  )} />
                  {item.name}
                </NavLink>
              );
            })}
          </div>

          <div className="mt-8 pt-8 border-t border-gray-200">
            <NavLink
              to="/sites/new"
              onClick={onClose}
              className="group flex items-center px-3 py-2 text-sm font-medium rounded-md text-primary-600 hover:bg-primary-50 transition-colors duration-200"
            >
              <Plus className="mr-3 h-5 w-5" />
              Add New Site
            </NavLink>
          </div>
        </nav>

        {/* Bottom section */}
        <div className="absolute bottom-0 left-0 right-0 p-6 border-t border-gray-200 bg-gray-50">
          <div className="text-xs text-gray-500 text-center">
            <p>AI Voice Assistant Dashboard</p>
            <p className="mt-1">Version 1.0.0</p>
          </div>
        </div>
      </div>
    </>
  );
};

export default Sidebar;