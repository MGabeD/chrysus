import { PdfUpload } from "./PdfUpload";
import { UserList } from "./UserList";

export const Sidebar = () => {
  return (
    <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
      <div className="p-6 border-b border-gray-200">
        <h1 className="text-2xl font-bold text-gray-900">Chrysus Dashboard</h1>
      </div>

      <div className="p-6 border-b border-gray-200">
        <PdfUpload />
      </div>

      <div className="flex-1 p-6">
        <UserList />
      </div>
    </div>
  );
};
