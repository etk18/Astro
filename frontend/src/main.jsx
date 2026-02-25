import React from 'react';
import ReactDOM from 'react-dom/client';
import axios from 'axios';
import App from './App';
import './index.css';

// Utilize VITE_BACKEND_URL if set (e.g. for Render/Vercel production deployments)
axios.defaults.baseURL = import.meta.env.VITE_BACKEND_URL || '';

ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
        <App />
    </React.StrictMode>
);
