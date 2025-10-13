import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { AntdRegistry } from "@ant-design/nextjs-registry";
import { ConfigProvider } from "antd";
import "./globals.css";
import AntdPatchProvider from "@/components/AntdPatchProvider";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Document Q&A Assistant",
  description: "Enterprise Document Q&A System with AI-powered search and chat",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className} suppressHydrationWarning>
        <AntdPatchProvider>
          <ConfigProvider
            theme={{
              token: {
                colorPrimary: "#667eea",
                borderRadius: 8,
                fontFamily: inter.style.fontFamily,
              },
              components: {
                Layout: {
                  headerBg: "#667eea",
                  siderBg: "#f8f9fa",
                },
                Menu: {
                  itemBg: "transparent",
                  subMenuItemBg: "transparent",
                },
              },
            }}
          >
            <AntdRegistry>
              {children}
            </AntdRegistry>
          </ConfigProvider>
        </AntdPatchProvider>
      </body>
    </html>
  );
}
