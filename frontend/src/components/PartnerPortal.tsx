'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Key, Webhook, BarChart3, Settings, Copy, Check, Plus, Trash2, Download, RefreshCw } from 'lucide-react'

interface APIKey {
  id: string
  name: string
  key: string
  created: string
  lastUsed: string
  permissions: string[]
}

interface WebhookConfig {
  id: string
  url: string
  events: string[]
  status: string
  created: string
  lastTriggered: string
}

export function PartnerPortal() {
  const [apiKeys, setApiKeys] = useState<APIKey[]>([
    { id: '1', name: 'Production API Key', key: 'ak_prod_xxxxxxxxxxxxxxxxxxxx', created: '2024-01-15', lastUsed: '2024-01-20', permissions: ['read', 'write'] },
    { id: '2', name: 'Test API Key', key: 'ak_test_yyyyyyyyyyyyyyyyyyyy', created: '2024-01-10', lastUsed: '2024-01-18', permissions: ['read'] },
  ])
  
  const [webhooks, setWebhooks] = useState<WebhookConfig[]>([
    { id: '1', url: 'https://example.com/webhook', events: ['case.created', 'case.updated'], status: 'active', created: '2024-01-12', lastTriggered: '2024-01-19' },
  ])
  
  const [copiedKey, setCopiedKey] = useState<string | null>(null)
  const [showCreateKey, setShowCreateKey] = useState(false)
  const [showCreateWebhook, setShowCreateWebhook] = useState(false)

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopiedKey(text)
    setTimeout(() => setCopiedKey(null), 2000)
  }

  const createNewKey = () => {
    const newKey: APIKey = {
      id: Date.now().toString(),
      name: 'New API Key',
      key: `ak_new_${Math.random().toString(36).substring(2, 15)}`,
      created: new Date().toISOString().split('T')[0],
      lastUsed: 'Never',
      permissions: ['read']
    }
    setApiKeys([...apiKeys, newKey])
    setShowCreateKey(false)
  }

  const deleteKey = (id: string) => {
    setApiKeys(apiKeys.filter(k => k.id !== id))
  }

  const createWebhook = () => {
    const newWebhook: WebhookConfig = {
      id: Date.now().toString(),
      url: 'https://example.com/new-webhook',
      events: ['case.created'],
      status: 'active',
      created: new Date().toISOString().split('T')[0],
      lastTriggered: 'Never'
    }
    setWebhooks([...webhooks, newWebhook])
    setShowCreateWebhook(false)
  }

  const deleteWebhook = (id: string) => {
    setWebhooks(webhooks.filter(w => w.id !== id))
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Partner Portal</CardTitle>
        <CardDescription>Manage your API keys, webhooks, and integration settings</CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="api-keys" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="api-keys">
              <Key className="h-4 w-4 mr-2" />
              API Keys
            </TabsTrigger>
            <TabsTrigger value="webhooks">
              <Webhook className="h-4 w-4 mr-2" />
              Webhooks
            </TabsTrigger>
            <TabsTrigger value="analytics">
              <BarChart3 className="h-4 w-4 mr-2" />
              Analytics
            </TabsTrigger>
            <TabsTrigger value="settings">
              <Settings className="h-4 w-4 mr-2" />
              Settings
            </TabsTrigger>
          </TabsList>

          <TabsContent value="api-keys" className="space-y-4">
            <div className="flex justify-between items-center">
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Manage your API keys for accessing the AgenticQuote API
              </p>
              <Button onClick={() => setShowCreateKey(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Create API Key
              </Button>
            </div>

            <div className="space-y-3">
              {apiKeys.map((apiKey) => (
                <div key={apiKey.id} className="flex items-center justify-between p-4 rounded-lg border bg-white dark:bg-slate-800">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <p className="font-medium">{apiKey.name}</p>
                      <span className="text-xs bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 px-2 py-1 rounded">
                        Active
                      </span>
                    </div>
                    <div className="flex items-center gap-2 mt-2">
                      <code className="text-sm bg-slate-100 dark:bg-slate-900 px-2 py-1 rounded">
                        {apiKey.key}
                      </code>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => copyToClipboard(apiKey.key)}
                      >
                        {copiedKey === apiKey.key ? (
                          <Check className="h-4 w-4" />
                        ) : (
                          <Copy className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                    <p className="text-xs text-slate-600 dark:text-slate-400 mt-2">
                      Created: {apiKey.created} • Last Used: {apiKey.lastUsed}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm">
                      <Settings className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => deleteKey(apiKey.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="webhooks" className="space-y-4">
            <div className="flex justify-between items-center">
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Configure webhooks to receive real-time event notifications
              </p>
              <Button onClick={() => setShowCreateWebhook(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Add Webhook
              </Button>
            </div>

            <div className="space-y-3">
              {webhooks.map((webhook) => (
                <div key={webhook.id} className="flex items-center justify-between p-4 rounded-lg border bg-white dark:bg-slate-800">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <p className="font-medium">{webhook.url}</p>
                      <span className={`text-xs px-2 py-1 rounded ${
                        webhook.status === 'active' 
                          ? 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300'
                          : 'bg-gray-100 dark:bg-gray-900 text-gray-700 dark:text-gray-300'
                      }`}>
                        {webhook.status}
                      </span>
                    </div>
                    <p className="text-xs text-slate-600 dark:text-slate-400 mt-2">
                      Events: {webhook.events.join(', ')} • Created: {webhook.created}
                    </p>
                    <p className="text-xs text-slate-600 dark:text-slate-400">
                      Last Triggered: {webhook.lastTriggered}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm">
                      <RefreshCw className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => deleteWebhook(webhook.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="analytics" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 rounded-lg border bg-white dark:bg-slate-800">
                <p className="text-sm text-slate-600 dark:text-slate-400">Total API Calls</p>
                <p className="text-2xl font-bold mt-2">12,458</p>
                <p className="text-xs text-green-600 dark:text-green-400 mt-1">+12% from last week</p>
              </div>
              <div className="p-4 rounded-lg border bg-white dark:bg-slate-800">
                <p className="text-sm text-slate-600 dark:text-slate-400">Success Rate</p>
                <p className="text-2xl font-bold mt-2">99.2%</p>
                <p className="text-xs text-green-600 dark:text-green-400 mt-1">+0.5% from last week</p>
              </div>
              <div className="p-4 rounded-lg border bg-white dark:bg-slate-800">
                <p className="text-sm text-slate-600 dark:text-slate-400">Avg Response Time</p>
                <p className="text-2xl font-bold mt-2">145ms</p>
                <p className="text-xs text-green-600 dark:text-green-400 mt-1">-8ms from last week</p>
              </div>
            </div>

            <div className="p-4 rounded-lg border bg-white dark:bg-slate-800">
              <p className="font-medium mb-4">API Usage Over Time</p>
              <div className="h-40 flex items-end gap-2">
                {[40, 65, 45, 80, 55, 90, 70, 85, 60, 95, 75, 88].map((height, i) => (
                  <div
                    key={i}
                    className="flex-1 bg-blue-500 dark:bg-blue-600 rounded-t"
                    style={{ height: `${height}%` }}
                  />
                ))}
              </div>
              <div className="flex justify-between mt-2 text-xs text-slate-600 dark:text-slate-400">
                <span>Jan</span>
                <span>Feb</span>
                <span>Mar</span>
                <span>Apr</span>
                <span>May</span>
                <span>Jun</span>
                <span>Jul</span>
                <span>Aug</span>
                <span>Sep</span>
                <span>Oct</span>
                <span>Nov</span>
                <span>Dec</span>
              </div>
            </div>

            <div className="flex gap-2">
              <Button variant="outline">
                <Download className="h-4 w-4 mr-2" />
                Export Report
              </Button>
              <Button variant="outline">
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh Data
              </Button>
            </div>
          </TabsContent>

          <TabsContent value="settings" className="space-y-4">
            <div className="space-y-4">
              <div className="p-4 rounded-lg border bg-white dark:bg-slate-800">
                <p className="font-medium mb-2">Rate Limits</p>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600 dark:text-slate-400">Requests per minute</span>
                    <span>60</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600 dark:text-slate-400">Requests per hour</span>
                    <span>1,000</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600 dark:text-slate-400">Requests per day</span>
                    <span>10,000</span>
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-lg border bg-white dark:bg-slate-800">
                <p className="font-medium mb-2">API Version</p>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-slate-600 dark:text-slate-400">Current Version</span>
                  <span className="bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 px-2 py-1 rounded text-sm">
                    v1
                  </span>
                </div>
              </div>

              <div className="p-4 rounded-lg border bg-white dark:bg-slate-800">
                <p className="font-medium mb-2">Webhook Signature</p>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Enable HMAC SHA256 signatures for webhook security
                </p>
                <Button variant="outline" size="sm" className="mt-2">
                  Configure Signature
                </Button>
              </div>

              <div className="p-4 rounded-lg border bg-white dark:bg-slate-800">
                <p className="font-medium mb-2">API Documentation</p>
                <Button variant="outline" size="sm">
                  View OpenAPI Spec
                </Button>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}
