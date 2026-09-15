import React from 'react';
import { Box, Layers, Palette, ShieldCheck, CheckCircle2 } from 'lucide-react';

export const FeaturesGrid: React.FC = () => {
  const features = [
    {
      icon: Box,
      title: '100% Native PowerPoint Objects',
      description:
        'Generates actual editable shapes, text frames, tables, and native PowerPoint charts. Zero flat slide-level PNG rasterizations.',
      badge: 'Editability',
      color: 'indigo',
    },
    {
      icon: Layers,
      title: 'Semantic Visual Intelligence',
      description:
        'Automatically transforms bullet points into process diagrams, comparison cards, milestone timelines, and structured KPI grids.',
      badge: 'Visual Hierarchy',
      color: 'violet',
    },
    {
      icon: Palette,
      title: 'Reference PPT Design Transfer',
      description:
        'Deeply inspects reference presentations to extract color palettes, typography, and card archetypes as a visual contract for your new topic.',
      badge: 'Design Fidelity',
      color: 'cyan',
    },
    {
      icon: ShieldCheck,
      title: 'Automated Visual QA & Layout Fixes',
      description:
        'Uses Pillow font glyph metrics and collision detection to dynamically eliminate text overflow and alignment errors before saving.',
      badge: 'Quality Guardrail',
      color: 'emerald',
    },
  ];

  return (
    <section className="py-12 border-t border-slate-800/60 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="text-center max-w-2xl mx-auto mb-12">
        <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
          Engineered for Professional Presentations
        </h2>
        <p className="text-sm text-slate-400 mt-2">
          Bridging AI content synthesis with strict deterministic PowerPoint layout geometry.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {features.map((feat, idx) => {
          const Icon = feat.icon;
          return (
            <div
              key={idx}
              className="glass-panel rounded-2xl p-6 sm:p-7 transition-all hover:border-slate-700/90 relative group"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 text-indigo-400 group-hover:scale-105 transition-transform">
                  <Icon className="w-5 h-5" />
                </div>
                <span className="text-[11px] font-medium px-2.5 py-1 rounded-full bg-slate-800/80 text-slate-400 border border-slate-700/60">
                  {feat.badge}
                </span>
              </div>
              <h3 className="text-base font-semibold text-white group-hover:text-indigo-300 transition-colors">
                {feat.title}
              </h3>
              <p className="text-xs sm:text-sm text-slate-400 mt-2 leading-relaxed">
                {feat.description}
              </p>
              <div className="mt-4 flex items-center gap-1.5 text-xs text-slate-500">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>Deterministic Engine Guarantee</span>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
};
