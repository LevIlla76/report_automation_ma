import { Kanit } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";

const kanit = Kanit({ 
  subsets: ["thai", "latin"], 
  weight: ["300", "400", "700"] 
});

export const metadata = {
  title: "Report Automation",
  description: "Advanced Network Infrastructure Reporting",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className={kanit.className}>
        {children}
        <Toaster />
      </body>
    </html>
  );
}
