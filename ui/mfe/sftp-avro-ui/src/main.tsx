import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import SftpModule from './SftpModule';
import AvroModule from './AvroModule';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <div className="min-h-screen bg-gray-950 text-white p-6 space-y-8">
      <SftpModule />
      <hr className="border-white/10" />
      <AvroModule />
    </div>
  </React.StrictMode>,
);
