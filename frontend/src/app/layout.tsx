import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { AntdRegistry } from "@ant-design/nextjs-registry";
import { ConfigProvider } from "antd";
import { suppressAntdWarning } from "@/lib/antd-patch";
import "./globals.css";

// Apply Antd warning suppression as early as possible - before any other imports
suppressAntdWarning();

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
    <html lang="en">
      <body className={inter.className}>
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
      </body>
    </html>
  );
}
