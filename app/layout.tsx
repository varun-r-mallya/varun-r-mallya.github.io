import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import {NavBar} from "../components/Navbar";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Varun R Mallya's Portfolio",
  description: "I showcase my projects and blog about my experiences here.",
};


export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-black-800`}>
        <NavBar />
        {children}
      </body>
    </html>
  );
}
