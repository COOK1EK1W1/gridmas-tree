import "./globals.css";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full">
      <body className={"fixed overflow-hidden h-[100dvh] w-full select-none"}>
        {children}
      </body>
    </html>
  );
}
