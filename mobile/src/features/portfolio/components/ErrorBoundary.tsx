/**
 * Error Boundary for Constellation Orb components
 * Re-exports unified ErrorBoundary with portfolio context
 */

import React from 'react';
import ErrorBoundary, { ErrorBoundaryProps } from '../../../components/ErrorBoundary';

/**
 * Constellation-specific error boundary with context
 */
export const ConstellationErrorBoundary: React.FC<ErrorBoundaryProps> = (props) => {
  return (
    <ErrorBoundary
      {...props}
      context="Constellation Portfolio"
    />
  );
};

export default ConstellationErrorBoundary;

