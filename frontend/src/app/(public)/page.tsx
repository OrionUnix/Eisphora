import Image from "next/image";
import Link from "next/link";

export default function LandingPage() {
  console.log("Base URL:", process.env.NEXT_PUBLIC_BASE_URL);

  return (
    <div className="text-center">
      <h2 className="text-4xl font-bold mb-8">Welcome to Our App!</h2>
      <p className="mb-4">
        Base URL: {process.env.NEXT_PUBLIC_BASE_URL || "Not defined"}
      </p>
      <Image
        className="mx-auto mb-8"
        src={`${process.env.NEXT_PUBLIC_BASE_URL}/icons/globe.svg`}
        alt="Globe icon"
        width={100}
        height={100}
      />
      <p className="text-lg mb-8">
        Discover our amazing features and join us today!
      </p>
      <div className="flex gap-4 justify-center">
        <Link
          href="/admin/login"
          className="rounded-full bg-blue-600 text-white py-2 px-4 hover:bg-blue-700"
        >
          Get Started
        </Link>
        <Link
          href="https://nextjs.org/docs"
          className="rounded-full border border-gray-300 py-2 px-4 hover:bg-gray-100"
          target="_blank"
          rel="noopener noreferrer"
        >
          Read Docs
        </Link>
      </div>
    </div>
  );
}