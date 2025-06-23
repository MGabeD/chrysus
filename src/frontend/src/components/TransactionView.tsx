import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { useUser } from "@/contexts/UserContext";
import { Loader2, Calendar, Receipt, Search, Filter } from "lucide-react";
import { Button } from "@/components/ui/button";
import { buildApiUrl } from "@/lib/config";

interface Transaction {
  date: string;
  description: string;
  transaction_amount: number;
  balance: number;
  tag: string;
}

export const TransactionView = () => {
  const { selectedUser } = useUser();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    if (selectedUser) {
      fetchTransactions();
    }
  }, [selectedUser]);

  const fetchTransactions = async () => {
    if (!selectedUser) return;

    setLoading(true);
    try {
      const response = await fetch(
        buildApiUrl(`user/${selectedUser.name}/transaction_table`)
      );
      if (response.ok) {
        const data = await response.json();
        setTransactions(data);
      }
    } catch (error) {
      console.error("Failed to fetch transactions:", error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
    }).format(value);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const groupTransactionsByDay = () => {
    const grouped = transactions.reduce((acc, transaction) => {
      const date = transaction.date.split(" ")[0]; // Get just the date part

      if (!acc[date]) {
        acc[date] = { date, positive: 0, negative: 0, tags: new Set() };
      }

      if (transaction.transaction_amount > 0) {
        acc[date].positive += transaction.transaction_amount;
      } else {
        acc[date].negative += Math.abs(transaction.transaction_amount);
      }

      acc[date].tags.add(transaction.tag);

      return acc;
    }, {} as Record<string, { date: string; positive: number; negative: number; tags: Set<string> }>);

    return Object.values(grouped)
      .map((item) => ({
        ...item,
        tags: Array.from(item.tags),
        negative: -item.negative, // Make negative for chart display
      }))
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  };

  const filteredTransactions = transactions.filter(
    (transaction) =>
      transaction.description
        .toLowerCase()
        .includes(searchTerm.toLowerCase()) ||
      transaction.tag.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const chartData = groupTransactionsByDay();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  if (transactions.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500">
          No transaction data available for this user.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Enhanced Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Transaction Analysis</h2>
        <div className="flex gap-2">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search transactions..."
              className="pl-10 pr-4 py-2 border rounded-md text-sm"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <Button variant="outline" size="sm">
            <Filter className="w-4 h-4 mr-2" />
            Filter
          </Button>
        </div>
      </div>

      {/* Transaction Flow Visualization */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            Daily Transaction Flow
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart
              data={chartData}
              margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                tickFormatter={(value) => new Date(value).toLocaleDateString()}
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis
                tickFormatter={(value) => formatCurrency(Math.abs(value))}
              />
              <Tooltip
                formatter={(value: number, name: string) => [
                  formatCurrency(Math.abs(value)),
                  name === "positive" ? "Income" : "Expenses",
                ]}
                labelFormatter={(value) =>
                  `Date: ${new Date(value).toLocaleDateString()}`
                }
              />
              <ReferenceLine y={0} stroke="#666" />
              <Bar dataKey="positive" fill="#10b981" name="Income" />
              <Bar dataKey="negative" fill="#ef4444" name="Expenses" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Enhanced Transaction Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Receipt className="w-5 h-5" />
            Transaction History ({filteredTransactions.length} transactions)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-3">Date</th>
                  <th className="text-left p-3">Description</th>
                  <th className="text-left p-3">Category</th>
                  <th className="text-right p-3">Amount</th>
                  <th className="text-right p-3">Balance</th>
                </tr>
              </thead>
              <tbody>
                {filteredTransactions.map((transaction, index) => (
                  <tr key={index} className="border-b hover:bg-gray-50">
                    <td className="p-3">{formatDate(transaction.date)}</td>
                    <td
                      className="p-3 max-w-xs truncate"
                      title={transaction.description}
                    >
                      {transaction.description}
                    </td>
                    <td className="p-3">
                      <span className="inline-block px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
                        {transaction.tag}
                      </span>
                    </td>
                    <td
                      className={`p-3 text-right font-medium ${
                        transaction.transaction_amount >= 0
                          ? "text-green-600"
                          : "text-red-600"
                      }`}
                    >
                      {formatCurrency(transaction.transaction_amount)}
                    </td>
                    <td className="p-3 text-right font-medium">
                      {formatCurrency(transaction.balance)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
