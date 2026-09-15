import React, { useEffect, useState } from 'react';
import { Header } from '@/components/layout/Header';
import { Footer } from '@/components/layout/Footer';
import { LandingPage } from '@/pages/LandingPage';
import { StudioPage } from '@/pages/StudioPage';
import { api } from '@/lib/api';
import { ActiveTab, CreationMode, HealthResponse, Theme } from '@/types';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('landing');
  const [studioMode, setStudioMode] = useState<CreationMode>('topic');
  const [theme, setTheme] = useState<Theme>('dark');
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loadingHealth, setLoadingHealth] = useState<boolean>(true);

  const fetchHealth = async () => {
    setLoadingHealth(true);
    try {
      const data = await api.getHealth();
      setHealth(data);
    } catch {
      setHealth(null);
    } finally {
      setLoadingHealth(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'light') {
      root.classList.add('light');
      root.classList.remove('dark');
    } else {
      root.classList.add('dark');
      root.classList.remove('light');
    }
  }, [theme]);

  const handleToggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  const handleStartCreation = (mode: CreationMode) => {
    setStudioMode(mode);
    setActiveTab('studio');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 antialiased selection:bg-indigo-500 selection:text-white">
      <Header
        activeTab={activeTab}
        onTabChange={setActiveTab}
        theme={theme}
        onToggleTheme={handleToggleTheme}
        health={health}
        loadingHealth={loadingHealth}
        onRefreshHealth={fetchHealth}
      />

      <main className="flex-1 w-full">
        {activeTab === 'landing' ? (
          <LandingPage onStartCreation={handleStartCreation} />
        ) : (
          <StudioPage initialMode={studioMode} />
        )}
      </main>

      <Footer />
    </div>
  );
};
