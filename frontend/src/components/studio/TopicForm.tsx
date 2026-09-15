import React from 'react';
import { Lightbulb } from 'lucide-react';

interface TopicFormProps {
  topic: string;
  onChange: (value: string) => void;
  error?: string | null;
}

export const TopicForm: React.FC<TopicFormProps> = ({ topic, onChange, error }) => {
  const suggestions = [
    'Cloud-Native Microservices Architecture & Migration Strategy',
    'AI in Healthcare: Clinical Diagnostics & Ethical Governance',
    'Quarterly Executive Financial Performance & Growth Vectors',
    'Cybersecurity Threat Landscape: Zero Trust Implementation',
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <label htmlFor="topic-input" className="block text-sm font-semibold text-slate-200">
          Presentation Topic & Prompt <span className="text-rose-400">*</span>
        </label>
        <span className="text-xs font-mono text-slate-500">
          {topic.length} characters
        </span>
      </div>

      <div className="relative">
        <textarea
          id="topic-input"
          value={topic}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Describe your presentation topic in detail. For example: 'Explain how generative AI transforms modern corporate finance with process workflows, KPI metrics, and risk mitigation models.'"
          rows={5}
          className={`w-full rounded-2xl bg-slate-900/90 border px-4 py-3.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all resize-y ${
            error ? 'border-rose-500/80 ring-1 ring-rose-500/50' : 'border-slate-800 hover:border-slate-700'
          }`}
        />
      </div>

      {error && (
        <p className="text-xs text-rose-400 font-medium">{error}</p>
      )}

      {/* Suggested Inspiration Prompts */}
      <div className="space-y-2 pt-1">
        <div className="flex items-center space-x-1.5 text-xs text-slate-400">
          <Lightbulb className="w-3.5 h-3.5 text-amber-400" />
          <span>Quick Inspiration Prompts:</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {suggestions.map((sug, i) => (
            <button
              key={i}
              type="button"
              onClick={() => onChange(sug)}
              className="text-[11px] text-left px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 text-slate-300 hover:text-white transition-all cursor-pointer"
            >
              {sug}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
