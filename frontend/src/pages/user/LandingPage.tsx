import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../../store/store';
import { login, register, clearAuthError, fetchProfile } from '../../store/authSlice';
import { Eye, EyeOff, ArrowRight, Shield } from 'lucide-react';

const LandingPage: React.FC = () => {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [form, setForm] = useState({ email: '', phone_number: '', password: '', full_name: '', confirm_password: '' });
  const [showPassword, setShowPassword] = useState(false);
  const dispatch = useDispatch<AppDispatch>();
  const navigate = useNavigate();
  const { loading, error } = useSelector((s: RootState) => s.auth);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (mode === 'register' && form.password !== form.confirm_password) return;
    try {
      if (mode === 'login') {
        await dispatch(login({ email: form.email, password: form.password })).unwrap();
      } else {
        await dispatch(register({
          email: form.email,
          phone_number: form.phone_number,
          password: form.password,
          full_name: form.full_name,
        })).unwrap();
      }
      
      // User portal always goes to application page
      navigate('/apply');
    } catch {}
  };

  return (
    <div className="min-h-screen flex flex-col lg:flex-row">
      {/* Left / Top panel — Navy hero */}
      <div className="relative lg:w-1/2 bg-barclays-navy bg-pattern-navy flex flex-col justify-center items-center p-8 lg:p-16 min-h-[40vh] lg:min-h-screen">
        <div className="absolute top-8 left-8">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-white/10 flex items-center justify-center">
              <Shield size={22} className="text-barclays-gold" />
            </div>
            <span className="text-white/90 font-display text-lg font-semibold tracking-tight">Barclays</span>
          </div>
        </div>

        <div className="max-w-md text-center lg:text-left">
          <h1 className="text-4xl lg:text-hero font-display font-bold text-white leading-tight">
            Your first loan
            <br />
            <span className="text-barclays-gold">starts here.</span>
          </h1>
          <p className="mt-4 text-white/70 text-base lg:text-lg font-body leading-relaxed">
            No credit history required. Fair, transparent, and explained — powered by AI.
          </p>

          <div className="mt-8 flex flex-wrap gap-3 justify-center lg:justify-start">
            {['Farmers', 'Gig Workers', 'MSME Owners', 'Daily Workers'].map((label) => (
              <span key={label} className="px-3 py-1.5 text-xs font-medium text-white/80 bg-white/10 rounded-pill backdrop-blur-sm">
                {label}
              </span>
            ))}
          </div>

          <div className="mt-10 grid grid-cols-3 gap-6">
            {[
              { value: '₹10K–₹10L', label: 'Loan Range' },
              { value: '300–850', label: 'Credit Score' },
              { value: '<2 hrs', label: 'Decision Time' },
            ].map((stat) => (
              <div key={stat.label} className="text-center lg:text-left">
                <div className="text-xl font-display font-bold text-barclays-gold">{stat.value}</div>
                <div className="text-xs text-white/50 mt-1 font-body">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right / Bottom panel — Form */}
      <div className="lg:w-1/2 bg-user-bg flex items-center justify-center p-8 lg:p-16">
        <div className="w-full max-w-md">
          <div className="flex bg-gray-100 rounded-pill p-1 mb-8">
            {(['login', 'register'] as const).map((m) => (
              <button
                key={m}
                onClick={() => { setMode(m); dispatch(clearAuthError()); }}
                className={`flex-1 py-2.5 text-sm font-semibold rounded-pill transition-all duration-300 ${
                  mode === m ? 'bg-white shadow-sm text-barclays-navy' : 'text-user-muted hover:text-user-text'
                }`}
              >
                {m === 'login' ? 'Sign In' : 'Create Account'}
              </button>
            ))}
          </div>

          <h2 className="text-2xl font-display font-bold text-user-text mb-2">
            {mode === 'login' ? 'Welcome back' : 'Begin your application'}
          </h2>
          <p className="text-sm text-user-muted mb-6 font-body">
            {mode === 'login' ? 'Check your application status or apply for a new loan.' : 'Create an account to start your loan application process.'}
          </p>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-input text-sm text-red-600 font-body">
              {typeof error === 'string' ? error : 'An error occurred'}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === 'register' && (
              <>
                <div className="relative">
                  <input
                    type="text" placeholder=" " value={form.full_name}
                    onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                    className="peer w-full px-4 pt-5 pb-2 border border-user-border rounded-input text-sm font-body focus:outline-none focus:border-barclays-navy transition-colors"
                    required
                  />
                  <label className="absolute left-4 top-2 text-xs text-user-muted font-body peer-placeholder-shown:top-4 peer-placeholder-shown:text-sm peer-focus:top-2 peer-focus:text-xs peer-focus:text-barclays-navy transition-all duration-200">
                    Full Name
                  </label>
                </div>
                <div className="relative">
                  <input
                    type="tel" placeholder=" " value={form.phone_number}
                    onChange={(e) => setForm({ ...form, phone_number: e.target.value })}
                    className="peer w-full px-4 pt-5 pb-2 border border-user-border rounded-input text-sm font-body focus:outline-none focus:border-barclays-navy transition-colors"
                  />
                  <label className="absolute left-4 top-2 text-xs text-user-muted font-body peer-placeholder-shown:top-4 peer-placeholder-shown:text-sm peer-focus:top-2 peer-focus:text-xs peer-focus:text-barclays-navy transition-all duration-200">
                    Phone Number (+91)
                  </label>
                </div>
              </>
            )}

            <div className="relative">
              <input
                type="email" placeholder=" " value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="peer w-full px-4 pt-5 pb-2 border border-user-border rounded-input text-sm font-body focus:outline-none focus:border-barclays-navy transition-colors"
                required
              />
              <label className="absolute left-4 top-2 text-xs text-user-muted font-body peer-placeholder-shown:top-4 peer-placeholder-shown:text-sm peer-focus:top-2 peer-focus:text-xs peer-focus:text-barclays-navy transition-all duration-200">
                Email Address
              </label>
            </div>

            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'} placeholder=" " value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                className="peer w-full px-4 pt-5 pb-2 pr-12 border border-user-border rounded-input text-sm font-body focus:outline-none focus:border-barclays-navy transition-colors"
                required minLength={8}
              />
              <label className="absolute left-4 top-2 text-xs text-user-muted font-body peer-placeholder-shown:top-4 peer-placeholder-shown:text-sm peer-focus:top-2 peer-focus:text-xs peer-focus:text-barclays-navy transition-all duration-200">
                Password
              </label>
              <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-4 text-user-muted hover:text-user-text">
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>

            {mode === 'register' && (
              <div className="relative">
                <input
                  type="password" placeholder=" " value={form.confirm_password}
                  onChange={(e) => setForm({ ...form, confirm_password: e.target.value })}
                  className="peer w-full px-4 pt-5 pb-2 border border-user-border rounded-input text-sm font-body focus:outline-none focus:border-barclays-navy transition-colors"
                  required
                />
                <label className="absolute left-4 top-2 text-xs text-user-muted font-body peer-placeholder-shown:top-4 peer-placeholder-shown:text-sm peer-focus:top-2 peer-focus:text-xs peer-focus:text-barclays-navy transition-all duration-200">
                  Confirm Password
                </label>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3.5 bg-barclays-navy text-white font-semibold rounded-input hover:bg-barclays-teal transition-all duration-300 flex items-center justify-center gap-2 disabled:opacity-60"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  {mode === 'login' ? 'Sign In' : 'Create Account'}
                  <ArrowRight size={18} />
                </>
              )}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-user-border">
            <p className="text-xs text-user-muted text-center font-body">
              Use your real account credentials. Test shortcut access has been removed.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LandingPage;
