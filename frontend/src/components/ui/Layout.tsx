'use client';

import React, { useState, useEffect } from 'react';
import {
  Layout as AntLayout,
  Menu,
  Button,
  Avatar,
  Dropdown,
  Badge,
  Typography,
  Space,
  Drawer,
} from 'antd';
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  UserOutlined,
  LogoutOutlined,
  DashboardOutlined,
  FileTextOutlined,
  MessageOutlined,
  SettingOutlined,
  TeamOutlined,
} from '@ant-design/icons';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { AuthService } from '@/lib/auth';
import type { User } from '@/types';

const { Header, Sider, Content } = AntLayout;
const { Text } = Typography;

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileMenuVisible, setMobileMenuVisible] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const pathname = usePathname();

  useEffect(() => {
    // Load user data on client side only
    const userData = AuthService.getUser();
    setUser(userData);
  }, []);

  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: <Link href="/dashboard">Dashboard</Link>,
    },
    {
      key: '/documents',
      icon: <FileTextOutlined />,
      label: <Link href="/documents">Documents</Link>,
    },
    {
      key: '/chat',
      icon: <MessageOutlined />,
      label: <Link href="/chat">Chat</Link>,
    },
  ];

  // Add admin menu items if user is admin
  if (user?.role === 'admin') {
    menuItems.push(
      {
        key: '/admin/users',
        icon: <TeamOutlined />,
        label: <Link href="/admin/users">Users</Link>,
      },
      {
        key: '/admin/settings',
        icon: <SettingOutlined />,
        label: <Link href="/admin/settings">Settings</Link>,
      }
    );
  }

  const userMenuItems = [
    {
      key: 'profile',
      label: 'Profile',
      icon: <UserOutlined />,
    },
    {
      key: 'logout',
      label: 'Logout',
      icon: <LogoutOutlined />,
      onClick: () => {
        AuthService.logout();
        window.location.href = '/login';
      },
    },
  ];

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      {/* Logo/Brand */}
      <div className="flex items-center justify-center h-16 px-4 border-b border-gray-200">
        <Text strong className="text-lg">
          📚 Doc Q&A
        </Text>
      </div>

      {/* Navigation Menu */}
      <Menu
        mode="inline"
        selectedKeys={[pathname]}
        items={menuItems}
        className="flex-1 border-r-0"
      />
    </div>
  );

  return (
    <AntLayout className="min-h-screen">
      {/* Desktop Sidebar */}
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        className="hidden md:block"
        width={280}
      >
        <SidebarContent />
      </Sider>

      {/* Mobile Sidebar */}
      <Drawer
        title="📚 Doc Q&A"
        placement="left"
        onClose={() => setMobileMenuVisible(false)}
        open={mobileMenuVisible}
        width={280}
        styles={{ body: { padding: 0 } }}
      >
        <SidebarContent />
      </Drawer>

      <AntLayout>
        {/* Header */}
        <Header className="px-4 bg-white border-b border-gray-200 flex items-center justify-between">
          <Space>
            {/* Mobile menu button */}
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setMobileMenuVisible(true)}
              className="md:hidden"
            />

            {/* Desktop collapse button */}
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed(!collapsed)}
              className="hidden md:block"
            />
          </Space>

          <Space>
            {/* User dropdown */}
            <Dropdown
              menu={{
                items: userMenuItems,
              }}
              placement="bottomRight"
            >
              <Button type="text" className="flex items-center space-x-2">
                <Avatar icon={<UserOutlined />} />
                <span className="hidden sm:block">{user?.username}</span>
                {user?.role === 'admin' && (
                  <Badge count="Admin" style={{ backgroundColor: '#667eea' }} />
                )}
              </Button>
            </Dropdown>
          </Space>
        </Header>

        {/* Main Content */}
        <Content className="p-6 bg-gray-50">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </Content>
      </AntLayout>
    </AntLayout>
  );
};

export default Layout;