import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  hoverable?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  onClick,
  hoverable = false,
}) => {
  return (
    <div
      onClick={onClick}
      className={`bg-[#FFFCF5] border border-[#D8D0C0] rounded-xl p-5 shadow-sm ${
        hoverable
          ? 'hover:border-stone-500 transition-all cursor-pointer hover:shadow-md'
          : ''
      } ${className}`}
    >
      {children}
    </div>
  );
};

export const CardHeader: React.FC<{
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
  icon?: React.ReactNode;
  className?: string;
}> = ({ title, subtitle, action, icon, className = '' }) => {
  return (
    <div className={`flex items-start justify-between gap-4 mb-4 ${className}`}>
      <div className="flex items-start gap-3">
        {icon && <div className="p-2 rounded-lg bg-[#EAE3D8]/80 border border-stone-400/60 text-gold-700 mt-0.5">{icon}</div>}
        <div>
          <h3 className="text-base font-semibold text-stone-900">{title}</h3>
          {subtitle && <p className="text-xs text-stone-600 mt-0.5">{subtitle}</p>}
        </div>
      </div>
      {action && <div>{action}</div>}
    </div>
  );
};

