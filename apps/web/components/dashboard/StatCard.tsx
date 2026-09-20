type StatCardProps = {
  label: string;
  value: string;
  change: string;
  description: string;
};

export default function StatCard({
  label,
  value,
  change,
  description,
}: StatCardProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-sm font-medium text-slate-500">{label}</p>

      <div className="mt-3 flex items-end justify-between gap-3">
        <p className="text-2xl font-bold tracking-tight text-slate-950">
          {value}
        </p>

        <span className="text-xs font-semibold text-emerald-600">{change}</span>
      </div>

      <p className="mt-2 text-xs text-slate-400">{description}</p>
    </div>
  );
}
