import React from 'react';
import { Sparkles, Cpu, Download } from 'lucide-react';

export const HowItWorks: React.FC = () => {
  const steps = [
    {
      step: '01',
      icon: Sparkles,
      title: 'Specify Topic or Reference Deck',
      description:
        'Enter your topic with target audience and purpose, or upload an existing PowerPoint presentation to transfer its design system.',
    },
    {
      step: '02',
      icon: Cpu,
      title: 'AI Blueprint & Layout Resolution',
      description:
        'The system designs slide progressions, selects semantic visual models, and computes exact container coordinates on a 1920×1080 canvas.',
    },
    {
      step: '03',
      icon: Download,
      title: 'Native .PPTX Generation & QA',
      description:
        'Shapes, text frames, tables, and native charts are assembled via OpenXML, checked for overflow, and delivered as an editable file.',
    },
  ];

  return (
    <section className="py-12 border-t border-slate-800/60 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mb-8">
      <div className="text-center max-w-2xl mx-auto mb-12">
        <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
          How the Pipeline Works
        </h2>
        <p className="text-sm text-slate-400 mt-2">
          From abstract concept to native PowerPoint in three deterministic steps.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative">
        {steps.map((st, idx) => {
          const Icon = st.icon;
          return (
            <div
              key={idx}
              className="glass-card rounded-2xl p-6 relative border border-slate-800 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="p-3 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                    <Icon className="w-5 h-5" />
                  </div>
                  <span className="text-xl font-bold text-slate-700 font-mono">
                    {st.step}
                  </span>
                </div>
                <h3 className="text-base font-semibold text-white mb-2">{st.title}</h3>
                <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
                  {st.description}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
};
