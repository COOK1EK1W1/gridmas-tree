import "./globals.css";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full">
      <head>
        <script src="https://cdn.jsdelivr.net/pyodide/v0.23.4/full/pyodide.js"></script>
      </head>
      <body className={"fixed overflow-hidden h-[100dvh] w-full select-none"}>
        {children}
      </body>
    </html>
  );
}
