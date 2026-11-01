import React from 'react';
import { RefreshCw, XCircle } from 'lucide-react';
import { Button } from './Button';
import { ApiError } from '../../types';

interface ErrorMessageProps {
  error: ApiError | string | null;
  onRetry?: () => void;
  className?: string;
  title?: string;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({
  error,
  onRetry,
  className = '',
  title = 'An error occurred',
}) => {
  if (!error) return null;

  const detailText = typeof error === 'string' ? error : error.detail;
  const errorCode = typeof error === 'string' ? undefined : error.error_code;

  return (
    <div
      className={`rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-red-800 ${className}`}
      role="alert"
    >
      <div className="flex items-start gap-3">
        <XCircle className="w-5 h-5 text-red-700 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <div className="flex items-center justify-between gap-2">
            <h4 className="text-sm font-semibold text-red-800">{title}</h4>
            {errorCode && (
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-red-950/60 border border-red-800/50 text-red-700">
                {errorCode}
              </span>
            )}
          </div>
          <p className="text-xs text-red-800/90 mt-1 leading-relaxed">{detailText}</p>

          {onRetry && (
            <div className="mt-3">
              <Button
                variant="outline"
                size="sm"
                onClick={onRetry}
                icon={<RefreshCw className="w-3.5 h-3.5" />}
                className="border-red-500/30 text-red-800 hover:bg-red-500/20"
              >
                Retry Request
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
