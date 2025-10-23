
'use client';

import React, { useState, useEffect, useRef, Suspense } from 'react';
import { Card, Input, Button, Typography, Avatar, Empty, Spin, Alert, Select, Tag, Dropdown, Modal } from 'antd';
import {
  SendOutlined,
  UserOutlined,
  RobotOutlined,
  FileTextOutlined,
  SwapOutlined,
  DownOutlined,
} from '@ant-design/icons';
import { useRouter, useSearchParams } from 'next/navigation';
import { AuthService } from '@/lib/auth';
import { api } from '@/lib/api';
import Layout from '@/components/ui/Layout';
import type { ChatMessage, User, Document, ReferenceDetail } from '@/types';

const { Title, Text } = Typography;
const { TextArea } = Input;

interface Message extends ChatMessage {
  id: number;
  timestamp: string;
  references?: ReferenceDetail[];
}

// Create a separate component that uses useSearchParams
function ChatContent() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [user, setUser] = useState<User | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocuments, setSelectedDocuments] = useState<Document[]>([]);
  const [documentsLoading, setDocumentsLoading] = useState(false);
  const [reportModalOpen, setReportModalOpen] = useState(false);
  const [reportText, setReportText] = useState('');
  const [visibleSources, setVisibleSources] = useState<Set<number>>(new Set());
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const searchParams = useSearchParams();

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

      // Check if a specific document ID is provided in the query params
      const documentIdParam = searchParams.get('documentId');
      if (documentIdParam) {
        const documentId = parseInt(documentIdParam, 10);
        const specificDocument = documentsData.find(doc => doc.id === documentId && doc.status === 'processed');
        if (specificDocument) {
          setSelectedDocuments([specificDocument]);
        }
      }
      // No auto-selection by default
    } catch (error) {
      console.error('Failed to load documents:', error);
    } finally {
      setDocumentsLoading(false);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || loading || selectedDocuments.length === 0) return;

    // Check if all selected documents are processed
    const unprocessedDocuments = selectedDocuments.filter(doc => doc.status !== 'processed');
    if (unprocessedDocuments.length > 0) {
      const errorMessage: Message = {
        id: Date.now() + 1,
        message: `Some documents are still processing: ${unprocessedDocuments.map(doc => doc.original_filename).join(', ')}. Please wait for processing to complete.`,
        isUser: false,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMessage]);
      return;
    }

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
        context_docs: response.context_docs,
        model_used: response.model_used,
        references: response.references,
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
                    ? selectedDocuments.length === 1
                      ? `Chatting with: ${selectedDocuments[0].original_filename}`
                      : `Chatting with ${selectedDocuments.length} documents`
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
              
              {/* Document Switching */}
              {documents.filter(doc => doc.status === 'processed').length > 1 && (
                <Dropdown
                  menu={{
                    items: documents
                      .filter(doc => doc.status === 'processed')
                      .map(doc => ({
                        key: doc.id,
                        label: (
                          <div
                            className="flex items-center justify-between w-full"
                            onClick={() => {
                              if (selectedDocuments.some(selected => selected.id === doc.id)) {
                                // Remove document if already selected
                                setSelectedDocuments(prev => prev.filter(d => d.id !== doc.id));
                              } else {
                                // Add document if not selected
                                setSelectedDocuments(prev => [...prev, doc]);
                              }
                            }}
                          >
                            <span className="truncate">{doc.original_filename}</span>
                            {selectedDocuments.some(selected => selected.id === doc.id) && (
                              <span className="text-green-500 ml-2">✓</span>
                            )}
                          </div>
                        ),
                      })),
                  }}
                  placement="bottomRight"
                >
                  <Button icon={<SwapOutlined />} size="small">
                    Quick Switch
                  </Button>
                </Dropdown>
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
                maxTagCount={2}
                maxTagPlaceholder={(omittedValues) => `+${omittedValues.length} more...`}
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
          
          {/* Selected Documents Badges */}
          {selectedDocuments.length > 0 && (
            <div className="mt-4 pt-4 border-t">
              <div className="flex flex-wrap gap-2">
                {selectedDocuments.map((doc, index) => (
                  <Tag
                    key={doc.id}
                    color={doc.status === 'processed' ? 'blue' : 'orange'}
                    closable
                    onClose={() => {
                      const newSelected = selectedDocuments.filter(d => d.id !== doc.id);
                      setSelectedDocuments(newSelected);
                    }}
                    className="flex items-center gap-1"
                  >
                    <FileTextOutlined className="text-xs" />
                    <span className="max-w-[200px] truncate">{doc.original_filename}</span>
                    {doc.status === 'processed' ? (
                      <span className="text-green-600">✓</span>
                    ) : (
                      <span className="text-orange-600">⏳</span>
                    )}
                  </Tag>
                ))}
              </div>
            </div>
          )}
        </Card>

        {/* Chat Interface */}
        <Card className="h-[calc(100vh-200px)] min-h-[400px] flex flex-col shadow-lg">
          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto mb-4 space-y-4" style={{ scrollBehavior: 'smooth', maxHeight: 'calc(100vh - 300px)' }}>
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
                        
                        {/* Collapsible source information */}
                        {!message.isUser && ((message.references && message.references.length > 0) || (selectedDocuments.length > 1 && message.context_docs && message.context_docs.length > 0)) && (
                          <div className="mt-2 pt-2 border-t border-gray-200">
                            <Button size="small" type="link" onClick={() => {
                              setVisibleSources(prev => {
                                const newSet = new Set(prev);
                                if (newSet.has(message.id)) {
                                  newSet.delete(message.id);
                                } else {
                                  newSet.add(message.id);
                                }
                                return newSet;
                              });
                            }}>
                              <DownOutlined className={`transition-transform ${visibleSources.has(message.id) ? 'rotate-180' : ''}`} />
                              Source Details
                            </Button>
                            {visibleSources.has(message.id) && (
                              <div className="mt-2 text-xs text-gray-500 transition-all duration-300">
                                {selectedDocuments.length > 1 && message.context_docs && message.context_docs.length > 0 && (
                                  <div>
                                    Sources: {selectedDocuments
                                      .filter(doc => message.context_docs?.includes(doc.id))
                                      .map(doc => doc.original_filename)
                                      .join(', ')}
                                  </div>
                                )}
                                {message.references && message.references.length > 0 && (
                                  <div className="mt-1">
                                    <div className="font-medium mb-1">Detailed Source Details:</div>
                                    {message.references.map((ref, index) => (
                                      <div key={index} className="ml-2 mb-1">
                                        <div className="flex items-center">
                                          <span className="font-medium">{ref.filename}</span>
                                          {ref.page_numbers && ref.page_numbers !== "N/A" && (
                                            <span className="ml-2 text-blue-600">(Page {ref.page_numbers})</span>
                                          )}
                                        </div>
                                        {ref.section_title && (
                                          <div className="text-gray-600 italic">Section: {ref.section_title}</div>
                                        )}
                                      </div>
                                    ))}
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        )}
                        
                        <div className={`text-xs mt-2 ${message.isUser ? 'text-blue-100' : 'text-gray-500'}`}>
                          {new Date(message.timestamp).toLocaleTimeString()}
                          {!message.isUser && message.model_used && (
                            <span className="ml-2">• {message.model_used}</span>
                          )}
                        </div>
                        {!message.isUser && (
                          <div className="mt-1">
                            <Button size="small" type="link" onClick={() => setReportModalOpen(true)}>
                              Report Error
                            </Button>
                          </div>
                        )}
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
          </div>
        </Card>
      </div>
      <Modal
        title="Report Error"
        open={reportModalOpen}
        onOk={() => {
          // Handle report - for now, just log
          console.log('Report submitted:', reportText);
          setReportModalOpen(false);
          setReportText('');
        }}
        onCancel={() => {
          setReportModalOpen(false);
          setReportText('');
        }}
      >
        <div className="mb-4">
          <Text>Describe the error in the AI response or provide the correct information:</Text>
        </div>
        <TextArea
          placeholder="Enter your correction or description of the error..."
          value={reportText}
          onChange={(e) => setReportText(e.target.value)}
          rows={4}
        />
      </Modal>
    </Layout>
  );
}

// Main chat page component with Suspense boundary
export default function ChatPage() {
  return (
    <Suspense fallback={
      <Layout>
        <div className="max-w-6xl mx-auto space-y-6">
          <div className="text-center">
            <Title level={2}>💬 Document Chat</Title>
            <Text type="secondary">
              Ask questions about your documents and get AI-powered answers
            </Text>
          </div>
          <Card className="h-[600px] flex items-center justify-center">
            <div className="text-center">
              <Spin size="large" />
              <div className="mt-4 text-gray-500">Loading chat interface...</div>
            </div>
          </Card>
        </div>
      </Layout>
    }>
      <ChatContent />
    </Suspense>
  );
}