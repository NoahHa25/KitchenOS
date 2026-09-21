import Sidebar from "@/components/layout/Sidebar";
import Topbar from "@/components/layout/Topbar";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar />

      <div className="lg:ps-64">
        <Topbar />

        <main className="min-h-[calc(100vh-4rem)] p-6 lg:p-8">{children}</main>
      </div>
    </div>
  );
}
