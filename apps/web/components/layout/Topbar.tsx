export default function Topbar() {
  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-slate-200 bg-white/95 px-6 backdrop-blur lg:px-8">
      <div>
        <p className="text-sm font-medium text-slate-500">
          Restaurant Operations
        </p>
      </div>

      <div className="flex items-center gap-4">
        <div className="hidden text-right sm:block">
          <p className="text-sm font-medium text-slate-900">Admin</p>
          <p className="text-xs text-slate-500">Restaurant Manager</p>
        </div>

        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-900 text-sm font-semibold text-white">
          A
        </div>
      </div>
    </header>
  );
}
