import Link from "next/link";
import Footer from "@elements/Footer";
import { seoConfig } from '@seoConfig';


export default function PublicLayout({
  children,
}: {
  children: React.ReactNode;
}) {
console.log("Footer is:", Footer);

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-blue-600 text-white p-4">
        <div className="container mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold">{seoConfig.siteName}</h1>
          <nav>
            <Link href="/admin/login" className="text-white hover:underline">
              Admin Login
            </Link>
          </nav>
        </div>
      </header>
<main className="flex-1">{children}</main>

     <Footer />
    </div>
  );
}