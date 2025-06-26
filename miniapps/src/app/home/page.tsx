'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/lib/store'
import { LogOut, Scale, Home } from 'lucide-react'

const miniapps = [
  {
    name: 'Comparison Tool',
    description: 'Compare multiple choices against various criteria to make better decisions',
    icon: '⚖️',
    color: '#FF6B6B',
    href: '/comparison-tool'
  }
]

export default function HomePage() {
  const { isAuthenticated, username, logout } = useAuthStore()
  const router = useRouter()

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/')
    }
  }, [isAuthenticated, router])

  const handleLogout = () => {
    logout()
    router.push('/')
  }

  if (!isAuthenticated) {
    return null
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <Home className="h-8 w-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-gray-900">Lakehouse Miniapps</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">
                Welcome, <span className="font-medium">{username}</span>! 👋
              </span>
              <button
                onClick={handleLogout}
                className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-gray-700 bg-gray-100 hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
              >
                <LogOut className="h-4 w-4 mr-2" />
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-2">
              Available Applications
            </h2>
            <p className="text-lg text-gray-600">
              A collection of useful mini applications for decision-making and productivity
            </p>
          </div>

          {/* Miniapps Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {miniapps.map((app, index) => (
              <div
                key={index}
                className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-300 overflow-hidden"
              >
                <div
                  className="h-2"
                  style={{ backgroundColor: app.color }}
                />
                <div className="p-6">
                  <div className="text-center">
                    <div className="text-4xl mb-4">{app.icon}</div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">
                      {app.name}
                    </h3>
                    <p className="text-gray-600 text-sm mb-6">
                      {app.description}
                    </p>
                    <button
                      onClick={() => router.push(app.href)}
                      className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors duration-200"
                    >
                      Launch {app.name}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Footer */}
          <div className="mt-12 text-center">
            <p className="text-gray-500 text-sm">
              More miniapps coming soon! 🚀
            </p>
          </div>
        </div>
      </main>
    </div>
  )
} 