import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import PmDashboardModule from './PmDashboardModule';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <div className="min-h-screen bg-gray-950 text-white p-6">
      <PmDashboardModule />
    </div>
  </React.StrictMode>,
);
