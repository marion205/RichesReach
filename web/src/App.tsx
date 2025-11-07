/**
 * RichesReach Web App
 * Main application component
 */

import React, { useState, useEffect } from 'react';
import OrbRenderer from './components/OrbRenderer';
import './App.css';

const API_BASE = process.env.API_BASE_URL || 'http://localhost:8000';

interface MoneySnapshot {
  netWorth: number;
  portfolioValue: number;
  bankBalance: number;
}

function App() {
  const [snapshot, setSnapshot] = useState<MoneySnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSnapshot();
  }, []);

  const loadSnapshot = async () => {
    try {
      // Get auth token from localStorage (if available)
      const token = localStorage.getItem('token') || localStorage.getItem('authToken');
      
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${API_BASE}/api/money/snapshot`, {
        method: 'GET',
        headers,
      });

      if (!response.ok) {
        // Use mock data if API fails
        setSnapshot({
          netWorth: 100000,
          portfolioValue: 90000,
          bankBalance: 10000,
        });
        return;
      }

      const data = await response.json();
      setSnapshot({
        netWorth: data.netWorth || 100000,
        portfolioValue: data.breakdown?.portfolioValue || 90000,
        bankBalance: data.breakdown?.bankBalance || 10000,
      });
    } catch (err) {
      console.warn('Failed to load snapshot, using mock data:', err);
      // Fallback to mock data
      setSnapshot({
        netWorth: 100000,
        portfolioValue: 90000,
        bankBalance: 10000,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleGesture = (gesture: string) => {
    console.log('Gesture detected:', gesture);
    // Handle gestures (open modals, navigate, etc.)
    // For now, just log
  };

  if (loading) {
    return (
      <div className="app-loading">
        <div className="spinner"></div>
        <p>Loading Constellation Orb...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="app-error">
        <h1>Error</h1>
        <p>{error}</p>
        <button onClick={loadSnapshot}>Retry</button>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>RichesReach</h1>
        <p className="app-subtitle">Constellation Orb</p>
      </header>
      
      <main className="app-main">
        <div className="orb-container">
          {snapshot && (
            <OrbRenderer
              netWorth={snapshot.netWorth}
              portfolioValue={snapshot.portfolioValue}
              bankBalance={snapshot.bankBalance}
              onGesture={handleGesture}
              width={Math.min(window.innerWidth - 40, 600)}
              height={Math.min(window.innerHeight - 200, 600)}
            />
          )}
        </div>
        
        <div className="app-info">
          <div className="info-card">
            <h3>Net Worth</h3>
            <p className="info-value">
              ${snapshot?.netWorth.toLocaleString() || '0'}
            </p>
          </div>
          <div className="info-card">
            <h3>Portfolio</h3>
            <p className="info-value">
              ${snapshot?.portfolioValue.toLocaleString() || '0'}
            </p>
          </div>
          <div className="info-card">
            <h3>Cash</h3>
            <p className="info-value">
              ${snapshot?.bankBalance.toLocaleString() || '0'}
            </p>
          </div>
        </div>
      </main>
      
      <footer className="app-footer">
        <p>Install this app for offline access</p>
        <button 
          className="install-button"
          onClick={() => {
            // PWA install prompt
            if ('serviceWorker' in navigator) {
              // Show install prompt
            }
          }}
        >
          Install App
        </button>
      </footer>
    </div>
  );
}

export default App;

