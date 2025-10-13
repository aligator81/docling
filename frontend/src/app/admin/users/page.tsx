'use client';

import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  Typography,
  Space,
  Tag,
  Tooltip,
  message,
  Popconfirm,
  Row,
  Col,
  Statistic,
  Avatar,
} from 'antd';
import {
  UserOutlined,
  EditOutlined,
  DeleteOutlined,
  UserAddOutlined,
  CrownOutlined,
  LockOutlined,
  UnlockOutlined,
  ReloadOutlined,
  KeyOutlined,
} from '@ant-design/icons';
import { useRouter } from 'next/navigation';
import { AuthService } from '@/lib/auth';
import { api } from '@/lib/api';
import Layout from '@/components/ui/Layout';
import type { User } from '@/types';

const { Title, Text } = Typography;
const { Option } = Select;

interface UserFormData {
  username: string;
  email?: string;
  password: string;
  role: 'admin' | 'user' | 'super_admin';
}

export default function AdminUsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [passwordModalVisible, setPasswordModalVisible] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [passwordUser, setPasswordUser] = useState<User | null>(null);
  const [form] = Form.useForm();
  const [passwordForm] = Form.useForm();
  const router = useRouter();

  const columns = [
    {
      title: 'User',
      key: 'user',
      render: (record: User) => (
        <div className="flex items-center space-x-3">
          <Avatar icon={<UserOutlined />} />
          <div>
            <div className="font-medium">{record.username}</div>
            <div className="text-sm text-gray-500">{record.email}</div>
          </div>
        </div>
      ),
    },
    {
      title: 'Role',
      dataIndex: 'role',
      key: 'role',
      render: (role: string) => {
        const getRoleColor = (role: string) => {
          switch (role) {
            case 'super_admin': return 'red';
            case 'admin': return 'gold';
            default: return 'blue';
          }
        };

        const getRoleIcon = (role: string) => {
          switch (role) {
            case 'super_admin': return <CrownOutlined />;
            case 'admin': return <CrownOutlined />;
            default: return null;
          }
        };

        return (
          <Tag color={getRoleColor(role)}>
            {getRoleIcon(role)}
            {role.replace('_', ' ')}
          </Tag>
        );
      },
    },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'success' : 'error'}>
          {isActive ? (
            <>
              <UnlockOutlined /> Active
            </>
          ) : (
            <>
              <LockOutlined /> Inactive
            </>
          )}
        </Tag>
      ),
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleDateString(),
    },
    {
      title: 'Last Login',
      dataIndex: 'last_login',
      key: 'last_login',
      render: (date: string | null) =>
        date ? new Date(date).toLocaleString() : 'Never',
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (record: User) => (
        <Space>
          <Tooltip title="Edit User">
            <Button
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEditUser(record)}
            />
          </Tooltip>
          <Tooltip title={record.is_active ? 'Deactivate' : 'Activate'}>
            <Button
              size="small"
              type={record.is_active ? 'default' : 'primary'}
              icon={record.is_active ? <LockOutlined /> : <UnlockOutlined />}
              onClick={() => handleToggleUserStatus(record)}
            >
              {record.is_active ? 'Deactivate' : 'Activate'}
            </Button>
          </Tooltip>
          <Tooltip title="Reset Password">
            <Button
              size="small"
              icon={<KeyOutlined />}
              onClick={() => handleResetPassword(record)}
            />
          </Tooltip>
          {record.id !== AuthService.getUser()?.id && (
            <Popconfirm
              title="Delete user"
              description="Are you sure you want to delete this user?"
              onConfirm={() => handleDeleteUser(record.id)}
              okText="Yes"
              cancelText="No"
            >
              <Button size="small" danger icon={<DeleteOutlined />} />
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

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

    loadUsers();
  }, [router]);

  const loadUsers = async () => {
    try {
      const usersData = await api.getUsers();
      // Filter out super_admin users if current user is admin (not super_admin)
      const filteredUsers = AuthService.isSuperAdmin()
        ? usersData
        : usersData.filter(user => user.role !== 'super_admin');
      setUsers(filteredUsers);
    } catch (error) {
      message.error('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const handleEditUser = (user: User) => {
    setEditingUser(user);
    form.setFieldsValue({
      username: user.username,
      email: user.email,
      role: user.role,
    });
    setModalVisible(true);
  };

  const handleCreateUser = () => {
    setEditingUser(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();

      if (editingUser) {
        // Update existing user
        if (values.role !== editingUser.role) {
          // Check if admin is trying to assign admin/super_admin role
          if (AuthService.isAdmin() && !AuthService.isSuperAdmin() && values.role !== 'user') {
            message.error('Admin users can only assign "user" role');
            return;
          }
          await api.updateUserRole(editingUser.id, values.role);
          message.success('User role updated successfully');
        }
      } else {
        // Create new user
        try {
          const newUser = await api.createUser({
            username: values.username,
            email: values.email,
            password: values.password,
            role: values.role,
          });
          message.success('User created successfully');
        } catch (error: any) {
          // Handle specific error cases
          if (error.message?.includes('already registered')) {
            message.error('Username or email already exists');
          } else {
            message.error('Failed to create user');
          }
          throw error; // Re-throw to prevent modal from closing
        }
      }

      setModalVisible(false);
      form.resetFields();
      loadUsers();
    } catch (error) {
      message.error('Failed to save user');
    }
  };

  const handleToggleUserStatus = async (user: User) => {
    try {
      await api.updateUserStatus(user.id, !user.is_active);
      message.success(`User ${user.is_active ? 'deactivated' : 'activated'} successfully`);
      loadUsers();
    } catch (error) {
      message.error('Failed to update user status');
    }
  };

  const handleDeleteUser = async (userId: number) => {
    try {
      await api.deleteUser(userId);
      message.success('User deleted successfully');
      loadUsers();
    } catch (error) {
      message.error('Failed to delete user');
    }
  };

  const handleResetPassword = (user: User) => {
    setPasswordUser(user);
    passwordForm.resetFields();
    setPasswordModalVisible(true);
  };

  const handlePasswordModalOk = async () => {
    try {
      const values = await passwordForm.validateFields();
      await api.resetUserPassword(passwordUser!.id, values.new_password);
      message.success('Password reset successfully');
      setPasswordModalVisible(false);
      passwordForm.resetFields();
    } catch (error) {
      message.error('Failed to reset password');
    }
  };

  const stats = {
    totalUsers: users.length,
    activeUsers: users.filter(user => user.is_active).length,
    adminUsers: users.filter(user => user.role === 'admin').length,
    superAdminUsers: AuthService.isSuperAdmin() ? users.filter(user => user.role === 'super_admin').length : 0,
    recentUsers: users.filter(user => {
      const createdDate = new Date(user.created_at);
      const weekAgo = new Date();
      weekAgo.setDate(weekAgo.getDate() - 7);
      return createdDate > weekAgo;
    }).length,
  };

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <Title level={2}>👥 User Management</Title>
            <Text type="secondary">
              Manage users, roles, and permissions
            </Text>
          </div>
          <Space>
            <Button
              type="primary"
              icon={<UserAddOutlined />}
              onClick={handleCreateUser}
            >
              Add User
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={loadUsers}
              loading={loading}
            >
              Refresh
            </Button>
          </Space>
        </div>

        {/* Statistics */}
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="Total Users"
                value={stats.totalUsers}
                prefix={<UserOutlined />}
                valueStyle={{ color: '#667eea' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="Active Users"
                value={stats.activeUsers}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="Administrators"
                value={stats.adminUsers}
                prefix={<CrownOutlined />}
                valueStyle={{ color: '#faad14' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="New This Week"
                value={stats.recentUsers}
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
        </Row>

        {/* Users Table */}
        <Card>
          <Table
            columns={columns}
            dataSource={users}
            loading={loading}
            rowKey="id"
            pagination={{
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) =>
                `${range[0]}-${range[1]} of ${total} users`,
            }}
          />
        </Card>

        {/* User Modal */}
        <Modal
          title={editingUser ? 'Edit User' : 'Create New User'}
          open={modalVisible}
          onOk={handleModalOk}
          onCancel={() => {
            setModalVisible(false);
            form.resetFields();
          }}
          width={500}
        >
          <Form
            form={form}
            layout="vertical"
            initialValues={{
              role: 'user',
            }}
          >
            <Form.Item
              name="username"
              label="Username"
              rules={[
                { required: true, message: 'Please enter a username' },
                { min: 3, message: 'Username must be at least 3 characters' },
              ]}
            >
              <Input placeholder="Enter username" />
            </Form.Item>

            <Form.Item
              name="email"
              label="Email"
              rules={[
                { type: 'email', message: 'Please enter a valid email' },
              ]}
            >
              <Input placeholder="Enter email address" />
            </Form.Item>

            {!editingUser && (
              <Form.Item
                name="password"
                label="Password"
                rules={[
                  { required: true, message: 'Please enter a password' },
                  { min: 8, message: 'Password must be at least 8 characters' },
                ]}
              >
                <Input.Password placeholder="Enter password" />
              </Form.Item>
            )}

            <Form.Item
              name="role"
              label="Role"
              rules={[
                { required: true, message: 'Please select a role' },
              ]}
            >
              <Select placeholder="Select user role">
                <Option value="user">
                  <Tag color="blue">User</Tag>
                </Option>
                {AuthService.isSuperAdmin() && (
                  <>
                    <Option value="admin">
                      <Tag color="gold">
                        <CrownOutlined /> Admin
                      </Tag>
                    </Option>
                    <Option value="super_admin">
                      <Tag color="red">
                        <CrownOutlined /> Super Admin
                      </Tag>
                    </Option>
                  </>
                )}
                {AuthService.isAdmin() && !AuthService.isSuperAdmin() && (
                  <Option value="admin" disabled>
                    <Tag color="gold">
                      <CrownOutlined /> Admin (Super Admin Only)
                    </Tag>
                  </Option>
                )}
              </Select>
            </Form.Item>
          </Form>
        </Modal>

        {/* Password Reset Modal */}
        <Modal
          title={`Reset Password for ${passwordUser?.username}`}
          open={passwordModalVisible}
          onOk={handlePasswordModalOk}
          onCancel={() => {
            setPasswordModalVisible(false);
            passwordForm.resetFields();
          }}
          width={400}
        >
          <Form
            form={passwordForm}
            layout="vertical"
          >
            <Form.Item
              name="new_password"
              label="New Password"
              rules={[
                { required: true, message: 'Please enter a new password' },
                { min: 8, message: 'Password must be at least 8 characters' },
              ]}
            >
              <Input.Password placeholder="Enter new password" />
            </Form.Item>

            <Form.Item
              name="confirm_password"
              label="Confirm Password"
              dependencies={['new_password']}
              rules={[
                { required: true, message: 'Please confirm the password' },
                ({ getFieldValue }) => ({
                  validator(_, value) {
                    if (!value || getFieldValue('new_password') === value) {
                      return Promise.resolve();
                    }
                    return Promise.reject(new Error('Passwords do not match'));
                  },
                }),
              ]}
            >
              <Input.Password placeholder="Confirm new password" />
            </Form.Item>
          </Form>
        </Modal>
      </div>
    </Layout>
  );
}