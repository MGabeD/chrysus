import { BarChart3, Table, Receipt, TrendingUp } from "lucide-react";
import { useUser } from "@/contexts/UserContext";

export const ViewModeSelector = () => {
  const { viewMode, setViewMode } = useUser();

  const modes = [
    { id: "aggregate" as const, label: "Aggregate Stats", icon: BarChart3 },
    { id: "transactions" as const, label: "Transactions", icon: Receipt },
    { id: "tables" as const, label: "Descriptive Tables", icon: Table },
    {
      id: "recommendations" as const,
      label: "Recommendations",
      icon: TrendingUp,
    },
  ];

  return (
    <div className="flex bg-gray-100 rounded-lg p-1">
      {modes.map(({ id, label, icon: Icon }) => (
        <button
          key={id}
          onClick={() => setViewMode(id)}
          className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${
            viewMode === id
              ? "bg-white text-blue-600 shadow-sm"
              : "text-gray-600 hover:text-gray-900"
          }`}
        >
          <Icon className="w-4 h-4" />
          {label}
        </button>
      ))}
    </div>
  );
};
