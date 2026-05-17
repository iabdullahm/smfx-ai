'use client';
import Link from 'next/link';
import Sidebar from '@/components/Sidebar';
import { XCircle, ArrowRight } from 'lucide-react';

export default function PaymentCancelPage() {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 flex items-center justify-center p-6">
        <div className="card max-w-md w-full text-center">
          <XCircle className="w-16 h-16 text-rose-400 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-white mb-2">تم إلغاء الدفع</h1>
          <p className="text-gray-400 mb-6">
            لم يتم خصم أي مبلغ. يمكنك المحاولة مرة أخرى في أي وقت.
          </p>
          <div className="flex gap-2">
            <Link href="/subscriptions" className="btn-primary flex-1">
              المحاولة مرة أخرى
            </Link>
            <Link href="/" className="btn-ghost flex-1">
              الصفحة الرئيسية <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
