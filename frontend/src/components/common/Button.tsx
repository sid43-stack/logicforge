import React from 'react';
import { Loader2 } from 'lucide-react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  icon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  isLoading = false,
  icon,
  children,
  className = '',
  disabled,
  ...props
}) => {
  const baseClasses =
    'inline-flex items-center justify-center font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[#F2EEE4] disabled:opacity-50 disabled:cursor-not-allowed rounded-lg';

  const sizeClasses = {
    sm: 'text-xs px-3 py-1.5 gap-1.5',
    md: 'text-sm px-4 py-2 gap-2',
    lg: 'text-base px-6 py-3 gap-2.5',
  }[size];

  const variantClasses = {
    primary:
      'bg-gold-600 hover:bg-gold-500 text-[#2B2822] shadow-sm focus:ring-gold-500 border border-gold-500/30',
    secondary:
      'bg-[#EAE3D8] hover:bg-[#D8D0C0] text-stone-900 border border-stone-400 focus:ring-stone-500',
    outline:
      'bg-transparent hover:bg-[#EAE3D8]/60 text-stone-700 hover:text-[#2B2822] border border-stone-400 focus:ring-gold-500',
    danger:
      'bg-red-600/90 hover:bg-red-500 text-[#2B2822] border border-red-500/30 focus:ring-red-500',
    ghost:
      'bg-transparent hover:bg-[#EAE3D8]/50 text-stone-600 hover:text-stone-900 border-none focus:ring-stone-600',
  }[variant];

  return (
    <button
      className={`${baseClasses} ${sizeClasses} ${variantClasses} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <Loader2 className="w-4 h-4 animate-spin text-current" />
      ) : icon ? (
        <span className="flex-shrink-0">{icon}</span>
      ) : null}
      {children}
    </button>
  );
};

