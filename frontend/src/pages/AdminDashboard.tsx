import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { ChartBarIcon, ArrowPathIcon, UsersIcon, FilmIcon, StarIcon, WrenchIcon } from '@heroicons/react/24/solid';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';
import toast from 'react-hot-toast';

export const AdminDashboard: React.FC = () => {
  const [stats, setStats] = useState<any>(null);
  const [genreDist, setGenreDist] = useState<any[]>([]);
  const [retrainStatus, setRetrainStatus] = useState<any>(null);
  const [users, setUsers] = useState<any[]>([]);

  const fetchAdminData = async () => {
    try {
      const [s, g, u] = await Promise.all([
        api.get('/analytics/dashboard').then((r) => r.data),
        api.get('/analytics/genre-distribution').then((r) => r.data),
        api.get('/admin/users').then((r) => r.data.items),
      ]);
      setStats(s);
      setGenreDist(g);
      setUsers(u);
    } catch {
      toast.error('Failed to load admin data');
    }
  };

  useEffect(() => {
    fetchAdminData();
  }, []);

  const handleRetrain = async () => {
    try {
      const { data } = await api.post('/admin/retrain');
      toast.success(data.message);
      checkRetrainStatus();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Retrain trigger failed');
    }
  };

  const checkRetrainStatus = async () => {
    try {
      const { data } = await api.get('/admin/retrain/status');
      setRetrainStatus(data);
    } catch {}
  };

  const toggleUserActive = async (userId: number) => {
    try {
      await api.put(`/admin/users/${userId}/toggle-active`);
      toast.success('User status updated');
      fetchAdminData();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Update failed');
    }
  };

  const handleSyncTMDB = async () => {
    try {
      const { data } = await api.post('/admin/sync-tmdb?pages=3');
      toast.success(data.message);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'TMDB Sync trigger failed');
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-black text-white font-['Outfit'] flex items-center gap-2">
            <ChartBarIcon className="w-8 h-8 text-[var(--color-primary-light)]" />
            Admin & Analytics Command Center
          </h1>
          <p className="text-gray-400 text-sm">System performance, analytics, user management, and ML pipeline control</p>
        </div>

        <div className="flex flex-wrap gap-2">
          <button onClick={handleSyncTMDB} className="btn-secondary text-xs py-2 px-4">
            <ArrowPathIcon className="w-4 h-4 text-amber-400" /> Multi-Industry TMDB Sync
          </button>

          <button onClick={handleRetrain} className="btn-primary text-xs py-2 px-4">
            <ArrowPathIcon className="w-4 h-4" /> Trigger ML Pipeline Retrain
          </button>
        </div>
      </div>

      {retrainStatus && (
        <div className="p-4 rounded-xl bg-purple-950/40 border border-purple-800 text-xs text-purple-200">
          Retrain Status: <strong className="uppercase">{retrainStatus.status}</strong> — {retrainStatus.message}
        </div>
      )}

      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="card p-5 space-y-2">
            <div className="flex justify-between text-gray-400 text-xs uppercase font-bold">
              <span>Total Movies</span>
              <FilmIcon className="w-4 h-4 text-blue-400" />
            </div>
            <div className="text-3xl font-black text-white font-['Outfit']">{stats.total_movies}</div>
          </div>
          <div className="card p-5 space-y-2">
            <div className="flex justify-between text-gray-400 text-xs uppercase font-bold">
              <span>Total Users</span>
              <UsersIcon className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-3xl font-black text-white font-['Outfit']">{stats.total_users}</div>
          </div>
          <div className="card p-5 space-y-2">
            <div className="flex justify-between text-gray-400 text-xs uppercase font-bold">
              <span>Total Ratings</span>
              <StarIcon className="w-4 h-4 text-[var(--color-accent)]" />
            </div>
            <div className="text-3xl font-black text-white font-['Outfit']">{stats.total_ratings}</div>
          </div>
          <div className="card p-5 space-y-2">
            <div className="flex justify-between text-gray-400 text-xs uppercase font-bold">
              <span>Total Searches</span>
              <WrenchIcon className="w-4 h-4 text-purple-400" />
            </div>
            <div className="text-3xl font-black text-white font-['Outfit']">{stats.total_searches}</div>
          </div>
        </div>
      )}

      <div className="card p-6 space-y-4">
        <h2 className="font-bold text-white text-lg font-['Outfit']">Database Genre Distribution</h2>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={genreDist}>
              <XAxis dataKey="genre" stroke="#9090a8" fontSize={11} />
              <YAxis stroke="#9090a8" fontSize={11} />
              <Tooltip />
              <Bar dataKey="count" fill="#e50914" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card p-6 space-y-4 overflow-x-auto">
        <h2 className="font-bold text-white text-lg font-['Outfit']">User Account Management</h2>
        <table className="w-full text-left text-sm border-collapse">
          <thead>
            <tr className="border-b border-[var(--color-border)] text-xs text-gray-400 uppercase">
              <th className="py-2">ID</th>
              <th className="py-2">User</th>
              <th className="py-2">Email</th>
              <th className="py-2">Role</th>
              <th className="py-2">Status</th>
              <th className="py-2 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                <td className="py-3 font-mono text-xs">{u.id}</td>
                <td className="py-3 font-semibold text-white">{u.username}</td>
                <td className="py-3 text-gray-400">{u.email}</td>
                <td className="py-3">
                  <span className={`text-[10px] px-2 py-0.5 rounded font-bold ${u.is_admin ? 'bg-red-950 text-red-400' : 'bg-gray-800 text-gray-400'}`}>
                    {u.is_admin ? 'ADMIN' : 'USER'}
                  </span>
                </td>
                <td className="py-3">
                  <span className={`text-[10px] px-2 py-0.5 rounded font-bold ${u.is_active ? 'bg-emerald-950 text-emerald-400' : 'bg-red-950 text-red-400'}`}>
                    {u.is_active ? 'ACTIVE' : 'INACTIVE'}
                  </span>
                </td>
                <td className="py-3 text-right">
                  <button
                    onClick={() => toggleUserActive(u.id)}
                    className="text-xs px-2.5 py-1 rounded bg-[var(--color-surface-2)] text-gray-300 hover:text-white border border-[var(--color-border)]"
                  >
                    Toggle Active
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
