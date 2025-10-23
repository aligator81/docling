'use client';

import React, { useState, useEffect } from 'react';
import { Form, Input, Button, Card, Typography, Alert, Space, Divider } from 'antd';
import { UserOutlined, LockOutlined, LoginOutlined } from '@ant-design/icons';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { AuthService } from '@/lib/auth';
import { api } from '@/lib/api';
import type { LoginForm } from '@/types';

const { Title, Text } = Typography;

export default function LoginPage() {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [companyName, setCompanyName] = useState<string>('');
  const [companyLogo, setCompanyLogo] = useState<string>('');
  const router = useRouter();

  useEffect(() => {
    const loadBranding = async () => {
      try {
        const branding = await api.getCompanyBranding();
        setCompanyName(branding.company_name);
        setCompanyLogo(branding.logo_url);
      } catch (error) {
        console.error('Failed to load branding:', error);
      }
    };
    loadBranding();
  }, []);

  // Check if already authenticated
  useEffect(() => {
    if (AuthService.isAuthenticated()) {
      router.push('/dashboard');
    }
  }, [router]);

  const handleSubmit = async (values: LoginForm) => {
    setLoading(true);
    setError(null);

    try {
      await AuthService.login(values);
      router.push('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <Card className="w-full max-w-md shadow-lg">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-2">
            {companyLogo ? (
              <img src={companyLogo} alt="Company Logo" className="h-8 mr-2" />
            ) : (
              <span className="text-2xl mr-2">📚</span>
            )}
            <Title level={2} className="text-gray-800 mb-0">
              {companyName || 'Document Q&A Assistant'}
            </Title>
          </div>
          <Text type="secondary" className="text-lg">
            Sign in to your account
          </Text>
        </div>

        {error && (
          <Alert
            message="Login Failed"
            description={error}
            type="error"
            showIcon
            className="mb-6"
          />
        )}

        <Form
          form={form}
          name="login"
          onFinish={handleSubmit}
          layout="vertical"
          size="large"
        >
          <Form.Item
            name="username"
            rules={[
              { required: true, message: 'Please enter your username' },
              { min: 3, message: 'Username must be at least 3 characters' },
            ]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="Username"
              autoComplete="username"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[
              { required: true, message: 'Please enter your password' },
              { min: 6, message: 'Password must be at least 6 characters' },
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="Password"
              autoComplete="current-password"
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              icon={<LoginOutlined />}
              block
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </Button>
          </Form.Item>
        </Form>

        <Divider />

        <div className="text-center">
          <Text type="secondary">
            Don't have an account?{' '}
            <Link href="/register" className="text-blue-600 hover:text-blue-800">
              Sign up here
            </Link>
          </Text>
        </div>

      </Card>
    </div>
  );
}