import React from 'react';
import { Sparkles, Sun, Moon, RefreshCw, Presentation, Home } from 'lucide-react';
import { ActiveTab, HealthResponse, Theme } from '@/types';

interface HeaderProps {
  activeTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
  theme: Theme;
  onToggleTheme: () => void;
  health: HealthResponse | null;
  loadingHealth: boolean;
  onRefreshHealth: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  onTabChange,
  theme,
  onToggleTheme,
  health,
  loadingHealth,
  onRefreshHealth,
}) => {
  return (
    <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div
          onClick={() => onTabChange('landing')}
          className="flex items-center space-x-3 cursor-pointer group select-none"
        >
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-violet-500 flex items-center justify-center shadow-lg shadow-indigo-500/20 group-hover:scale-105 transition-transform">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <span className="text-lg font-bold tracking-tight text-white block">
              PresenAI
            </span>
            <span className="text-[10px] text-slate-400 font-mono -mt-1 block uppercase tracking-wider">
              Presentation Studio
            </span>
          </div>
        </div>

        {/* Center Nav Tabs */}
        <nav className="flex items-center space-x-1 bg-slate-950/60 p-1 rounded-xl border border-slate-800/80">
          <button
            onClick={() => onTabChange('landing')}
            className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTab === 'landing'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
          >
            <Home className="w-3.5 h-3.5" />
            <span>Overview</span>
          </button>
          <button
            onClick={() => onTabChange('studio')}
            className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTab === 'studio'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
          >
            <Presentation className="w-3.5 h-3.5" />
            <span>Studio</span>
          </button>
        </nav>

        {/* Right Tools: Backend Badge & Theme Toggle */}
        <div className="flex items-center space-x-3">
          <div className="hidden sm:flex items-center space-x-2 px-3 py-1.5 rounded-full bg-slate-950/80 border border-slate-800 text-xs">
            <div
              className={`w-2 h-2 rounded-full ${
                loadingHealth
                  ? 'bg-amber-400 animate-pulse'
                  : health
                  ? 'bg-emerald-400'
                  : 'bg-rose-500'
              }`}
            />
            <span className="text-slate-300 font-medium">
              {loadingHealth
                ? 'Checking API...'
                : health
                ? 'API Online'
                : 'API Offline'}
            </span>
            <button
              onClick={onRefreshHealth}
              disabled={loadingHealth}
              className="ml-1 text-slate-500 hover:text-slate-300 transition-colors disabled:opacity-40"
              title="Refresh API Health"
            >
              <RefreshCw className={`w-3 h-3 ${loadingHealth ? 'animate-spin' : ''}`} />
            </button>
          </div>

          <button
            onClick={onToggleTheme}
            className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition-colors"
            title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? (
              <Sun className="w-4 h-4 text-amber-400" />
            ) : (
              <Moon className="w-4 h-4 text-indigo-400" />
            )}
          </button>
        </div>
      </div>
    </header>
  );
};
