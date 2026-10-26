import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { Card, CardContent, CardFooter } from '../../components/ui/Card';
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';
import { Alert } from '../../components/ui/Alert';
import { Activity, KeyRound, UserCheck, Stethoscope } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const from = (location.state as any)?.from?.pathname || '/patient/dashboard';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      await login({ email, password });
      // If logging in as staff/doctor, navigate to staff dashboard
      navigate(from, { replace: true });
    } catch (err: any) {
      setError(err.message || 'Failed to authenticate. Please check your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  const fillDemoPatient = () => {
    setEmail('patient@hospital.org');
    setPassword('Patient123!');
  };

  const fillDemoDoctor = () => {
    setEmail('dr.smith@hospital.org');
    setPassword('Doctor123!');
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-sky-600 text-white shadow-lg shadow-sky-600/30">
            <Activity className="w-7 h-7" />
          </div>
          <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">Sign In to Queueless</h2>
          <p className="text-sm text-slate-500">Access your virtual queue tickets or staff dashboard</p>
        </div>

        {/* Demo Fast-Fill Helper */}
        <div className="bg-sky-50 border border-sky-100 rounded-xl p-3 text-xs text-slate-600 flex flex-col gap-2">
          <span className="font-semibold text-sky-900 flex items-center gap-1">
            <KeyRound className="w-3.5 h-3.5" /> Quick Fill Demo Credentials:
          </span>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={fillDemoPatient}
              className="flex-1 py-1.5 px-2 bg-white border border-sky-200 rounded-md text-sky-700 font-medium hover:bg-sky-100/50 flex items-center justify-center gap-1 transition-colors"
            >
              <UserCheck className="w-3.5 h-3.5" /> Patient
            </button>
            <button
              type="button"
              onClick={fillDemoDoctor}
              className="flex-1 py-1.5 px-2 bg-white border border-sky-200 rounded-md text-sky-700 font-medium hover:bg-sky-100/50 flex items-center justify-center gap-1 transition-colors"
            >
              <Stethoscope className="w-3.5 h-3.5" /> Doctor/Staff
            </button>
          </div>
        </div>

        <Card>
          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-4 pt-6">
              {error && <Alert variant="error">{error}</Alert>}

              <Input
                label="Email Address"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                autoComplete="email"
              />

              <Input
                label="Password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                autoComplete="current-password"
              />

              <Button type="submit" isLoading={isLoading} className="w-full mt-2">
                Sign In
              </Button>
            </CardContent>

            <CardFooter className="justify-center text-center">
              <p className="text-xs text-slate-600">
                Don't have an account yet?{' '}
                <Link to="/register" className="font-semibold text-sky-600 hover:text-sky-700 underline">
                  Register as a Patient
                </Link>
              </p>
            </CardFooter>
          </form>
        </Card>
      </div>
    </div>
  );
};
