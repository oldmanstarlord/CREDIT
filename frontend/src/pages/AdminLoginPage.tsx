import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../store/store';
import { login, clearAuthError, fetchProfile } from '../store/authSlice';
import { Eye, EyeOff, Shield, ArrowLeft } from 'lucide-react';

const AdminLoginPage: React.FC = () => {
  const [form, setForm] = useState({ email: '', password: '' });
  const [showPassword, setShowPassword] = useState(false);
  const dispatch = useDispatch<AppDispatch>();
  const navigate = useNavigate();
  const { loading, error } = useSelector((s: RootState) => s.auth);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await dispatch(login({ email: form.email, password: form.password })).unwrap();
      const profileResult = await dispatch(fetchProfile()).unwrap();
      const userRole = profileResult.role?.toUpperCase();
      
      // Check if user has admin role
      if (userRole === 'ADMIN' || userRole === 'ANALYST' || userRole === 'RISK_MANAGER' || userRole === 'SENIOR_ANALYST') {
        navigate('/admin/dashboard');
      } else {
        // Not an admin - show error and logout
        dispatch(clearAuthError());
        alert('Access denied. This portal is for administrators only.');
        navigate('/');
      }
    } catch {}
  };

  return (
    <div className="min-h-screen flex">
      {/* Left Panel - Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-barclays-navy bg-pattern-navy flex-col justify-center items-center p-16 relative">
        <Link to="/" className="absolute top-8 left-8 flex items-center gap-2 text-white/70 hover:text-white transition-colors">
          <ArrowLeft size={18} />
          <span className="text-sm">Back to portal selection</span>
        </Link>

        <div className="max-w-md text-center">
          <div className="w-20 h-20 rounded-2xl bg-white/10 flex items-center justify-center mx-auto mb-6">
            <Shield size={40} className="text-barclays-gold" />
          </div>
          <h1 className="text-4xl font-display font-bold text-white mb-4">
            Admin Portal
          </h1>
          <p className="text-white/70 text-lg font-body leading-relaxed">
            Secure access for administrators, analysts, and risk managers
          </p>

          <div className="mt-12 space-y-4">
            <div className="flex items-center gap-3 text-white/60">
              <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center text-xs font-bold">1</div>
              <span className="text-sm">Review loan applications</span>
            </div>
            <div className="flex items-center gap-3 text-white/60">
              <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center text-xs font-bold">2</div>
              <span className="text-sm">Make approval decisions</span>
            </div>
            <div className="flex items-center gap-3 text-white/60">
              <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center text-xs font-bold">3</div>
              <span className="text-sm">Monitor system performance</span>
            </div>
          </div>
        </div>
      </div>

      {/* Right Panel - Login Form */}
      <div className="w-full lg:w-1/2 bg-user-bg flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          <Link to="/" className="lg:hidden flex items-center gap-2 text-user-muted hover:text-user-text transition-colors mb-8">
            <ArrowLeft size={18} />
            <span className="text-sm">Back</span>
          </Link>

          <div className="mb-8">
            <h2 className="text-3xl font-display font-bold text-user-text mb-2">
              Admin Sign In
            </h2>
            <p className="text-sm text-user-muted font-body">
              Enter your administrator credentials
            </p>
          </div>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-user-text mb-2 font-body">
                Email Address
              </label>
              <input
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="w-full px-4 py-3 border border-user-border rounded-input focus:outline-none focus:ring-2 focus:ring-barclays-navy text-user-text font-body"
                placeholder="admin@barclays.com"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-user-text mb-2 font-body">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  className="w-full px-4 py-3 border border-user-border rounded-input focus:outline-none focus:ring-2 focus:ring-barclays-navy text-user-text font-body pr-12"
                  placeholder="••••••••"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-user-muted hover:text-user-text"
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-barclays-navy text-white py-3 rounded-input font-semibold hover:bg-barclays-navy/90 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-body"
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-xs text-blue-800 font-body">
              <strong>Test Credentials:</strong><br />
              Email: admin@barclays.com<br />
              Password: Admin123!@#
            </p>
          </div>

          <div className="mt-6 text-center">
            <p className="text-sm text-user-muted font-body">
              Not an administrator?{' '}
              <Link to="/user/login" className="text-barclays-navy hover:underline font-medium">
                Go to User Portal
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminLoginPage;
