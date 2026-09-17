import React from 'react';
import { Users, Target, Layers, Palette } from 'lucide-react';
import { AudienceOption, PurposeOption, SlideCountOption, StyleOption } from '@/types';

interface PresentationSettingsProps {
  audience: AudienceOption;
  onAudienceChange: (val: AudienceOption) => void;
  purpose: PurposeOption;
  onPurposeChange: (val: PurposeOption) => void;
  slideCount: SlideCountOption;
  onSlideCountChange: (val: SlideCountOption) => void;
  style: StyleOption;
  onStyleChange: (val: StyleOption) => void;
}

export const PresentationSettings: React.FC<PresentationSettingsProps> = ({
  audience,
  onAudienceChange,
  purpose,
  onPurposeChange,
  slideCount,
  onSlideCountChange,
  style,
  onStyleChange,
}) => {
  const audiences: Array<{ value: AudienceOption; label: string }> = [
    { value: 'general', label: 'General Audience' },
    { value: 'executives', label: 'C-Level & Executives' },
    { value: 'developers', label: 'Engineers & Tech' },
    { value: 'students', label: 'Academic & Students' },
    { value: 'investors', label: 'Investors & VC' },
    { value: 'sales_clients', label: 'Clients & Prospects' },
  ];

  const purposes: Array<{ value: PurposeOption; label: string }> = [
    { value: 'business', label: 'Business Strategy' },
    { value: 'pitch', label: 'Startup Pitch Deck' },
    { value: 'technical', label: 'Technical Deep-Dive' },
    { value: 'academic', label: 'Research & Science' },
    { value: 'training', label: 'Workshop & Training' },
    { value: 'case_study', label: 'Case Study & Results' },
  ];

  const slideCounts: Array<{ value: SlideCountOption; label: string }> = [
    { value: 'auto', label: 'Auto' },
    { value: '5', label: '5 Slides' },
    { value: '8', label: '8 Slides' },
    { value: '10', label: '10 Slides' },
    { value: '12', label: '12 Slides' },
    { value: '15', label: '15 Slides' },
    { value: '20', label: '20 Slides' },
  ];

  const styles: Array<{ value: StyleOption; label: string; desc: string }> = [
    { value: 'professional', label: 'Professional', desc: 'Balanced high-contrast corporate look' },
    { value: 'modern_dark', label: 'Modern Dark', desc: 'Sleek dark canvas with vibrant accents' },
    { value: 'minimal', label: 'Minimalist', desc: 'Spacious typography and clean whitespace' },
    { value: 'corporate', label: 'Executive', desc: 'Structured grid and formal color density' },
    { value: 'creative', label: 'Creative', desc: 'Expressive cards and bold visual anchors' },
  ];

  return (
    <div className="space-y-6">
      <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
        Presentation Configuration
      </h3>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Audience Selector */}
        <div className="space-y-2">
          <label htmlFor="audience-select" className="flex items-center space-x-1.5 text-xs font-semibold text-slate-300">
            <Users className="w-3.5 h-3.5 text-indigo-400" />
            <span>Target Audience</span>
          </label>
          <select
            id="audience-select"
            value={audience}
            onChange={(e) => onAudienceChange(e.target.value as AudienceOption)}
            className="w-full rounded-xl bg-slate-900 border border-slate-800 px-3.5 py-2.5 text-xs sm:text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 cursor-pointer"
          >
            {audiences.map((item) => (
              <option key={item.value} value={item.value} className="bg-slate-900 text-white">
                {item.label}
              </option>
            ))}
          </select>
        </div>

        {/* Purpose Selector */}
        <div className="space-y-2">
          <label htmlFor="purpose-select" className="flex items-center space-x-1.5 text-xs font-semibold text-slate-300">
            <Target className="w-3.5 h-3.5 text-violet-400" />
            <span>Presentation Purpose</span>
          </label>
          <select
            id="purpose-select"
            value={purpose}
            onChange={(e) => onPurposeChange(e.target.value as PurposeOption)}
            className="w-full rounded-xl bg-slate-900 border border-slate-800 px-3.5 py-2.5 text-xs sm:text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 cursor-pointer"
          >
            {purposes.map((item) => (
              <option key={item.value} value={item.value} className="bg-slate-900 text-white">
                {item.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Slide Count Selector */}
      <div className="space-y-2">
        <label className="flex items-center space-x-1.5 text-xs font-semibold text-slate-300">
          <Layers className="w-3.5 h-3.5 text-cyan-400" />
          <span>Deck Length</span>
        </label>
        <div className="grid grid-cols-4 sm:grid-cols-7 gap-1.5" role="group" aria-label="Deck Length">
          {slideCounts.map((item) => (
            <button
              key={item.value}
              type="button"
              aria-pressed={slideCount === item.value}
              onClick={() => onSlideCountChange(item.value)}
              className={`py-2 px-2 rounded-xl text-xs font-medium border text-center transition-all cursor-pointer ${
                slideCount === item.value
                  ? 'bg-indigo-600 border-indigo-500 text-white shadow-sm'
                  : 'bg-slate-900/80 border-slate-800 text-slate-400 hover:text-white hover:border-slate-700'
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {/* Visual Style Selection */}
      <div className="space-y-2">
        <label className="flex items-center space-x-1.5 text-xs font-semibold text-slate-300">
          <Palette className="w-3.5 h-3.5 text-emerald-400" />
          <span>Design Aesthetic</span>
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2" role="radiogroup" aria-label="Design Aesthetic">
          {styles.map((item) => (
            <div
              key={item.value}
              role="radio"
              aria-checked={style === item.value}
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  onStyleChange(item.value);
                }
              }}
              onClick={() => onStyleChange(item.value)}
              className={`p-3 rounded-xl border text-left cursor-pointer transition-all ${
                style === item.value
                  ? 'bg-indigo-600/15 border-indigo-500 ring-1 ring-indigo-500'
                  : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
              }`}
            >
              <p className="text-xs font-semibold text-white">{item.label}</p>
              <p className="text-[11px] text-slate-400 mt-0.5">{item.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
