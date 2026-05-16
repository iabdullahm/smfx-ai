'use client';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

type Candle = { time: string; open: number; high: number; low: number; close: number };

export default function PriceChart({
  data, entry, sl, tp1, tp2, tp3,
}: { data: Candle[]; entry?: number; sl?: number; tp1?: number; tp2?: number; tp3?: number }) {
  const series = data.map((c) => ({
    time: new Date(c.time).toLocaleTimeString('ar-EG', { hour: '2-digit', minute: '2-digit' }),
    close: c.close,
  }));
  return (
    <div className="card">
      <h3 className="font-bold text-white mb-4">حركة السعر (آخر {data.length} شمعة)</h3>
      <div className="h-72">
        <ResponsiveContainer>
          <LineChart data={series}>
            <XAxis dataKey="time" stroke="#6B7280" fontSize={11} interval="preserveStartEnd" />
            <YAxis stroke="#6B7280" fontSize={11} domain={['auto', 'auto']} orientation="right" />
            <Tooltip
              contentStyle={{ background: '#121826', border: '1px solid #232C44', borderRadius: 8 }}
              labelStyle={{ color: '#9CA3AF' }}
            />
            <Line type="monotone" dataKey="close" stroke="#E8A21F" strokeWidth={2} dot={false} />
            {entry !== undefined && <ReferenceLine y={entry} stroke="#60A5FA" strokeDasharray="3 3" label={{ value: 'الدخول', fill: '#60A5FA', fontSize: 11 }} />}
            {sl !== undefined &&    <ReferenceLine y={sl}    stroke="#F87171" strokeDasharray="3 3" label={{ value: 'SL', fill: '#F87171', fontSize: 11 }} />}
            {tp1 !== undefined &&   <ReferenceLine y={tp1}   stroke="#34D399" strokeDasharray="3 3" label={{ value: 'TP1', fill: '#34D399', fontSize: 11 }} />}
            {tp2 !== undefined &&   <ReferenceLine y={tp2}   stroke="#34D399" strokeDasharray="3 3" label={{ value: 'TP2', fill: '#34D399', fontSize: 11 }} />}
            {tp3 !== undefined &&   <ReferenceLine y={tp3}   stroke="#34D399" strokeDasharray="3 3" label={{ value: 'TP3', fill: '#34D399', fontSize: 11 }} />}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
