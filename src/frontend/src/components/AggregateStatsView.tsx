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
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { useUser } from "@/contexts/UserContext";
import {
  Loader2,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Filter,
  Download,
  FileText,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { buildApiUrl } from "@/lib/config";

interface TagData {
  tag: string;
  mean: number;
  max: number;
  min: number;
  sum: number;
  std: number;
  count: number;
}

interface FrequentDescription {
  description: string;
  mean: number;
  max: number;
  min: number;
  sum: number;
  std: number;
  count: number;
}

interface MonthlyData {
  month: string;
  mean: number;
  max: number;
  min: number;
  sum: number;
  std: number;
  count: number;
}

interface WeeklyData {
  week: string;
  mean: number;
  max: number;
  min: number;
  sum: number;
  std: number;
  count: number;
}

interface BaseInsights {
  frequent_descriptions: FrequentDescription[];
  tags: TagData[];
  monthly: MonthlyData[];
  weekly: WeeklyData[];
}

export const AggregateStatsView = () => {
  const { selectedUser } = useUser();
  const [data, setData] = useState<BaseInsights | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (selectedUser) {
      fetchBaseInsights();
    }
  }, [selectedUser]);

  const fetchBaseInsights = async () => {
    if (!selectedUser) return;

    setLoading(true);
    try {
      const response = await fetch(
        buildApiUrl(`user/${selectedUser.name}/base_insights`)
      );
      if (response.ok) {
        const insights = await response.json();
        setData(insights);
      }
    } catch (error) {
      console.error("Failed to fetch base insights:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500">
          No aggregate data available for this user.
        </p>
      </div>
    );
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
    }).format(value);
  };

  const totalSum = data.tags.reduce((acc, tag) => acc + tag.sum, 0);
  const positiveSum = data.tags
    .filter((tag) => tag.sum > 0)
    .reduce((acc, tag) => acc + tag.sum, 0);
  const negativeSum = data.tags
    .filter((tag) => tag.sum < 0)
    .reduce((acc, tag) => acc + tag.sum, 0);

  // Pie chart data for spending categories
  const pieData = data.tags
    .filter((tag) => tag.sum < 0)
    .map((tag) => ({ name: tag.tag, value: Math.abs(tag.sum) }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 8);

  const COLORS = [
    "#0088FE",
    "#00C49F",
    "#FFBB28",
    "#FF8042",
    "#8884D8",
    "#82CA9D",
    "#FFC658",
    "#FF6B6B",
  ];

  return (
    <div className="space-y-6">
      {/* Enhanced Header with Actions */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Financial Analysis</h2>
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <Filter className="w-4 h-4 mr-2" />
            Filter
          </Button>
          <Button variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Balance</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(totalSum)}</div>
            <p className="text-xs text-muted-foreground">
              All transactions combined
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Income</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {formatCurrency(positiveSum)}
            </div>
            <p className="text-xs text-muted-foreground">
              Positive transactions
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Total Expenses
            </CardTitle>
            <TrendingDown className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {formatCurrency(negativeSum)}
            </div>
            <p className="text-xs text-muted-foreground">
              Negative transactions
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Enhanced Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Spending by Category Bar Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Spending by Category</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={data.tags}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="tag"
                  angle={-45}
                  textAnchor="end"
                  height={80}
                  fontSize={12}
                />
                <YAxis tickFormatter={(value) => formatCurrency(value)} />
                <Tooltip
                  formatter={(value: number) => [formatCurrency(value), "Sum"]}
                />
                <Bar dataKey="sum" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Spending Distribution Pie Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Expense Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) =>
                    `${name} ${(percent * 100).toFixed(0)}%`
                  }
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={COLORS[index % COLORS.length]}
                    />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value: number) => [
                    formatCurrency(value),
                    "Amount",
                  ]}
                />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Monthly Trend */}
      <Card>
        <CardHeader>
          <CardTitle>Monthly Trend</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data.monthly}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis tickFormatter={(value) => formatCurrency(value)} />
              <Tooltip
                formatter={(value: number) => [formatCurrency(value), "Sum"]}
              />
              <Line
                type="monotone"
                dataKey="sum"
                stroke="#3b82f6"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
      {/* Frequent Descriptions */}
      {data.frequent_descriptions && data.frequent_descriptions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Frequent Transaction Descriptions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {data.frequent_descriptions.map((item, index) => (
                <div key={index} className="p-4 bg-gray-50 rounded-lg border">
                  <div className="flex justify-between items-start mb-2">
                    <h4 className="font-medium text-sm text-gray-900">
                      {item.description}
                    </h4>
                    <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                      {item.count} transactions
                    </span>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                    <div>
                      <span className="text-gray-500">Total:</span>
                      <div
                        className={`font-medium ${
                          item.sum >= 0 ? "text-green-600" : "text-red-600"
                        }`}
                      >
                        {formatCurrency(item.sum)}
                      </div>
                    </div>
                    <div>
                      <span className="text-gray-500">Average:</span>
                      <div className="font-medium">
                        {formatCurrency(item.mean)}
                      </div>
                    </div>
                    <div>
                      <span className="text-gray-500">Min:</span>
                      <div className="font-medium">
                        {formatCurrency(item.min)}
                      </div>
                    </div>
                    <div>
                      <span className="text-gray-500">Max:</span>
                      <div className="font-medium">
                        {formatCurrency(item.max)}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
      {/* Enhanced Tag Statistics Table */}
      <Card>
        <CardHeader>
          <CardTitle>Category Statistics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-3">Category</th>
                  <th className="text-right p-3">Count</th>
                  <th className="text-right p-3">Total</th>
                  <th className="text-right p-3">Average</th>
                  <th className="text-right p-3">Min</th>
                  <th className="text-right p-3">Max</th>
                  <th className="text-right p-3">Std Dev</th>
                </tr>
              </thead>
              <tbody>
                {data.tags.map((tag) => (
                  <tr key={tag.tag} className="border-b hover:bg-gray-50">
                    <td className="p-3 font-medium">{tag.tag}</td>
                    <td className="p-3 text-right">{tag.count}</td>
                    <td
                      className={`p-3 text-right font-medium ${
                        tag.sum >= 0 ? "text-green-600" : "text-red-600"
                      }`}
                    >
                      {formatCurrency(tag.sum)}
                    </td>
                    <td className="p-3 text-right">
                      {formatCurrency(tag.mean)}
                    </td>
                    <td className="p-3 text-right">
                      {formatCurrency(tag.min)}
                    </td>
                    <td className="p-3 text-right">
                      {formatCurrency(tag.max)}
                    </td>
                    <td className="p-3 text-right">
                      {isNaN(tag.std) ? "-" : formatCurrency(tag.std)}
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
