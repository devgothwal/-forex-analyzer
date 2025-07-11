// Application entry point

import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';

// Import global styles
import './index.css';

// Performance monitoring
import { reportWebVitals } from './utils/reportWebVitals';

// Get root element
const container = document.getElementById('root');
if (!container) {
  throw new Error('Root element not found');
}

// Create root and render app
const root = createRoot(container);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// Performance monitoring in development
if (process.env.NODE_ENV === 'development') {
  reportWebVitals(console.log);
}