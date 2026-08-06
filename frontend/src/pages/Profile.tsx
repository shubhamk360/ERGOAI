import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { User as UserIcon, Shield, Activity, Calendar, Award, Check, Edit2, Camera, X } from 'lucide-react';
import api from '../services/api';

const Profile = () => {
  const { user } = useAuth();
  
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [formData, setFormData] = useState({
    username: user?.username || '',
    bio: 'Ergonomics enthusiast focused on building better daily habits.',
    company: 'Independent'
  });

  const handleSave = () => {
    setIsSaving(true);
    // Simulate API call since we don't have a PUT /users route
    setTimeout(() => {
      setIsSaving(false);
      setIsEditing(false);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
      // In a real app we'd update AuthContext user here
    }, 800);
  };

  return (
    <div className="space-y-6 max-w-4xl pb-12">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">Profile</h1>
          <p className="text-slate-400 mt-1">Manage your identity and public details.</p>
        </div>
        
        {saveSuccess && (
          <div className="flex items-center space-x-2 text-emerald-400 bg-emerald-500/10 px-4 py-2 rounded-full border border-emerald-500/20 animate-fade-in text-sm font-medium">
            <Check className="w-4 h-4" />
            <span>Profile updated</span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Left Column: Avatar & Quick Stats */}
        <div className="space-y-6">
          <div className="glass-panel p-6 flex flex-col items-center text-center relative overflow-hidden">
            {/* Background Accent */}
            <div className="absolute -top-12 -right-12 w-32 h-32 bg-violet-500/20 rounded-full blur-3xl"></div>
            
            <div className="relative group mb-4">
              <div className="w-28 h-28 bg-gradient-to-tr from-violet-600 to-indigo-500 rounded-full flex items-center justify-center shadow-xl shadow-violet-500/20 relative z-10 border-4 border-slate-900">
                <UserIcon className="w-12 h-12 text-white" />
              </div>
              {isEditing && (
                <button className="absolute bottom-0 right-0 bg-slate-800 border border-slate-700 p-2 rounded-full z-20 hover:bg-slate-700 transition-colors shadow-lg">
                  <Camera className="w-4 h-4 text-slate-300" />
                </button>
              )}
            </div>
            
            <h2 className="text-xl font-bold text-white mb-1">
              {isEditing ? formData.username : (user?.username || 'User')}
            </h2>
            <div className="flex items-center space-x-2 text-violet-400 font-medium text-sm mb-4">
              <Shield className="w-4 h-4" />
              <span>Standard Member</span>
            </div>
            
            <p className="text-sm text-slate-400 leading-relaxed">
              {formData.bio}
            </p>
          </div>

          <div className="glass-panel p-6 space-y-4">
            <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">Account Stats</h3>
            
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3 text-slate-400">
                <Calendar className="w-5 h-5 text-slate-500" />
                <span className="text-sm">Joined</span>
              </div>
              <span className="text-sm font-medium text-white">August 2026</span>
            </div>
            
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3 text-slate-400">
                <Activity className="w-5 h-5 text-emerald-500" />
                <span className="text-sm">Total Sessions</span>
              </div>
              <span className="text-sm font-medium text-white">--</span>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3 text-slate-400">
                <Award className="w-5 h-5 text-amber-500" />
                <span className="text-sm">Ergo Score</span>
              </div>
              <span className="text-sm font-medium text-white">TBD</span>
            </div>
          </div>
        </div>

        {/* Right Column: Details & Edit Form */}
        <div className="md:col-span-2">
          <div className="glass-panel p-8 relative">
            
            <div className="flex justify-between items-center mb-8 border-b border-slate-800 pb-4">
              <h3 className="text-xl font-bold text-white">Personal Information</h3>
              {!isEditing ? (
                <button 
                  onClick={() => setIsEditing(true)}
                  className="flex items-center space-x-2 text-sm font-medium text-violet-400 hover:text-violet-300 transition-colors bg-violet-500/10 hover:bg-violet-500/20 px-3 py-1.5 rounded-lg"
                >
                  <Edit2 className="w-4 h-4" />
                  <span>Edit Profile</span>
                </button>
              ) : (
                <button 
                  onClick={() => setIsEditing(false)}
                  className="flex items-center space-x-1 text-sm font-medium text-slate-400 hover:text-slate-300 transition-colors"
                >
                  <X className="w-4 h-4" />
                  <span>Cancel</span>
                </button>
              )}
            </div>

            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-slate-400 mb-2">
                    Username
                  </label>
                  {isEditing ? (
                    <input 
                      type="text" 
                      value={formData.username}
                      onChange={(e) => setFormData({...formData, username: e.target.value})}
                      className="input-field w-full"
                    />
                  ) : (
                    <div className="px-4 py-3 bg-slate-900/50 border border-slate-800 rounded-xl text-white font-medium">
                      {user?.username}
                    </div>
                  )}
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-slate-400 mb-2">
                    User ID (Read-only)
                  </label>
                  <div className="px-4 py-3 bg-slate-900/30 border border-slate-800/50 rounded-xl text-slate-500 font-mono text-sm cursor-not-allowed">
                    #{user?.id}
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-400 mb-2">
                  Organization / Company
                </label>
                {isEditing ? (
                  <input 
                    type="text" 
                    value={formData.company}
                    onChange={(e) => setFormData({...formData, company: e.target.value})}
                    className="input-field w-full"
                  />
                ) : (
                  <div className="px-4 py-3 bg-slate-900/50 border border-slate-800 rounded-xl text-slate-300">
                    {formData.company}
                  </div>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-400 mb-2">
                  Bio
                </label>
                {isEditing ? (
                  <textarea 
                    rows={4}
                    value={formData.bio}
                    onChange={(e) => setFormData({...formData, bio: e.target.value})}
                    className="input-field w-full resize-none"
                  />
                ) : (
                  <div className="px-4 py-3 bg-slate-900/50 border border-slate-800 rounded-xl text-slate-300 min-h-[100px]">
                    {formData.bio}
                  </div>
                )}
              </div>

              {isEditing && (
                <div className="pt-6 border-t border-slate-800 flex justify-end">
                  <button 
                    onClick={handleSave}
                    disabled={isSaving}
                    className="btn-primary w-full md:w-auto min-w-[120px]"
                  >
                    {isSaving ? 'Saving...' : 'Save Changes'}
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;
