import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Users, ArrowRight, Building2 } from 'lucide-react';

const PortalSelectionPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-barclays-navy via-barclays-navy to-barclays-blue flex items-center justify-center p-6">
      <div className="max-w-5xl w-full">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-lg bg-white/10 flex items-center justify-center">
              <Shield size={28} className="text-barclays-gold" />
            </div>
            <span className="text-white font-display text-2xl font-semibold tracking-tight">Barclays Credit Intelligence</span>
          </div>
          <h1 className="text-4xl font-display font-bold text-white mb-3">
            Welcome! Choose Your Portal
          </h1>
          <p className="text-white/70 text-lg font-body">
            Select the portal that matches your role
          </p>
        </div>

        {/* Portal Cards */}
        <div className="grid md:grid-cols-2 gap-6">
          {/* User Portal Card */}
          <button
            onClick={() => navigate('/user/login')}
            className="group relative bg-white rounded-2xl p-8 text-left hover:shadow-2xl transition-all duration-300 hover:-translate-y-1"
          >
            <div className="absolute top-6 right-6 w-16 h-16 rounded-full bg-barclays-lightblue flex items-center justify-center group-hover:scale-110 transition-transform">
              <Users size={32} className="text-barclays-navy" />
            </div>

            <div className="pr-20">
              <h2 className="text-2xl font-display font-bold text-barclays-navy mb-3">
                User Portal
              </h2>
              <p className="text-gray-600 font-body mb-6 leading-relaxed">
                Apply for loans, check your credit score, and manage your applications
              </p>

              <div className="space-y-2 mb-6">
                <div className="flex items-center gap-2 text-sm text-gray-700">
                  <div className="w-1.5 h-1.5 rounded-full bg-barclays-teal"></div>
                  <span>Submit loan applications</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-700">
                  <div className="w-1.5 h-1.5 rounded-full bg-barclays-teal"></div>
                  <span>View credit scores & explanations</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-700">
                  <div className="w-1.5 h-1.5 rounded-full bg-barclays-teal"></div>
                  <span>Use what-if simulator</span>
                </div>
              </div>

              <div className="flex items-center gap-2 text-barclays-navy font-semibold group-hover:gap-3 transition-all">
                <span>Continue as User</span>
                <ArrowRight size={20} />
              </div>
            </div>
          </button>

          {/* Admin Portal Card */}
          <button
            onClick={() => navigate('/admin/login')}
            className="group relative bg-white rounded-2xl p-8 text-left hover:shadow-2xl transition-all duration-300 hover:-translate-y-1"
          >
            <div className="absolute top-6 right-6 w-16 h-16 rounded-full bg-barclays-gold/20 flex items-center justify-center group-hover:scale-110 transition-transform">
              <Building2 size={32} className="text-barclays-navy" />
            </div>

            <div className="pr-20">
              <h2 className="text-2xl font-display font-bold text-barclays-navy mb-3">
                Admin Portal
              </h2>
              <p className="text-gray-600 font-body mb-6 leading-relaxed">
                Review applications, make decisions, and monitor system performance
              </p>

              <div className="space-y-2 mb-6">
                <div className="flex items-center gap-2 text-sm text-gray-700">
                  <div className="w-1.5 h-1.5 rounded-full bg-barclays-gold"></div>
                  <span>Review loan applications</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-700">
                  <div className="w-1.5 h-1.5 rounded-full bg-barclays-gold"></div>
                  <span>Make approval decisions</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-700">
                  <div className="w-1.5 h-1.5 rounded-full bg-barclays-gold"></div>
                  <span>Monitor fairness & risk</span>
                </div>
              </div>

              <div className="flex items-center gap-2 text-barclays-navy font-semibold group-hover:gap-3 transition-all">
                <span>Continue as Admin</span>
                <ArrowRight size={20} />
              </div>
            </div>
          </button>
        </div>

        {/* Footer Note */}
        <div className="text-center mt-8">
          <p className="text-white/50 text-sm font-body">
            Don't have an account? You can register after selecting your portal
          </p>
        </div>
      </div>
    </div>
  );
};

export default PortalSelectionPage;
