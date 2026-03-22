import React, { useState } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import {
  BarChart3, ClipboardList, Search, Scale, ScrollText, Cpu,
  Briefcase, Settings, Bell, ChevronLeft, Menu, Shield, LogOut
} from 'lucide-react';

const navItems = [
  { path: 'dashboard', label: 'Dashboard', icon: BarChart3 },
  { path: 'pipeline', label: 'Applications', icon: ClipboardList },
  { path: 'fairness', label: 'Fairness', icon: Scale },
  { path: 'audit', label: 'Audit Log', icon: ScrollText },
  { path: 'models', label: 'Models', icon: Cpu },
  { path: 'portfolio', label: 'Portfolio', icon: Briefcase },
];

const AdminLayout: React.FC = () => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const navigate = useNavigate();

  return (
    <div className="flex h-screen bg-admin-bg overflow-hidden">
      {/* Mobile sidebar overlay */}
      {mobileSidebarOpen && (
        <div className="fixed inset-0 bg-black/50 z-40 md:hidden" onClick={() => setMobileSidebarOpen(false)} />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed md:relative z-50 h-full bg-admin-bg border-r border-admin-border flex flex-col transition-all duration-300
        ${sidebarCollapsed ? 'w-16' : 'w-60'}
        ${mobileSidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
      `}>
        {/* Logo */}
        <div className={`flex items-center gap-3 px-4 py-5 border-b border-admin-border ${sidebarCollapsed ? 'justify-center' : ''}`}>
          <Shield size={24} className="text-barclays-gold shrink-0" />
          {!sidebarCollapsed && (
            <div>
              <span className="font-display font-semibold text-admin-text text-sm">Barclays</span>
              <span className="block text-[10px] text-admin-muted font-body">Risk Intelligence</span>
            </div>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-4 space-y-1 px-2 overflow-y-auto">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={() => setMobileSidebarOpen(false)}
              className={({ isActive }) => `
                flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-body transition-all duration-200
                ${isActive
                  ? 'bg-admin-surface2 text-admin-accent border-l-3 border-admin-accent'
                  : 'text-admin-muted hover:text-admin-text hover:bg-admin-surface2/50'
                }
                ${sidebarCollapsed ? 'justify-center' : ''}
              `}
            >
              <item.icon size={18} className="shrink-0" />
              {!sidebarCollapsed && <span>{item.label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* Collapse toggle */}
        <div className="hidden md:flex border-t border-admin-border p-3">
          <button onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="w-full flex items-center justify-center p-2 text-admin-muted hover:text-admin-text rounded-lg hover:bg-admin-surface2 transition-colors">
            <ChevronLeft size={16} className={`transition-transform ${sidebarCollapsed ? 'rotate-180' : ''}`} />
          </button>
        </div>

        {/* User section */}
        <div className={`border-t border-admin-border p-3 ${sidebarCollapsed ? 'text-center' : ''}`}>
          <div className={`flex items-center gap-3 ${sidebarCollapsed ? 'justify-center' : ''}`}>
            <div className="w-8 h-8 rounded-full bg-admin-accent/20 flex items-center justify-center text-admin-accent text-xs font-semibold">
              RM
            </div>
            {!sidebarCollapsed && (
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-admin-text truncate font-body">Risk Manager</p>
                <p className="text-[10px] text-admin-muted font-body">v20250315</p>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* Main content area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <header className="h-14 bg-admin-surface border-b border-admin-border flex items-center justify-between px-4 shrink-0">
          <div className="flex items-center gap-3">
            <button onClick={() => setMobileSidebarOpen(true)} className="md:hidden p-1 text-admin-muted hover:text-admin-text">
              <Menu size={20} />
            </button>
          </div>
          <div className="flex items-center gap-3">
            <button className="relative p-2 text-admin-muted hover:text-admin-text rounded-lg hover:bg-admin-surface2 transition-colors">
              <Bell size={18} />
              <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-risk-very_high" />
            </button>
            <button onClick={() => navigate('/')} className="p-2 text-admin-muted hover:text-admin-text rounded-lg hover:bg-admin-surface2 transition-colors">
              <LogOut size={18} />
            </button>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default AdminLayout;
