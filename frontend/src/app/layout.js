import { Kanit } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";
import TitleBar from "@/components/TitleBar";

const kanit = Kanit({ 
  subsets: ["thai", "latin"], 
  weight: ["300", "400", "700"] 
});

export const metadata = {
  title: "OCR Report Automation",
  description: "Advanced Network Infrastructure Reporting",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className={kanit.className} style={{ display: "flex", flexDirection: "column", height: "100vh", overflow: "hidden" }}>
        {/* Custom Discord-style title bar — always on top */}
        <TitleBar />

        {/* Main content area — scrollable */}
        <main style={{ flex: 1, overflowY: "auto" }}>
          {children}
        </main>

        <Toaster />
      </body>
    </html>
  );
}
