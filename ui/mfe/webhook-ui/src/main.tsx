import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import WebhookModule from './WebhookModule';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <div className="min-h-screen bg-gray-950 text-white p-6">
      <WebhookModule />
    </div>
  </React.StrictMode>,
);
