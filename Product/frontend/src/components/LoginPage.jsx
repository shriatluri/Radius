import { SignIn } from '@clerk/clerk-react';

export default function LoginPage() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Radius</h1>
          <p className="text-gray-600">Compliance Dashboard</p>
        </div>
        <SignIn
          appearance={{
            elements: {
              rootBox: 'mx-auto',
              card: 'shadow-md',
            },
          }}
        />
      </div>
    </div>
  );
}
