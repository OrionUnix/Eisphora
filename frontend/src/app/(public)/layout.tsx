import Link from "next/link";

export default function PublicLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  console.log("Layout Base URL:", process.env.NEXT_PUBLIC_BASE_URL); // Debug

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      <header className="bg-blue-600 text-white p-4">
        <div className="container mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold">My App</h1>
          <nav>
            <Link href="/admin/login" className="text-white hover:underline">
              Admin Login
            </Link>
          </nav>
        </div>
      </header>
      <main className="flex-1 container mx-auto p-8">{children}</main>
      <footer className="bg-gray-800 text-white p-4 text-center">
        © 2025 My App
      </footer>
    </div>
  );
}