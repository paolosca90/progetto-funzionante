import { Metadata } from 'next'
import dynamic from 'next/dynamic'
import { Suspense } from 'react'
import LoadingSpinner from '@/components/ui/loading-spinner'

// Lazy load the login component
const LoginForm = dynamic(() => import('@/components/auth/login-form'), {
  loading: () => <LoadingSpinner />,
  ssr: false, // Disable SSR for better mobile performance
})

export const metadata: Metadata = {
  title: 'Login - AI Cash Revolution',
  description: 'Sign in to your AI Cash Revolution trading account',
}

export default function LoginPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-white dark:from-dark-900 dark:to-dark-800 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <Suspense fallback={<LoadingSpinner />}>
          <LoginForm />
        </Suspense>
      </div>
    </div>
  )
}