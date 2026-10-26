import React from 'react';
import { QueueStatus } from '../../types';

interface StatusBadgeProps {
  status: QueueStatus | string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const config: Record<string, { label: string; classes: string }> = {
    waiting: {
      label: 'Waiting in Queue',
      classes: 'bg-amber-100 text-amber-800 border-amber-200',
    },
    in_consultation: {
      label: 'In Consultation',
      classes: 'bg-sky-100 text-sky-800 border-sky-200 animate-pulse',
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

  const item = config[status] || { label: status, classes: 'bg-slate-100 text-slate-700 border-slate-200' };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${item.classes}`}>
      {item.label}
    </span>
  );
};
