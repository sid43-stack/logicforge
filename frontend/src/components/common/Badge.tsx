import React from 'react';

interface BadgeProps {
  variant?: 'severity' | 'status' | 'category' | 'tier' | 'neutral';
  value: string;
  className?: string;
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({
  variant = 'neutral',
  value,
  className = '',
  size = 'md',
}) => {
  const getColors = () => {
    const upper = value.toUpperCase();

    // Severity Colors
    if (variant === 'severity' || ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].includes(upper)) {
      switch (upper) {
        case 'CRITICAL':
          return 'bg-red-500/10 text-red-700 border-red-500/20';
        case 'HIGH':
          return 'bg-orange-500/10 text-orange-400 border-orange-500/20';
        case 'MEDIUM':
          return 'bg-amber-500/10 text-amber-700 border-amber-500/20';
        case 'LOW':
          return 'bg-emerald-500/10 text-emerald-700 border-emerald-500/20';
      }
    }

    // Status Colors
    if (variant === 'status' || ['COMPLETED', 'IN_PROGRESS', 'INCONCLUSIVE', 'CONFLICT_DETECTED'].includes(upper)) {
      switch (upper) {
        case 'COMPLETED':
          return 'bg-emerald-500/10 text-emerald-700 border-emerald-500/20';
        case 'IN_PROGRESS':
          return 'bg-gold-500/10 text-gold-700 border-gold-500/20';
        case 'INCONCLUSIVE':
          return 'bg-amber-500/10 text-amber-700 border-amber-500/20';
        case 'CONFLICT_DETECTED':
          return 'bg-red-500/10 text-red-700 border-red-500/20';
      }
    }

    // Category Colors
    if (variant === 'category') {
      return 'bg-gold-500/10 text-gold-700 border-gold-500/20';
    }

    // Source Tier Colors
    if (variant === 'tier') {
      switch (upper) {
        case 'STATIC_DOMAIN':
          return 'bg-gold-500/10 text-gold-700 border-gold-500/20';
        case 'USER_INPUT':
          return 'bg-gold-500/10 text-gold-700 border-gold-500/20';
        case 'RULE_DERIVED':
          return 'bg-emerald-500/10 text-emerald-700 border-emerald-500/20';
      }
    }

    return 'bg-[#EAE3D8] text-stone-700 border-stone-400';
  };

  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs font-medium';

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border ${getColors()} ${sizeClasses} ${className}`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current opacity-80" />
      {value.replace('_', ' ')}
    </span>
  );
};

