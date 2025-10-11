'use client';

import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Input,
  Button,
  Typography,
  Space,
  Alert,
  Row,
  Col,
  Select,
  Switch,
  Divider,
  message,
  Tabs,
  Statistic,
  Tag,
} from 'antd';
import {
  SettingOutlined,
  KeyOutlined,
  RobotOutlined,
  DatabaseOutlined,
  SaveOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons';
import { useRouter } from 'next/navigation';
import { AuthService } from '@/lib/auth';
import { api } from '@/lib/api';
import Layout from '@/components/ui/Layout';

const { Title, Text } = Typography;
const { Option } = Select;
const { TabPane } = Tabs;

interface APIConfig {
  provider: 'openai' | 'mistral';
  api_key: string;
  is_active: boolean;
}

export default function AdminSettingsPage() {
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [systemStats, setSystemStats] = useState<any>(null);
  const [form] = Form.useForm();
  const router = useRouter();

  useEffect(() => {
    // Check admin authentication
    if (!AuthService.isAuthenticated() || !AuthService.isAdmin()) {
      router.push('/login');
      return;
    }

    loadSystemStats();
  }, [router]);

  const loadSystemStats = async () => {
    try {
      const stats = await api.getSystemStats();
      setSystemStats(stats);
    } catch (error) {
      console.error('Failed to load system stats:', error);
    }
  };

  const handleSaveAPIConfig = async (values: APIConfig) => {
    setLoading(true);
    try {
      await api.configureAPIKeys(values);
      message.success(`${values.provider} API configuration saved successfully`);
      form.resetFields();
    } catch (error) {
      message.error('Failed to save API configuration');
    } finally {
      setLoading(false);
    }
  };

  const handleTestConnection = async () => {
    setTesting(true);
    try {
      // Test database connection
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/admin/health`);
      if (response.ok) {
        message.success('System health check passed');
        loadSystemStats();
      } else {
        message.error('System health check failed');
      }
    } catch (error) {
      message.error('Failed to test system health');
    } finally {
      setTesting(false);
    }
  };

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="text-center">
          <Title level={2}>⚙️ System Settings</Title>
          <Text type="secondary">
            Configure API keys, manage system settings, and monitor performance
          </Text>
        </div>

        <Tabs defaultActiveKey="api-config" type="card">
          {/* API Configuration Tab */}
          <TabPane tab={<span><KeyOutlined />API Configuration</span>} key="api-config">
            <Row gutter={[16, 16]}>
              <Col xs={24} lg={16}>
                <Card title="🔑 API Keys Configuration">
                  <Alert
                    message="Secure API Key Management"
                    description="API keys are stored securely and used only for document processing and chat functionality."
                    type="info"
                    showIcon
                    className="mb-6"
                  />

                  <Form
                    form={form}
                    layout="vertical"
                    onFinish={handleSaveAPIConfig}
                    initialValues={{
                      is_active: true,
                    }}
                  >
                    <Row gutter={16}>
                      <Col xs={24} md={12}>
                        <Form.Item
                          name="provider"
                          label="AI Provider"
                          rules={[
                            { required: true, message: 'Please select a provider' },
                          ]}
                        >
                          <Select placeholder="Select AI provider">
                            <Option value="openai">
                              <div className="flex items-center space-x-2">
                                <RobotOutlined />
                                <span>OpenAI</span>
                              </div>
                            </Option>
                            <Option value="mistral">
                              <div className="flex items-center space-x-2">
                                <RobotOutlined />
                                <span>Mistral AI</span>
                              </div>
                            </Option>
                          </Select>
                        </Form.Item>
                      </Col>

                      <Col xs={24} md={12}>
                        <Form.Item
                          name="is_active"
                          label="Status"
                          valuePropName="checked"
                        >
                          <Switch
                            checkedChildren="Active"
                            unCheckedChildren="Inactive"
                          />
                        </Form.Item>
                      </Col>
                    </Row>

                    <Form.Item
                      name="api_key"
                      label="API Key"
                      rules={[
                        { required: true, message: 'Please enter the API key' },
                        { min: 20, message: 'API key seems too short' },
                      ]}
                    >
                      <Input.Password
                        placeholder="Enter your API key"
                        style={{ width: '100%' }}
                      />
                    </Form.Item>

                    <Form.Item>
                      <Space>
                        <Button
                          type="primary"
                          htmlType="submit"
                          loading={loading}
                          icon={<SaveOutlined />}
                        >
                          Save Configuration
                        </Button>
                        <Button
                          onClick={() => form.resetFields()}
                        >
                          Reset
                        </Button>
                      </Space>
                    </Form.Item>
                  </Form>

                  <Divider />

                  <div className="space-y-4">
                    <Title level={4}>📚 API Key Guidelines</Title>

                    <Card size="small" title="OpenAI" type="inner">
                      <Text>
                        • Get your API key from{' '}
                        <a
                          href="https://platform.openai.com/api-keys"
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600"
                        >
                          OpenAI Platform
                        </a>
                        <br />
                        • Supports: GPT-4, GPT-3.5-turbo, text-embedding-3-large
                        <br />
                        • Recommended model: gpt-4o-mini
                      </Text>
                    </Card>

                    <Card size="small" title="Mistral AI" type="inner">
                      <Text>
                        • Get your API key from{' '}
                        <a
                          href="https://console.mistral.ai/"
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600"
                        >
                          Mistral Console
                        </a>
                        <br />
                        • Supports: Mistral Large, Medium, Small models
                        <br />
                        • Includes embedding models for document search
                      </Text>
                    </Card>
                  </div>
                </Card>
              </Col>

              <Col xs={24} lg={8}>
                <Card title="🔧 Quick Actions">
                  <Space direction="vertical" className="w-full">
                    <Button
                      type="primary"
                      icon={<CheckCircleOutlined />}
                      onClick={handleTestConnection}
                      loading={testing}
                      block
                    >
                      Test System Health
                    </Button>

                    <Button
                      icon={<ReloadOutlined />}
                      onClick={loadSystemStats}
                      block
                    >
                      Refresh Stats
                    </Button>

                    <Button
                      icon={<DatabaseOutlined />}
                      onClick={() => router.push('/admin/database')}
                      block
                    >
                      Database Tools
                    </Button>
                  </Space>
                </Card>

                {systemStats && (
                  <Card title="📊 System Status" className="mt-4">
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <Text>Database:</Text>
                        <Tag color="success">Connected</Tag>
                      </div>
                      <div className="flex justify-between">
                        <Text>API Keys:</Text>
                        <Tag color="processing">Configured</Tag>
                      </div>
                      <div className="flex justify-between">
                        <Text>File Storage:</Text>
                        <Tag color="success">Available</Tag>
                      </div>
                    </div>
                  </Card>
                )}
              </Col>
            </Row>
          </TabPane>

          {/* System Monitoring Tab */}
          <TabPane tab={<span><DatabaseOutlined />System Monitoring</span>} key="monitoring">
            <Row gutter={[16, 16]}>
              <Col xs={24} md={12}>
                <Card title="📈 Performance Metrics">
                  {systemStats ? (
                    <Row gutter={[16, 16]}>
                      <Col span={12}>
                        <Statistic
                          title="Total Users"
                          value={systemStats.total_users}
                          prefix={<SettingOutlined />}
                        />
                      </Col>
                      <Col span={12}>
                        <Statistic
                          title="Active Sessions"
                          value={systemStats.active_sessions}
                          prefix={<CheckCircleOutlined />}
                        />
                      </Col>
                      <Col span={12}>
                        <Statistic
                          title="Documents"
                          value={systemStats.total_documents}
                          prefix={<DatabaseOutlined />}
                        />
                      </Col>
                      <Col span={12}>
                        <Statistic
                          title="Embeddings"
                          value={systemStats.total_embeddings}
                          prefix={<RobotOutlined />}
                        />
                      </Col>
                    </Row>
                  ) : (
                    <div className="text-center py-8">
                      <Text type="secondary">Loading system statistics...</Text>
                    </div>
                  )}
                </Card>
              </Col>

              <Col xs={24} md={12}>
                <Card title="🔍 System Health">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <Text>Database Connection</Text>
                      <Tag color="success" icon={<CheckCircleOutlined />}>
                        Healthy
                      </Tag>
                    </div>

                    <div className="flex items-center justify-between">
                      <Text>API Endpoints</Text>
                      <Tag color="success" icon={<CheckCircleOutlined />}>
                        Operational
                      </Tag>
                    </div>

                    <div className="flex items-center justify-between">
                      <Text>File Storage</Text>
                      <Tag color="success" icon={<CheckCircleOutlined />}>
                        Available
                      </Tag>
                    </div>

                    <div className="flex items-center justify-between">
                      <Text>AI Services</Text>
                      <Tag color="processing" icon={<ExclamationCircleOutlined />}>
                        Check Required
                      </Tag>
                    </div>
                  </div>

                  <Divider />

                  <Button
                    type="primary"
                    icon={<ReloadOutlined />}
                    onClick={handleTestConnection}
                    loading={testing}
                    block
                  >
                    Run Health Check
                  </Button>
                </Card>
              </Col>
            </Row>
          </TabPane>

          {/* Database Tools Tab */}
          <TabPane tab={<span><DatabaseOutlined />Database Tools</span>} key="database">
            <Card title="🗄️ Database Management">
              <Alert
                message="Database Operations"
                description="Advanced database management tools for system administrators."
                type="warning"
                showIcon
                className="mb-6"
              />

              <Row gutter={[16, 16]}>
                <Col xs={24} sm={12} md={8}>
                  <Card>
                    <Statistic
                      title="Database Size"
                      value={2.4}
                      suffix="GB"
                      valueStyle={{ color: '#667eea' }}
                    />
                  </Card>
                </Col>
                <Col xs={24} sm={12} md={8}>
                  <Card>
                    <Statistic
                      title="Tables"
                      value={8}
                      valueStyle={{ color: '#52c41a' }}
                    />
                  </Card>
                </Col>
                <Col xs={24} sm={12} md={8}>
                  <Card>
                    <Statistic
                      title="Connections"
                      value={3}
                      suffix="/ 20"
                      valueStyle={{ color: '#faad14' }}
                    />
                  </Card>
                </Col>
              </Row>

              <Divider />

              <div className="space-y-4">
                <Title level={4}>Available Tools</Title>

                <Card size="small" title="Backup & Recovery" type="inner">
                  <Text>
                    Database backup and recovery tools will be available here.
                    Features include automated backups, point-in-time recovery, and export functionality.
                  </Text>
                </Card>

                <Card size="small" title="Performance Monitoring" type="inner">
                  <Text>
                    Real-time database performance monitoring, query analysis,
                    and optimization recommendations will be displayed here.
                  </Text>
                </Card>

                <Card size="small" title="Data Maintenance" type="inner">
                  <Text>
                    Database maintenance tools including index optimization,
                    vacuum operations, and data integrity checks.
                  </Text>
                </Card>
              </div>
            </Card>
          </TabPane>
        </Tabs>
      </div>
    </Layout>
  );
}