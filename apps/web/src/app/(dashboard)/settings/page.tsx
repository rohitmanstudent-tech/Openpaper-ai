"use client"

import { useState } from "react"
import { useAuthStore } from "@/stores/auth"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useRouter } from "next/navigation"
import { LogOut, User, Shield, Calendar, Key, Eye, EyeOff } from "lucide-react"

export default function SettingsPage() {
  const { user, logout } = useAuthStore()
  const router = useRouter()
  const [showApiKey, setShowApiKey] = useState(false)
  const [apiKeys, setApiKeys] = useState<Record<string, string>>({
    openai: "",
    claude: "",
    openrouter: "",
  })

  const handleLogout = () => {
    logout()
    router.push("/login")
  }

  const handleSaveKey = (provider: string) => {
    localStorage.setItem(`${provider}_api_key`, apiKeys[provider])
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="text-muted-foreground text-sm mt-1">Manage your account and API keys</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-5 w-5 text-accent-400" /> Profile
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-muted-foreground">Username</p>
              <p className="text-white font-medium">{user?.username || "-"}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Email</p>
              <p className="text-white font-medium">{user?.email || "-"}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Full Name</p>
              <p className="text-white font-medium">{user?.full_name || "-"}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Role</p>
              <p className="text-white font-medium capitalize">{user?.role || "-"}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Key className="h-5 w-5 text-accent-400" /> API Keys
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">Configure API keys for LLM providers. Keys are stored locally.</p>
          {["openai", "claude", "openrouter"].map((provider) => (
            <div key={provider} className="flex items-end gap-2">
              <div className="flex-1 space-y-1">
                <Label className="capitalize">{provider}</Label>
                <div className="relative">
                  <Input
                    type={showApiKey ? "text" : "password"}
                    value={apiKeys[provider]}
                    onChange={(e) => setApiKeys({ ...apiKeys, [provider]: e.target.value })}
                    placeholder={`sk-... (${provider} API key)`}
                    className="pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowApiKey(!showApiKey)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  >
                    {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
              <Button variant="outline" size="sm" onClick={() => handleSaveKey(provider)}>Save</Button>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-accent-400" /> Security
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Button variant="destructive" onClick={handleLogout}>
            <LogOut className="h-4 w-4 mr-2" /> Sign Out
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5 text-accent-400" /> Account Info
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-muted-foreground">
            <p>Member since {user?.created_at ? new Date(user.created_at).toLocaleDateString() : "-"}</p>
            <p className="mt-1">Account ID: {user?.id}</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
