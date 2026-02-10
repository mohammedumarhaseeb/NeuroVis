import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Brain Tumor MRI Analysis',
  description: 'AI-powered brain tumor MRI analysis with genotype prediction',
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
