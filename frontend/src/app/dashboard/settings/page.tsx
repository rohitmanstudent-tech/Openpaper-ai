"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { api, getToken, getStoredUser, storeUser } from "@/lib/api";
import { Settings as SettingsIcon, User, Shield, Bell, Key, Palette, Cpu } from "lucide-react";

export default function SettingsPage() {
  const [user, setUser] = useState<any>(null);
  const [ollamaModels, setOllamaModels] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [fullName, setFullName] = useState("");
  const token = getToken();

  useEffect(() => {
    if (!token) return;
    const stored = getStoredUser();
    setUser(stored);
    setFullName(stored?.full_name || "");
    api.get<{ models: { name: string }[] }>("/ollama/models", token)
      .then((data) => setOllamaModels(data.models.map((m) => m.name)))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleUpdate = async () => {
    if (!token) return;
    try {
      const updated = await api.put<any>("/users/me", { full_name: fullName }, token);
      storeUser(updated);
      setUser(updated);
    } catch {}
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="h-5 w-5 animate-spin rounded-full border border-accent-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-xl font-semibold text-base-100">Settings</h1>
        <p className="mt-0.5 text-sm text-base-400">Manage your account and preferences</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          {/* Profile */}
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-4">
              <User size={15} className="text-accent-400" />
              <h2 className="text-sm font-semibold text-base-100">Profile</h2>
            </div>
            <div className="space-y-3">
              <Input label="Email" value={user?.email || ""} disabled />
              <Input label="Username" value={user?.username || ""} disabled />
              <div className="flex items-end gap-3">
                <div className="flex-1">
                  <Input label="Full Name" value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="Your full name" />
                </div>
                <Button className="mb-0.5" onClick={handleUpdate}>Save</Button>
              </div>
              <div className="flex items-center gap-2 pt-2">
                <Shield size={14} className="text-base-500" />
                <span className="text-xs text-base-500">Role:</span>
                <Badge variant={user?.role as any}>{user?.role || "member"}</Badge>
              </div>
            </div>
          </Card>

          {/* Notifications */}
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-4">
              <Bell size={15} className="text-accent-400" />
              <h2 className="text-sm font-semibold text-base-100">Notifications</h2>
            </div>
            <div className="space-y-3">
              {[
                { label: "Agent status changes", desc: "When agents start or stop working" },
                { label: "Task completions", desc: "When a task is marked as done" },
                { label: "Provider errors", desc: "When an AI provider fails" },
                { label: "Weekly digest", desc: "Summary of agent activity each week" },
              ].map((n) => (
                <div key={n.label} className="flex items-center justify-between py-1.5">
                  <div>
                    <p className="text-sm text-base-200">{n.label}</p>
                    <p className="text-xs text-base-500">{n.desc}</p>
                  </div>
                  <label className="relative inline-flex h-5 w-9 cursor-pointer items-center">
                    <input type="checkbox" defaultChecked className="peer sr-only" />
                    <div className="h-5 w-9 rounded-full bg-base-700 after:absolute after:left-[2px] after:top-[2px] after:h-4 after:w-4 after:rounded-full after:bg-base-400 after:transition-all peer-checked:bg-accent-500/30 peer-checked:after:bg-accent-400 peer-checked:after:translate-x-4" />
                  </label>
                </div>
              ))}
            </div>
          </Card>
        </div>

        <div className="space-y-6">
          {/* API Keys */}
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-4">
              <Key size={15} className="text-accent-400" />
              <h2 className="text-sm font-semibold text-base-100">API Keys</h2>
            </div>
            <div className="space-y-2 text-xs text-base-500">
              <p>Manage your provider API keys in the configuration file or CLI.</p>
              <code className="block rounded bg-base-800 px-2 py-1.5 text-[11px] text-base-400">
                openpaper configure --key OPENAI_API_KEY --value sk-...
              </code>
            </div>
          </Card>

          {/* Ollama */}
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-4">
              <Cpu size={15} className="text-accent-400" />
              <h2 className="text-sm font-semibold text-base-100">Local Models</h2>
            </div>
            {ollamaModels.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {ollamaModels.map((model) => (
                  <Badge key={model} variant="idle">{model}</Badge>
                ))}
              </div>
            ) : (
              <div className="text-xs text-base-500 space-y-1">
                <p>No local models detected.</p>
                <p className="text-base-600">Run: ollama pull llama3.1</p>
              </div>
            )}
          </Card>

          {/* Theme */}
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-4">
              <Palette size={15} className="text-accent-400" />
              <h2 className="text-sm font-semibold text-base-100">Appearance</h2>
            </div>
            <div className="text-xs text-base-500">
              <div className="flex items-center justify-between py-1.5">
                <span>Theme</span>
                <Badge variant="idle">Dark</Badge>
              </div>
              <div className="flex items-center justify-between py-1.5">
                <span>Sidebar</span>
                <Badge variant="idle">Expanded</Badge>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
