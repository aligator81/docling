'use client';

import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Typography,
  Space,
  Alert,
  Row,
  Col,
  Statistic,
  Progress,
  Tag,
  Modal,
  Input,
  message,
  Tooltip,
} from 'antd';
import {
  DatabaseOutlined,
  TableOutlined,
  ReloadOutlined,
  InfoCircleOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  SyncOutlined,
  DeleteOutlined,
} from '@ant-design/icons';
import { useRouter } from 'next/navigation';
import { AuthService } from '@/lib/auth';
import Layout from '@/components/ui/Layout';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

interface DatabaseTable {
  name: string;
  rows: number;
  size: string;
  status: 'healthy' | 'warning' | 'error';
}

export default function AdminDatabasePage() {
  const [tables, setTables] = useState<DatabaseTable[]>([]);
  const [loading, setLoading] = useState(true);
  const [sqlModalVisible, setSqlModalVisible] = useState(false);
  const [customSql, setCustomSql] = useState('');
  const [executingSql, setExecutingSql] = useState(false);
  const [deleteAllModalVisible, setDeleteAllModalVisible] = useState(false);
  const [deletingAll, setDeletingAll] = useState(false);
  const router = useRouter();

  useEffect(() => {
    // Check authentication and permissions
    if (!AuthService.isAuthenticated()) {
      router.push('/login');
      return;
    }

    // Check if user is admin or super_admin
    if (!AuthService.isAdmin()) {
      router.push('/dashboard');
      return;
    }

    loadDatabaseInfo();
  }, [router]);

  const loadDatabaseInfo = async () => {
    setLoading(true);
    try {
      // Simulate loading database information
      // In a real implementation, this would call the backend API
      const mockTables: DatabaseTable[] = [
        {
          name: 'users',
          rows: 15,
          size: '2.1 MB',
          status: 'healthy',
        },
        {
          name: 'documents',
          rows: 127,
          size: '45.3 MB',
          status: 'healthy',
        },
        {
          name: 'document_chunks',
          rows: 15420,
          size: '1.2 GB',
          status: 'healthy',
        },
        {
          name: 'embeddings',
          rows: 15420,
          size: '8.7 GB',
          status: 'warning',
        },
        {
          name: 'chat_history',
          rows: 3421,
          size: '156 MB',
          status: 'healthy',
        },
        {
          name: 'api_sessions',
          rows: 8,
          size: '1.2 MB',
          status: 'healthy',
        },
      ];

      setTables(mockTables);
    } catch (error) {
      message.error('Failed to load database information');
    } finally {
      setLoading(false);
    }
  };

  const handleExecuteSql = async () => {
    if (!customSql.trim()) {
      message.warning('Please enter SQL to execute');
      return;
    }

    setExecutingSql(true);
    try {
      // Simulate SQL execution
      await new Promise(resolve => setTimeout(resolve, 2000));
      message.success('SQL executed successfully');
      setSqlModalVisible(false);
      setCustomSql('');
    } catch (error) {
      message.error('Failed to execute SQL');
    } finally {
      setExecutingSql(false);
    }
  };

  const handleDeleteAllDocuments = async () => {
    setDeletingAll(true);
    try {
      const token = AuthService.getToken();
      const response = await fetch('/api/admin/documents', {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const result = await response.json();
        message.success(result.message || 'All documents deleted successfully');
        setDeleteAllModalVisible(false);
        // Refresh the page data
        loadDatabaseInfo();
      } else {
        const error = await response.json();
        message.error(error.detail || 'Failed to delete documents');
      }
    } catch (error) {
      message.error('Failed to delete documents');
    } finally {
      setDeletingAll(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'warning':
        return <WarningOutlined style={{ color: '#faad14' }} />;
      case 'error':
        return <WarningOutlined style={{ color: '#ff4d4f' }} />;
      default:
        return <InfoCircleOutlined />;
    }
  };

  const getStatusTag = (status: string) => {
    const statusConfig = {
      healthy: { color: 'success', text: 'Healthy' },
      warning: { color: 'warning', text: 'Warning' },
      error: { color: 'error', text: 'Error' },
    };
    const config = statusConfig[status as keyof typeof statusConfig] || { color: 'default', text: status };
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  const columns = [
    {
      title: 'Table Name',
      dataIndex: 'name',
      key: 'name',
      render: (name: string) => (
        <div className="flex items-center space-x-2">
          <TableOutlined />
          <Text strong>{name}</Text>
        </div>
      ),
    },
    {
      title: 'Rows',
      dataIndex: 'rows',
      key: 'rows',
      render: (rows: number) => rows.toLocaleString(),
      sorter: (a: DatabaseTable, b: DatabaseTable) => a.rows - b.rows,
    },
    {
      title: 'Size',
      dataIndex: 'size',
      key: 'size',
      render: (size: string) => <Text code>{size}</Text>,
      sorter: (a: DatabaseTable, b: DatabaseTable) =>
        parseFloat(a.size) - parseFloat(b.size),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <div className="flex items-center space-x-2">
          {getStatusIcon(status)}
          {getStatusTag(status)}
        </div>
      ),
      filters: [
        { text: 'Healthy', value: 'healthy' },
        { text: 'Warning', value: 'warning' },
        { text: 'Error', value: 'error' },
      ],
      onFilter: (value: any, record: DatabaseTable) => record.status === value,
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (record: DatabaseTable) => (
        <Space>
          <Tooltip title="View Details">
            <Button size="small" onClick={() => handleViewTable(record)}>
              Details
            </Button>
          </Tooltip>
          <Tooltip title="Optimize">
            <Button size="small" type="primary" onClick={() => handleOptimizeTable(record)}>
              Optimize
            </Button>
          </Tooltip>
        </Space>
      ),
    },
  ];

  const handleViewTable = (table: DatabaseTable) => {
    message.info(`Viewing details for table: ${table.name}`);
  };

  const handleOptimizeTable = (table: DatabaseTable) => {
    message.success(`Optimization started for table: ${table.name}`);
  };

  const totalSize = tables.reduce((acc, table) => {
    const sizeNum = parseFloat(table.size.replace(' GB', '').replace(' MB', '').replace(' KB', ''));
    const multiplier = table.size.includes('GB') ? 1024 : table.size.includes('MB') ? 1 : 0.001;
    return acc + (sizeNum * multiplier);
  }, 0);

  const healthyTables = tables.filter(t => t.status === 'healthy').length;
  const totalTables = tables.length;
  const healthPercentage = totalTables > 0 ? (healthyTables / totalTables) * 100 : 0;

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="text-center">
          <Title level={2}>🗄️ Database Management</Title>
          <Text type="secondary">
            Monitor and manage database performance, tables, and maintenance tasks
          </Text>
        </div>

        {/* Database Overview */}
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="Total Tables"
                value={totalTables}
                prefix={<TableOutlined />}
                valueStyle={{ color: '#667eea' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="Database Size"
                value={totalSize}
                precision={1}
                suffix="GB"
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="Health Status"
                value={healthPercentage}
                precision={1}
                suffix="%"
                valueStyle={{
                  color: healthPercentage >= 80 ? '#52c41a' : healthPercentage >= 60 ? '#faad14' : '#ff4d4f'
                }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="Total Rows"
                value={tables.reduce((acc, table) => acc + table.rows, 0)}
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
        </Row>

        {/* Database Health */}
        <Card title="💊 Database Health">
          <div className="space-y-4">
            <div>
              <Text strong>Overall Health: </Text>
              <Progress
                percent={healthPercentage}
                status={healthPercentage >= 80 ? 'success' : healthPercentage >= 60 ? 'normal' : 'exception'}
                strokeColor={
                  healthPercentage >= 80 ? '#52c41a' :
                  healthPercentage >= 60 ? '#faad14' : '#ff4d4f'
                }
              />
            </div>

            <Row gutter={[16, 16]}>
              <Col span={8}>
                <div className="text-center">
                  <div style={{ fontSize: '24px', color: '#52c41a' }}>
                    {healthyTables}
                  </div>
                  <Text type="secondary">Healthy Tables</Text>
                </div>
              </Col>
              <Col span={8}>
                <div className="text-center">
                  <div style={{ fontSize: '24px', color: '#faad14' }}>
                    {tables.filter(t => t.status === 'warning').length}
                  </div>
                  <Text type="secondary">Need Attention</Text>
                </div>
              </Col>
              <Col span={8}>
                <div className="text-center">
                  <div style={{ fontSize: '24px', color: '#ff4d4f' }}>
                    {tables.filter(t => t.status === 'error').length}
                  </div>
                  <Text type="secondary">Issues</Text>
                </div>
              </Col>
            </Row>
          </div>
        </Card>

        {/* Tables Management */}
        <Card
          title="📋 Database Tables"
          extra={
            <Space>
              <Button
                icon={<SyncOutlined />}
                onClick={loadDatabaseInfo}
                loading={loading}
              >
                Refresh
              </Button>
              <Button
                type="primary"
                icon={<DatabaseOutlined />}
                onClick={() => setSqlModalVisible(true)}
              >
                Execute SQL
              </Button>
            </Space>
          }
        >
          <Table
            columns={columns}
            dataSource={tables}
            loading={loading}
            rowKey="name"
            pagination={{
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) =>
                `${range[0]}-${range[1]} of ${total} tables`,
            }}
          />
        </Card>

        {/* Maintenance Tools */}
        <Card title="🔧 Maintenance Tools">
          <Alert
            message="Database Maintenance"
            description="Use these tools to optimize and maintain database performance."
            type="info"
            showIcon
            className="mb-6"
          />

          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12} md={6}>
              <Card
                title="VACUUM"
                type="inner"
                extra={<Button size="small">Run</Button>}
              >
                <Paragraph type="secondary">
                  Reclaim storage occupied by dead tuples and optimize table performance.
                </Paragraph>
              </Card>
            </Col>

            <Col xs={24} sm={12} md={6}>
              <Card
                title="REINDEX"
                type="inner"
                extra={<Button size="small">Run</Button>}
              >
                <Paragraph type="secondary">
                  Rebuild indexes to improve query performance and reduce index bloat.
                </Paragraph>
              </Card>
            </Col>

            <Col xs={24} sm={12} md={6}>
              <Card
                title="ANALYZE"
                type="inner"
                extra={<Button size="small">Run</Button>}
              >
                <Paragraph type="secondary">
                  Update table statistics for better query planning and performance.
                </Paragraph>
              </Card>
            </Col>

            <Col xs={24} sm={12} md={6}>
              <Card
                title="🗑️ Delete All Documents"
                type="inner"
                extra={
                  <Button
                    size="small"
                    danger
                    icon={<DeleteOutlined />}
                    onClick={() => setDeleteAllModalVisible(true)}
                  >
                    Delete All
                  </Button>
                }
              >
                <Paragraph type="secondary">
                  Permanently delete all documents, chunks, and embeddings from the system.
                </Paragraph>
              </Card>
            </Col>
          </Row>
        </Card>

        {/* SQL Execution Modal */}
        <Modal
          title="⚡ Execute Custom SQL"
          open={sqlModalVisible}
          onCancel={() => setSqlModalVisible(false)}
          footer={[
            <Button key="cancel" onClick={() => setSqlModalVisible(false)}>
              Cancel
            </Button>,
            <Button
              key="execute"
              type="primary"
              loading={executingSql}
              onClick={handleExecuteSql}
            >
              Execute SQL
            </Button>,
          ]}
          width={800}
        >
          <Alert
            message="⚠️ Warning"
            description="Executing custom SQL can modify your database. Please ensure you have proper backups before proceeding."
            type="warning"
            showIcon
            className="mb-4"
          />

          <div className="space-y-4">
            <div>
              <Text strong>SQL Query:</Text>
              <TextArea
                value={customSql}
                onChange={(e) => setCustomSql(e.target.value)}
                placeholder="Enter your SQL query here..."
                rows={8}
              />
            </div>

            <Card size="small" title="💡 Common Queries" type="inner">
              <div className="space-y-2 text-sm">
                <div>
                  <Text code>SELECT COUNT(*) FROM users;</Text>
                  <br />
                  <Text type="secondary">Count total users</Text>
                </div>
                <div>
                  <Text code>VACUUM ANALYZE;</Text>
                  <br />
                  <Text type="secondary">Optimize all tables</Text>
                </div>
                <div>
                  <Text code>SELECT * FROM documents WHERE status = 'failed';</Text>
                  <br />
                  <Text type="secondary">Find failed documents</Text>
                </div>
              </div>
            </Card>
          </div>
        </Modal>

        {/* Delete All Documents Modal */}
        <Modal
          title="🗑️ Delete All Documents"
          open={deleteAllModalVisible}
          onCancel={() => setDeleteAllModalVisible(false)}
          footer={[
            <Button key="cancel" onClick={() => setDeleteAllModalVisible(false)}>
              Cancel
            </Button>,
            <Button
              key="delete"
              type="primary"
              danger
              loading={deletingAll}
              onClick={handleDeleteAllDocuments}
            >
              Yes, Delete All Documents
            </Button>,
          ]}
          width={600}
        >
          <Alert
            message="⚠️ Destructive Action"
            description="This action cannot be undone. This will permanently delete all documents, document chunks, and embeddings from the system."
            type="error"
            showIcon
            className="mb-4"
          />

          <div className="space-y-4">
            <Card size="small" type="inner">
              <div className="space-y-2 text-sm">
                <div className="flex items-center space-x-2">
                  <DeleteOutlined style={{ color: '#ff4d4f' }} />
                  <Text strong>All documents will be deleted</Text>
                </div>
                <div className="flex items-center space-x-2">
                  <DeleteOutlined style={{ color: '#ff4d4f' }} />
                  <Text>All document chunks will be deleted</Text>
                </div>
                <div className="flex items-center space-x-2">
                  <DeleteOutlined style={{ color: '#ff4d4f' }} />
                  <Text>All embeddings will be deleted</Text>
                </div>
                <div className="flex items-center space-x-2">
                  <DeleteOutlined style={{ color: '#ff4d4f' }} />
                  <Text>Uploaded files will be removed from disk</Text>
                </div>
              </div>
            </Card>

            <Alert
              message="Confirmation Required"
              description="This action will affect all users and cannot be reversed. Please ensure you have proper backups before proceeding."
              type="warning"
              showIcon
            />
          </div>
        </Modal>
      </div>
    </Layout>
  );
}