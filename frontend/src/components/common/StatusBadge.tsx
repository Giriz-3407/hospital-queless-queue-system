import React from 'react';
import { QueueStatus } from '../../types';

interface StatusBadgeProps {
  status: QueueStatus | string;
  size?: 'sm' | 'md' | 'lg';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'sm' }) => {
  const norm = (status || '').toLowerCase().trim();

  const config: Record<string, { label: string; classes: string }> = {
    waiting: {
      label: 'Waiting in Queue',
      classes: 'bg-amber-100 text-amber-800 border-amber-200',
    },
    called: {
      label: 'Called - Proceed to Room',
      classes: 'bg-sky-100 text-sky-800 border-sky-300 animate-pulse font-bold',
    },
    in_consultation: {
      label: 'In Consultation',
      classes: 'bg-indigo-100 text-indigo-800 border-indigo-200 animate-pulse',
    },
    completed: {
      label: 'Completed',
      classes: 'bg-emerald-100 text-emerald-800 border-emerald-200',
    },
    cancelled: {
      label: 'Cancelled',
      classes: 'bg-slate-100 text-slate-700 border-slate-200',
    },
    no_show: {
      label: 'No Show',
      classes: 'bg-rose-100 text-rose-800 border-rose-200',
    },
  };

  const item = config[norm] || {
    label: status ? status.replace(/_/g, ' ') : 'Unknown',
    classes: 'bg-slate-100 text-slate-700 border-slate-200',
  };

  const sizeClasses =
    size === 'lg'
      ? 'px-3 py-1 text-sm'
      : size === 'md'
      ? 'px-2.5 py-0.5 text-xs'
      : 'px-2 py-0.5 text-[11px]';

  return (
    <span className={`inline-flex items-center font-semibold rounded-full border ${sizeClasses} ${item.classes}`}>
      {item.label}
    </span>
  );
};
