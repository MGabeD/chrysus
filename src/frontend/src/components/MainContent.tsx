
import { ViewModeSelector } from './ViewModeSelector';
import { AggregateStatsView } from './AggregateStatsView';
import { TransactionView } from './TransactionView';
import { DescriptiveTablesView } from './DescriptiveTablesView';
import { useUser } from '@/contexts/UserContext';

export const MainContent = () => {
  const { selectedUser, viewMode } = useUser();

  if (!selectedUser) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 bg-gray-200 rounded-full flex items-center justify-center">
            <span className="text-2xl text-gray-400">👤</span>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Select a User</h2>
          <p className="text-gray-500">Choose a user from the sidebar to view their financial data.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col">
      <div className="bg-white border-b border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{selectedUser.name}</h1>
            <p className="text-gray-500">Financial Overview</p>
          </div>
          <ViewModeSelector />
        </div>
      </div>
      
      <div className="flex-1 p-6">
        {viewMode === 'aggregate' && <AggregateStatsView />}
        {viewMode === 'transactions' && <TransactionView />}
        {viewMode === 'tables' && <DescriptiveTablesView />}
      </div>
    </div>
  );
};
