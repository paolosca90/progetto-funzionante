import { Metadata } from 'next'
import dynamic from 'next/dynamic'
import { Suspense } from 'react'
import LoadingSpinner from '@/components/ui/loading-spinner'

// Lazy load the register component
const RegisterForm = dynamic(() => import('@/components/auth/register-form'), {
  loading: () => <LoadingSpinner />,
  ssr: false, // Disable SSR for better mobile performance
})

export const metadata: Metadata = {
  title: 'Sign Up - AI Cash Revolution',
  description: 'Create your AI Cash Revolution trading account',
}

export default function RegisterPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-white dark:from-dark-900 dark:to-dark-800 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <Suspense fallback={<LoadingSpinner />}>
          <RegisterForm />
        </Suspense>
      </div>
    </div>
  )
}