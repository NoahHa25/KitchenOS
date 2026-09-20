import Link from "next/link";

const navigation = [
  { name: "Dashboard", href: "/dashboard" },
  { name: "Orders", href: "/orders" },
  { name: "Inventory", href: "/inventory" },
  { name: "Recipes", href: "/recipes" },
  { name: "Food Cost", href: "/food-cost" },
  { name: "Analytics", href: "/analytics" },
  { name: "Settings", href: "/settings" },
];

export default function Sidebar() {
  return (
    <aside className="fixed inset-y-0 left-0 z-40 hidden w-64 border-r border-slate-200 bg-white lg:flex lg:flex-col">
      <div className="flex h-16 items-center border-b border-slate-200 px-6">
        <Link href="/dashboard" className="text-xl font-bold tracking-tight">
          KitchenOS
        </Link>
      </div>

      <nav className="flex-1 space-y-1 p-4">
        {navigation.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className="block rounded-lg px-4 py-3 text-sm font-medium text-slate-600 transition hover:bg-slate-100 hover:text-slate-950"
          >
            {item.name}
          </Link>
        ))}
      </nav>

      <div className="border-t border-slate-200 p-4">
        <div className="rounded-lg bg-slate-50 px-4 py-3">
          <p className="text-sm font-medium text-slate-900">Restaurant</p>
          <p className="mt-1 text-xs text-slate-500">KitchenOS</p>
        </div>
      </div>
    </aside>
  );
}
