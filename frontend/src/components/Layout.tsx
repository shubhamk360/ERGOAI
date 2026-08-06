import React from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Camera, BarChart3, History, FileText, User, Settings as SettingsIcon, LogOut } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import clsx from 'clsx';
import { twMerge } from 'tailwind-merge';

const cn = (...inputs: (string | undefined | null | false)[]) => {
  return twMerge(clsx(inputs));
};

const Layout = () => {
  const { logout, user } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Live Detection', path: '/live', icon: Camera },
    { name: 'Analytics', path: '/analytics', icon: BarChart3 },
    { name: 'Session History', path: '/history', icon: History },
    { name: 'Reports', path: '/reports', icon: FileText },
    { name: 'Profile', path: '/profile', icon: User },
    { name: 'Settings', path: '/settings', icon: SettingsIcon },
  ];

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col z-20 shadow-2xl relative">
        <div className="p-6 flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-tr from-violet-600 to-indigo-500 rounded-xl flex items-center justify-center shadow-lg shadow-violet-500/30">
            <Camera className="w-5 h-5 text-white" />
          </div>
          <span className="text-xl font-bold tracking-tight text-white">ERGOAI</span>
        </div>
        
        <div className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.name}
              to={item.path}
              className={({ isActive }) => cn(
                "flex items-center space-x-3 px-3 py-2.5 rounded-xl transition-all duration-200 group",
                isActive 
                  ? "bg-violet-600/10 text-violet-400" 
                  : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
              )}
            >
              <item.icon className={cn("w-5 h-5 transition-colors")} />
              <span className="font-medium">{item.name}</span>
            </NavLink>
          ))}
        </div>

        <div className="p-4 border-t border-slate-800">
          <div className="flex items-center space-x-3 px-3 py-3 rounded-xl bg-slate-900 mb-2">
            <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center flex-shrink-0">
              <User className="w-4 h-4 text-slate-400" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-200 truncate">{user?.username}</p>
            </div>
          </div>
          <button 
            onClick={handleLogout}
            className="flex items-center space-x-3 px-3 py-2.5 rounded-xl w-full text-slate-400 hover:bg-red-500/10 hover:text-red-400 transition-all group"
          >
            <LogOut className="w-5 h-5" />
            <span className="font-medium">Sign out</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 relative overflow-y-auto">
        {/* Subtle background glow */}
        <div className="absolute top-[-20%] right-[-10%] w-[800px] h-[800px] bg-violet-600/5 rounded-full blur-[120px] pointer-events-none" />
        
        <div className="p-8 max-w-7xl mx-auto relative z-10 min-h-full">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default Layout;
