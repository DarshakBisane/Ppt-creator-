import React from 'react';
import { AlertCircle, X } from 'lucide-react';

interface ErrorAlertProps {
  title?: string;
  message: string;
  onDismiss?: () => void;
  className?: string;
}

export const ErrorAlert: React.FC<ErrorAlertProps> = ({
  title = 'Validation Error',
  message,
  onDismiss,
  className = '',
}) => {
  return (
    <div
      role="alert"
      className={`p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 flex items-start justify-between gap-3 text-sm animate-in fade-in duration-200 ${className}`}
    >
      <div className="flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
        <div>
          {title && <h5 className="font-semibold text-rose-200">{title}</h5>}
          <p className="text-xs sm:text-sm text-rose-300/90 mt-0.5 leading-relaxed">{message}</p>
        </div>
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="p-1 rounded-lg text-rose-400 hover:text-rose-200 hover:bg-rose-500/20 transition-colors"
          aria-label="Dismiss error"
        >
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
};
