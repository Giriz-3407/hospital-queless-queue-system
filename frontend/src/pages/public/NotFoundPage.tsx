import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../../components/ui/Button';
import { Home } from 'lucide-react';

export const NotFoundPage: React.FC = () => {
  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center text-center px-4">
      <span className="text-6xl font-black text-sky-600 mb-2">404</span>
      <h2 className="text-2xl font-bold text-slate-900 mb-2">Page Not Found</h2>
      <p className="text-sm text-slate-500 max-w-sm mb-6">
        The page or queue ticket you are looking for does not exist or has been moved.
      </p>
      <Link to="/">
        <Button variant="primary" className="gap-2">
          <Home className="w-4 h-4" /> Return Home
        </Button>
      </Link>
    </div>
  );
};
