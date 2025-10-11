'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Spin, Typography } from 'antd';
import { AuthService } from '@/lib/auth';

const { Title, Text } = Typography;

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    // Check authentication status and redirect accordingly
    if (AuthService.isAuthenticated()) {
      router.push('/dashboard');
    } else {
      router.push('/login');
    }
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="text-center">
        <div className="mb-8">
          <Title level={1} className="text-gray-800 mb-4">
            📚 Document Q&A Assistant
          </Title>
          <Text type="secondary" className="text-lg">
            Redirecting to login...
          </Text>
        </div>
        <Spin size="large" />
      </div>
    </div>
  );
}
