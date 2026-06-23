"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Store, Download, Star, Search, Grid3X3, List, ArrowUpRight, Check, Bot, Workflow, Cpu, BookOpen } from "lucide-react";
import { cn } from "@/lib/utils";

interface Listing {
  id: number; name: string; description: string; type: "agent" | "workflow" | "plugin" | "knowledge";
  author: string; rating: number; downloads: number; price: string; tags: string[];
}

const listings: Listing[] = [
  { id: 1, name: "Market Research Pro", description: "Advanced market analysis agent with real-time data gathering, competitor tracking, and report generation.", type: "agent", author: "OpenPaper Labs", rating: 4.8, downloads: 1240, price: "Free", tags: ["research", "analysis"] },
  { id: 2, name: "Lead Gen Pipeline", description: "End-to-end lead qualification workflow from discovery to CRM integration.", type: "workflow", author: "GrowthStack", rating: 4.6, downloads: 892, price: "$49", tags: ["sales", "leads"] },
  { id: 3, name: "Code Review Assistant", description: "Automated code review plugin supporting 12 languages with security scanning.", type: "plugin", author: "DevTools Inc", rating: 4.9, downloads: 2103, price: "$29/mo", tags: ["code", "review"] },
  { id: 4, name: "Industry Reports Bundle", description: "Curated knowledge base of 500+ industry reports across 20 sectors.", type: "knowledge", author: "DataVault", rating: 4.5, downloads: 567, price: "$99", tags: ["reports", "data"] },
  { id: 5, name: "Customer Support Agent", description: "Multi-channel support agent with ticket management and sentiment analysis.", type: "agent", author: "SupportAI", rating: 4.7, downloads: 1567, price: "Free", tags: ["support", "customer"] },
  { id: 6, name: "SEO Optimization Suite", description: "Complete SEO workflow: keyword research, content optimization, and rank tracking.", type: "workflow", author: "SEO Masters", rating: 4.4, downloads: 723, price: "$79", tags: ["seo", "marketing"] },
  { id: 7, name: "Database Query Plugin", description: "Natural language to SQL query plugin supporting PostgreSQL, MySQL, and BigQuery.", type: "plugin", author: "DataQuery", rating: 4.3, downloads: 445, price: "$19/mo", tags: ["sql", "database"] },
  { id: 8, name: "Competitor Intel Pack", description: "Structured knowledge base of competitive intelligence frameworks and templates.", type: "knowledge", author: "MarketIntel", rating: 4.6, downloads: 334, price: "$39", tags: ["competitive", "intel"] },
];

const typeIcons: Record<string, any> = { agent: Bot, workflow: Workflow, plugin: Cpu, knowledge: BookOpen };
const categories = ["All", "Agents", "Workflows", "Plugins", "Knowledge"];

export default function MarketplacePage() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All");
  const [installed, setInstalled] = useState<number[]>([1]);

  const filtered = listings.filter(l => {
    if (category !== "All") {
      const catMap: Record<string, string> = { Agents: "agent", Workflows: "workflow", Plugins: "plugin", Knowledge: "knowledge" };
      if (l.type !== catMap[category]) return false;
    }
    if (search && !l.name.toLowerCase().includes(search.toLowerCase()) && !l.description.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-base-100">Marketplace</h1>
          <p className="mt-0.5 text-sm text-base-400">Discover agents, workflows, plugins, and knowledge packs</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-xs">
          <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-base-500" />
          <input value={search} onChange={(e) => setSearch(e.target.value)}
            placeholder="Search marketplace..."
            className="w-full rounded-md border border-base-700/50 bg-base-900 py-1.5 pl-8 pr-3 text-sm text-base-100 placeholder-base-500 outline-none focus:border-accent-500/50" />
        </div>
        <div className="flex items-center gap-1 rounded-md border border-base-700/50 p-0.5">
          {categories.map((cat) => (
            <button key={cat} onClick={() => setCategory(cat)}
              className={cn("rounded px-2.5 py-1 text-xs transition-colors", category === cat ? "bg-base-700 text-base-200" : "text-base-500 hover:text-base-300")}>
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Grid */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {filtered.map((item) => {
          const Icon = typeIcons[item.type] || Bot;
          const isInstalled = installed.includes(item.id);
          return (
            <Card key={item.id} className="p-4 card-hover flex flex-col">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-base-800">
                    <Icon size={16} className="text-base-300" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-base-100">{item.name}</p>
                    <p className="text-[11px] text-base-500">{item.author}</p>
                  </div>
                </div>
                <Badge variant="idle" className="text-[10px]">{item.type}</Badge>
              </div>
              <p className="text-xs text-base-400 leading-relaxed line-clamp-2 flex-1">{item.description}</p>
              <div className="mt-3 flex items-center gap-2">
                {item.tags.map((tag) => (
                  <span key={tag} className="rounded bg-base-800 px-1.5 py-0.5 text-[10px] text-base-500">{tag}</span>
                ))}
              </div>
              <div className="mt-3 flex items-center justify-between pt-3 border-t border-base-700/30">
                <div className="flex items-center gap-3 text-[11px] text-base-500">
                  <span className="flex items-center gap-1"><Star size={10} className="text-amber-400" />{item.rating}</span>
                  <span>{item.downloads.toLocaleString()} downloads</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium text-base-300">{item.price}</span>
                  {isInstalled ? (
                    <span className="flex items-center gap-1 rounded-md bg-emerald-500/10 px-2 py-1 text-[11px] text-emerald-400">
                      <Check size={10} /> Installed
                    </span>
                  ) : (
                    <button className="flex items-center gap-1 rounded-md bg-base-800 px-2 py-1 text-[11px] text-base-300 transition-colors hover:bg-base-700">
                      <Download size={10} /> Install
                    </button>
                  )}
                </div>
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
