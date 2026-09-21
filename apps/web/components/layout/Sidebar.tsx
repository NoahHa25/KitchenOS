"use client";

import { useTranslations } from "next-intl";

import { Link, usePathname } from "@/i18n/navigation";

const navigation = [
  { key: "dashboard", href: "/dashboard" },
  { key: "orders", href: "/orders" },
  { key: "inventory", href: "/inventory" },
  { key: "recipes", href: "/recipes" },
  { key: "foodCost", href: "/food-cost" },
  { key: "analytics", href: "/analytics" },
  { key: "settings", href: "/settings" },
] as const;

export default function Sidebar() {
  const t = useTranslations("navigation");
  const pathname = usePathname();

  return (
    <aside className="fixed inset-y-0 start-0 z-40 hidden w-64 border-e border-slate-200 bg-white lg:flex lg:flex-col">
      <div className="flex h-16 items-center border-b border-slate-200 px-6">
        <Link href="/dashboard" className="text-xl font-bold tracking-tight">
          KitchenOS
        </Link>
      </div>

      <nav className="flex-1 space-y-1 p-4">
        {navigation.map((item) => {
          const isActive =
            pathname === item.href || pathname.startsWith(`${item.href}/`);

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`block rounded-lg px-4 py-3 text-sm font-medium transition ${
                isActive
                  ? "bg-slate-100 text-slate-950"
                  : "text-slate-600 hover:bg-slate-100 hover:text-slate-950"
              }`}
            >
              {t(item.key)}
            </Link>
          );
        })}
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
