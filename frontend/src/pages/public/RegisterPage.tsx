import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { Card, CardContent, CardFooter } from '../../components/ui/Card';
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';
import { Alert } from '../../components/ui/Alert';
import { Activity, UserPlus } from 'lucide-react';

export const RegisterPage: React.FC = () => {
  const { register } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const searchParams = new URLSearchParams(location.search);
  const redirectParam = searchParams.get('redirect');

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [phone, setPhone] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password.length < 8) {
      setError('Password must be at least 8 characters long.');
      return;
    }

    setIsLoading(true);
    try {
      await register({ name, email, password, phone, role: 'patient' });
      if (redirectParam) {
        navigate(redirectParam, { replace: true });
      } else {
        navigate('/patient/dashboard', { replace: true });
      }
    } catch (err: any) {
      setError(err.message || 'Registration failed. Please check the details entered.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-sky-600 text-white shadow-lg shadow-sky-600/30">
            <Activity className="w-7 h-7" />
          </div>
          <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">Patient Registration</h2>
          <p className="text-sm text-slate-500">Register to join virtual queues and receive live hospital turn alerts</p>
        </div>

        <Card>
          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-4 pt-6">
              {error && <Alert variant="error">{error}</Alert>}

              <Input
                label="Full Name"
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Jane Doe"
              />

              <Input
                label="Email Address"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="jane.doe@example.com"
                autoComplete="email"
              />

              <Input
                label="Phone Number (Optional)"
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+1 555-0123"
              />

              <Input
                label="Password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Minimum 8 characters"
                helperText="Must be at least 8 characters long"
              />

              <Button
                type="submit"
                size="lg"
                isLoading={isLoading}
                className="w-full gap-2 shadow-sm"
              >
                <UserPlus className="w-4 h-4" /> Create Patient Account
              </Button>
            </CardContent>

            <CardFooter className="justify-center border-t border-slate-100 py-4 text-xs text-slate-500">
              Already have an account?{' '}
              <Link
                to={redirectParam ? `/login?redirect=${encodeURIComponent(redirectParam)}` : '/login'}
                className="text-sky-600 font-semibold hover:underline ml-1"
              >
                Sign in here
              </Link>
            </CardFooter>
          </form>
        </Card>
      </div>
    </div>
  );
};
