import type { Metadata } from 'next'


// These styles apply to every route in the application
import './globals.css'
 
export const metadata: Metadata = {
  title: 'Eisphora - OpenSource',
  description: 'Eisphora Your fiscal data. Your rules. Our open-source code.',
}
 
export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}