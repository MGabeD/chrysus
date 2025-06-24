import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useUser } from "@/contexts/UserContext";
import { Loader2, Table, Download, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { buildApiUrl } from "@/lib/config";

type TableData = Record<string, any>;

interface DescriptiveTable {
  title: string;
  data: TableData[];
}

export const DescriptiveTablesView = () => {
  const { selectedUser } = useUser();
  const [tables, setTables] = useState<DescriptiveTable[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (selectedUser) {
      fetchDescriptiveTables();
    }
  }, [selectedUser]);

  const fetchDescriptiveTables = async () => {
    if (!selectedUser) return;

    setLoading(true);
    try {
      const response = await fetch(
        buildApiUrl(`user/${selectedUser.name}/descriptive_tables`)
      );
      if (response.ok) {
        const data = await response.json();
        setTables(data);
      }
    } catch (error) {
      console.error("Failed to fetch descriptive tables:", error);
    } finally {
      setLoading(false);
    }
  };

  const formatCellValue = (value: any) => {
    if (value === null || value === undefined) {
      return "-";
    }
    if (typeof value === "string" && value.startsWith("$")) {
      return value;
    }
    return String(value);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  if (tables.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500">
          No descriptive tables available for this user.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Enhanced Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Descriptive Tables</h2>
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <Search className="w-4 h-4 mr-2" />
            Search
          </Button>
          <Button variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {tables.map((table, tableIndex) => {
        if (!table.data || table.data.length === 0) return null;

        // Get all unique keys from the table data to create headers
        const headers = Object.keys(table.data[0]);

        return (
          <Card key={tableIndex}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Table className="w-5 h-5" />
                {table.title}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      {headers.map((header) => (
                        <th
                          key={header}
                          className="text-left p-3 font-medium capitalize"
                        >
                          {header.replace(/_/g, " ")}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {table.data.map((row, rowIndex) => (
                      <tr key={rowIndex} className="border-b hover:bg-gray-50">
                        {headers.map((header) => (
                          <td key={header} className="p-3">
                            {formatCellValue(row[header])}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
};
