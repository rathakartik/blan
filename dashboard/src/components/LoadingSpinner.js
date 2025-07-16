import React from 'react';
import { clsx } from 'clsx';

const LoadingSpinner = ({ size = 'medium', className = '' }) => {
  const sizeClasses = {
    small: 'h-4 w-4',
    medium: 'h-8 w-8',
    large: 'h-12 w-12',
  };

  return (
    <div className={clsx('flex items-center justify-center', className)}>
      <div
        className={clsx(
          'animate-spin rounded-full border-2 border-primary-200 border-t-primary-600',
          sizeClasses[size]
        )}
      />
    </div>
  );
};

export default LoadingSpinner;