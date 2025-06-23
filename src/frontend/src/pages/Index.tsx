
import { useState } from 'react';
import { Sidebar } from '@/components/Sidebar';
import { MainContent } from '@/components/MainContent';
import { UserProvider } from '@/contexts/UserContext';

const Index = () => {
  return (
    <UserProvider>
      <div className="min-h-screen bg-gray-50 flex">
        <Sidebar />
        <MainContent />
      </div>
    </UserProvider>
  );
};

export default Index;
