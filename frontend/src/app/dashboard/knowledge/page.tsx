"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Library, Search, Plus, FileText, FolderOpen, BookOpen, Link2, Upload, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface KnowledgeItem {
  id: number; title: string; type: "document" | "link" | "note" | "dataset";
  category: string; tags: string[]; updated_at: string; size: string;
}

const items: KnowledgeItem[] = [
  { id: 1, title: "Company Product Specs v4", type: "document", category: "Products", tags: ["specs", "internal"], updated_at: "1h ago", size: "2.4 MB" },
  { id: 2, title: "Market Research Q3 2026", type: "document", category: "Research", tags: ["market", "competitors"], updated_at: "3h ago", size: "4.1 MB" },
  { id: 3, title: "API Integration Guide", type: "link", category: "Engineering", tags: ["api", "docs"], updated_at: "5h ago", size: "Link" },
  { id: 4, title: "Customer Interview Notes", type: "note", category: "Sales", tags: ["customers", "feedback"], updated_at: "1d ago", size: "12 KB" },
  { id: 5, title: "Training Data v2", type: "dataset", category: "AI", tags: ["training", "models"], updated_at: "2d ago", size: "156 MB" },
  { id: 6, title: "Competitor Pricing Sheet", type: "document", category: "Sales", tags: ["pricing", "competitors"], updated_at: "2d ago", size: "890 KB" },
];

const typeIcons: Record<string, any> = {
  document: FileText, link: Link2, note: BookOpen, dataset: FolderOpen,
};

const categories = ["All", "Products", "Research", "Engineering", "Sales", "AI"];

export default function KnowledgePage() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All");

  const filtered = items.filter(i => {
    if (category !== "All" && i.category !== category) return false;
    if (search && !i.title.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-base-100">Knowledge Base</h1>
          <p className="mt-0.5 text-sm text-base-400">Store and organize your team's collective intelligence</p>
        </div>
        <Button>
          <Upload size={15} className="mr-1.5" />
          Upload
        </Button>
      </div>

      {/* Search & filter */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-md">
          <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-base-500" />
          <input value={search} onChange={(e) => setSearch(e.target.value)}
            placeholder="Search knowledge base..."
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

      {/* Items grid */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {filtered.map((item) => {
          const Icon = typeIcons[item.type] || FileText;
          return (
            <Card key={item.id} className="p-4 card-hover group">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-base-800">
                    <Icon size={16} className="text-base-300" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-base-100">{item.title}</p>
                    <p className="text-[11px] text-base-500 capitalize">{item.type} · {item.category}</p>
                  </div>
                </div>
              </div>
              <div className="mt-3 flex items-center gap-2">
                {item.tags.map((tag) => (
                  <span key={tag} className="rounded bg-base-800 px-1.5 py-0.5 text-[10px] text-base-500">#{tag}</span>
                ))}
              </div>
              <div className="mt-3 flex items-center justify-between text-[11px] text-base-500 pt-3 border-t border-base-700/30">
                <span>{item.size}</span>
                <span>{item.updated_at}</span>
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
