/**
 * DemoContext — controls demo mode across the entire app.
 *
 * Enable by setting EXPO_PUBLIC_DEMO_MODE=true in your .env file.
 * When active:
 *   - Auth is bypassed (demo user is injected)
 *   - All GraphQL queries resolve from the pre-seeded mock Apollo cache
 *   - All REST calls are intercepted and return static JSON
 *   - WebSocket services skip their connections
 *   - A "DEMO" banner is shown at the top of the screen
 */

import React, { createContext, useContext, ReactNode } from 'react';

const IS_DEMO = process.env.EXPO_PUBLIC_DEMO_MODE === 'true';

export const DEMO_USER = {
  id: 'demo-user-1',
  email: 'demo@richesreach.com',
  username: 'demo',
  name: 'Alex Demo',
  profilePic: null as string | null,
  hasPremiumAccess: true,
  subscriptionTier: 'premium',
};

interface DemoContextType {
  isDemoMode: boolean;
  demoUser: typeof DEMO_USER;
}

const DemoContext = createContext<DemoContextType>({
  isDemoMode: IS_DEMO,
  demoUser: DEMO_USER,
});

export const DemoProvider: React.FC<{ children: ReactNode }> = ({ children }) => (
  <DemoContext.Provider value={{ isDemoMode: IS_DEMO, demoUser: DEMO_USER }}>
    {children}
  </DemoContext.Provider>
);

export const useDemo = () => useContext(DemoContext);
