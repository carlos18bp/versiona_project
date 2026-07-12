import type { Metadata } from 'next';
import './globals.css';
import Header from '@/components/layout/Header';
import Footer from '@/components/layout/Footer';
import StagingGate from '@/components/staging/StagingGate';
import { Toaster } from '@/components/ui/toast';
import Providers from './providers';

export const metadata: Metadata = {
  title: 'Versiona — El Git de tus documentos',
  description: 'Control de versiones, comparación y aprobación con sello para PDFs',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" suppressHydrationWarning>
      <body className="antialiased">
        <Providers>
          <StagingGate>
            <Header />
            {children}
            <Footer />
            <Toaster />
          </StagingGate>
        </Providers>
      </body>
    </html>
  );
}
