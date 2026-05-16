'use client';
import { useState } from 'react';
import Sidebar from '@/components/Sidebar';
import { Sparkles } from 'lucide-react';

export default function LoginPage() {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 flex items-center justify-center p-6">
        <div className="card w-full max-w-md">
          <div className="flex items-center gap-2 mb-6">
            <Sparkles className="w-6 h-6 text-brand-400" />
            <h1 className="text-xl font-bold text-white">
              {mode === 'login' ? 'تسجيل الدخول' : 'إنشاء حساب'}
            </h1>
          </div>

          <form className="space-y-3" onSubmit={(e) => e.preventDefault()}>
            {mode === 'register' && (
              <div>
                <label className="label">الاسم الكامل</label>
                <input type="text" className="w-full bg-bg-panel border border-bg-border rounded-xl px-3 py-2" />
              </div>
            )}
            <div>
              <label className="label">البريد الإلكتروني</label>
              <input type="email" className="w-full bg-bg-panel border border-bg-border rounded-xl px-3 py-2" />
            </div>
            <div>
              <label className="label">كلمة المرور</label>
              <input type="password" className="w-full bg-bg-panel border border-bg-border rounded-xl px-3 py-2" />
            </div>
            <button type="submit" className="btn-primary w-full">
              {mode === 'login' ? 'تسجيل الدخول' : 'إنشاء الحساب'}
            </button>
          </form>

          <button
            onClick={() => setMode(mode === 'login' ? 'register' : 'login')}
            className="w-full text-center text-sm text-brand-300 mt-4 hover:underline"
          >
            {mode === 'login' ? 'ليس لديك حساب؟ إنشاء حساب' : 'لديك حساب؟ تسجيل الدخول'}
          </button>
        </div>
      </main>
    </div>
  );
}
