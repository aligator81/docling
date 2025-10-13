'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Card, Input, Button, Typography, Avatar, Empty, Spin, Alert, Select, Tag } from 'antd';
import {
  SendOutlined,
  UserOutlined,
  RobotOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import { useRouter } from 'next/navigation';
import { AuthService } from '@/lib/auth';
import { api } from '@/lib/api';
import Layout from '@/components/ui/Layout';
import type { ChatMessage, User, Document } from '@/types';

const { Title, Text } = Typography;
const { TextArea } = Input;

interface Message extends ChatMessage {
  id: number;
  timestamp: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [user, setUser] = useState<User | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocuments, setSelectedDocuments] = useState<Document[]>([]);
  const [documentsLoading, setDocumentsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  useEffect(() => {
    // Check authentication
    if (!AuthService.isAuthenticated()) {
      router.push('/login');
      return;
    }

    // Load user and chat history
    loadUserAndHistory();
  }, [router]);

  useEffect(() => {
    // Scroll to bottom when new messages arrive
    scrollToBottom();
  }, [messages]);

  const loadUserAndHistory = async () => {
    try {
      setInitialLoading(true);
      const userData = AuthService.getUser();
      setUser(userData);

      if (!userData) {
        console.warn('No user data available');
        setInitialLoading(false);
        return;
      }

      // Load documents
      await loadDocuments();

    } catch (error) {
      console.error('Failed to load chat data:', error);
      // If authentication error, redirect to login
      if (error instanceof Error && error.message.includes('401')) {
        console.log('Authentication failed, redirecting to login');
        router.push('/login');
      }
    } finally {
      setInitialLoading(false);
    }
  };

  const loadDocuments = async () => {
    try {
      setDocumentsLoading(true);
      const documentsData = await api.getDocuments();
      setDocuments(documentsData);

      // Auto-select all processed documents if available
      const processedDocuments = documentsData.filter(doc => doc.status === 'processed');
      if (processedDocuments.length > 0) {
        setSelectedDocuments(processedDocuments);
      }
    } catch (error) {
      console.error('Failed to load documents:', error);
    } finally {
      setDocumentsLoading(false);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || loading || selectedDocuments.length === 0) return;

    const userMessage: Message = {
      id: Date.now(),
      message: inputMessage,
      isUser: true,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);

    try {
       const response = await api.sendChatMessage({
         message: inputMessage,
         document_ids: selectedDocuments.map(doc => doc.id),
       });

      const assistantMessage: Message = {
        id: Date.now() + 1,
        message: response.response,
        isUser: false,
        timestamp: new Date().toISOString(),
      };

      setMessages(prev => [...prev, assistantMessage]);


    } catch (error) {
      console.error('Failed to send message:', error);

      let errorMessageText = 'Sorry, I encountered an error processing your message. Please try again.';

      // Handle specific error types
      if (error instanceof Error) {
        console.log('Chat error details:', error.message);
        
        if (error.message.includes('401')) {
          errorMessageText = 'Your session has expired. Please refresh the page and log in again.';
        } else if (error.message.includes('503')) {
          errorMessageText = 'The AI service is currently unavailable. Please try again later.';
        } else if (error.message.includes('Network')) {
          errorMessageText = 'Network error. Please check your connection and try again.';
        } else if (error.message.includes('not found') || error.message.includes('404')) {
          errorMessageText = 'Some selected documents are not available. Please refresh the page and select documents again.';
        } else if (error.message.includes('LLM API keys not configured')) {
          errorMessageText = 'AI service is not configured. Please check API key settings.';
        } else if (error.message.includes('No LLM provider available')) {
          errorMessageText = 'No AI service provider is available. Please check configuration.';
        } else if (error.message.includes('not fully processed')) {
          errorMessageText = 'One or more documents are still processing. Please wait for processing to complete.';
        } else {
          // Show the actual error message for debugging
          errorMessageText = `Error: ${error.message}`;
        }
      }

      const errorMessage: Message = {
        id: Date.now() + 1,
        message: errorMessageText,
        isUser: false,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };


  return (
    <Layout>
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center">
          <Title level={2}>💬 Document Chat</Title>
          <Text type="secondary">
            Ask questions about your documents and get AI-powered answers
          </Text>
        </div>

        {/* Document Selection */}
        <Card className="shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <FileTextOutlined className="text-xl text-blue-500" />
              <div>
                <div className="font-medium">Select Documents to Chat With</div>
                <div className="text-sm text-gray-500">
                  {selectedDocuments.length > 0
                    ? `Chatting with: ${selectedDocuments.map(doc => doc.original_filename).join(', ')}`
                    : 'Please select processed documents to start chatting'
                  }
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              {selectedDocuments.length > 0 && (
                <div className="text-right">
                  <div className={`text-sm font-medium ${
                    selectedDocuments.every(doc => doc.status === 'processed') ? 'text-green-600' : 'text-yellow-600'
                  }`}>
                    Status: {selectedDocuments.every(doc => doc.status === 'processed') ? 'All Ready' : 'Processing'}
                  </div>
                  <div className="text-xs text-gray-500">
                    {selectedDocuments.length} document{selectedDocuments.length > 1 ? 's' : ''} selected
                  </div>
                </div>
              )}
              <Select
                placeholder="Select documents"
                mode="multiple"
                loading={documentsLoading}
                value={selectedDocuments.map(doc => doc.id).filter(id => id !== null && id !== undefined)}
                onChange={(values: number[]) => {
                  const validValues = values.filter(id => id !== null && id !== undefined);
                  const selectedDocs = documents.filter(d => validValues.includes(d.id));
                  setSelectedDocuments(selectedDocs);
                }}
                className="w-96"
                disabled={documentsLoading}
                maxTagCount={3}
              >
                {documents
                  .filter(doc => doc.status === 'processed')
                  .map(document => (
                    <Select.Option key={document.id} value={document.id}>
                      <div className="flex items-center justify-between w-full">
                        <span className="truncate">{document.original_filename}</span>
                        <Tag color="green" className="ml-2">Ready</Tag>
                      </div>
                    </Select.Option>
                  ))
                }
                {documents.filter(doc => doc.status === 'processed').length === 0 && (
                  <Select.Option disabled>
                    No processed documents available
                  </Select.Option>
                )}
              </Select>
            </div>
          </div>
        </Card>

        {/* Chat Interface */}
        <Card className="h-[600px] flex flex-col shadow-lg">
          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto mb-4 space-y-4">
            {initialLoading ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <Spin size="large" />
                  <div className="mt-4 text-gray-500">Loading chat...</div>
                </div>
              </div>
            ) : (
              <>
            {messages.length === 0 ? (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description={
                  <div className="text-center">
                    <Text className="text-lg">
                      {documents.length === 0 ? 'Upload and process documents first' : 'Select documents to start chatting'}
                    </Text>
                    <br />
                    <Text type="secondary">
                      {documents.length === 0
                        ? 'Upload documents from the Documents page and wait for processing to complete'
                        : 'Choose processed documents from the dropdown above to ask questions about them'
                      }
                    </Text>
                  </div>
                }
              />
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[70%] p-4 rounded-lg ${
                      message.isUser
                        ? 'bg-blue-500 text-white ml-12'
                        : 'bg-gray-100 text-gray-800 mr-12'
                    }`}
                  >
                    <div className="flex items-start space-x-3">
                      <Avatar
                        icon={message.isUser ? <UserOutlined /> : <RobotOutlined />}
                        size="small"
                        className={`flex-shrink-0 ${message.isUser ? 'bg-white text-blue-500' : 'bg-gray-200 text-gray-600'}`}
                      />
                      <div className="flex-1 min-w-0">
                        <div className={`break-words ${message.isUser ? 'text-white' : 'text-gray-800'}`}>
                          {message.message}
                        </div>
                        <div className={`text-xs mt-2 ${message.isUser ? 'text-blue-100' : 'text-gray-500'}`}>
                          {new Date(message.timestamp).toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 p-4 rounded-lg max-w-[70%] mr-12">
                  <div className="flex items-center space-x-3">
                    <Avatar
                      icon={<RobotOutlined />}
                      size="small"
                      className="bg-gray-200 text-gray-600"
                    />
                    <div className="flex items-center space-x-2">
                      <Spin size="small" />
                      <Text type="secondary">AI is thinking...</Text>
                    </div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
             </>
           )}
         </div>

          {/* Input Area */}
          <div className="border-t pt-4">
            <div className="flex space-x-3">
              <TextArea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={
                  selectedDocuments.length > 0
                    ? `Ask a question about ${selectedDocuments.length === 1 ? `"${selectedDocuments[0].original_filename}"` : `the selected documents`}...`
                    : "Please select processed documents to start chatting..."
                }
                autoSize={{ minRows: 1, maxRows: 4 }}
                className="flex-1 resize-none"
                disabled={loading || selectedDocuments.length === 0}
              />
              <Button
                type="primary"
                icon={<SendOutlined />}
                onClick={handleSendMessage}
                disabled={!inputMessage.trim() || loading || selectedDocuments.length === 0}
                loading={loading}
                size="large"
              >
                {loading ? 'Sending...' : 'Send'}
              </Button>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-between items-center mt-3">
              <div className="text-sm text-gray-500">
                💡 Tip: Ask specific questions about your selected documents
              </div>
            </div>
          </div>
        </Card>

      </div>
    </Layout>
  );
}