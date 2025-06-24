import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useUser } from "@/contexts/UserContext";
import {
  Loader2,
  TrendingUp,
  TrendingDown,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
} from "lucide-react";
import { buildApiUrl } from "@/lib/config";

interface Recommendation {
  recommendation: string;
  reasoning: string;
  strengths: string;
  weaknesses: string;
  evidence: string;
}

export const RecommendationsView = () => {
  const { selectedUser } = useUser();
  const [recommendation, setRecommendation] = useState<Recommendation | null>(
    null
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (selectedUser) {
      fetchRecommendations();
    }
  }, [selectedUser]);

  const fetchRecommendations = async () => {
    if (!selectedUser) return;

    setLoading(true);
    setError(null);
    try {
      const response = await fetch(
        buildApiUrl(`user/${selectedUser.name}/recommendations`)
      );
      if (response.ok) {
        const data = await response.json();
        setRecommendation(data);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || "Failed to fetch recommendations");
      }
    } catch (error) {
      console.error("Failed to fetch recommendations:", error);
      setError("Failed to fetch recommendations");
    } finally {
      setLoading(false);
    }
  };

  const getRecommendationIcon = (recommendation: string) => {
    const rec = recommendation.toLowerCase();
    if (rec.includes("accept"))
      return <CheckCircle className="w-6 h-6 text-green-600" />;
    if (rec.includes("reject"))
      return <XCircle className="w-6 h-6 text-red-600" />;
    if (rec.includes("defer"))
      return <Clock className="w-6 h-6 text-yellow-600" />;
    return <AlertCircle className="w-6 h-6 text-gray-600" />;
  };

  const getRecommendationColor = (recommendation: string) => {
    const rec = recommendation.toLowerCase();
    if (rec.includes("accept")) return "text-green-600";
    if (rec.includes("reject")) return "text-red-600";
    if (rec.includes("defer")) return "text-yellow-600";
    return "text-gray-600";
  };

  const getRecommendationBgColor = (recommendation: string) => {
    const rec = recommendation.toLowerCase();
    if (rec.includes("accept")) return "bg-green-50 border-green-200";
    if (rec.includes("reject")) return "bg-red-50 border-red-200";
    if (rec.includes("defer")) return "bg-yellow-50 border-yellow-200";
    return "bg-gray-50 border-gray-200";
  };

  const formatText = (text: string) => {
    return text.replace(/\n/g, "<br/>").replace(/\*\s+/g, "• ");
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <AlertCircle className="w-12 h-12 mx-auto mb-4 text-red-500" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Error Loading Recommendations
        </h3>
        <p className="text-gray-500 mb-4">{error}</p>
        <button
          onClick={fetchRecommendations}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          Try Again
        </button>
      </div>
    );
  }

  if (!recommendation) {
    return (
      <div className="text-center py-8">
        <AlertCircle className="w-12 h-12 mx-auto mb-4 text-gray-400" />
        <p className="text-gray-500">
          No recommendations available for this user.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Loan Recommendations</h2>
        <button
          onClick={fetchRecommendations}
          className="px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          Refresh
        </button>
      </div>

      {/* Recommendation Card */}
      <Card
        className={`border-2 ${getRecommendationBgColor(
          recommendation.recommendation
        )}`}
      >
        <CardHeader>
          <CardTitle className="flex items-center gap-3">
            {getRecommendationIcon(recommendation.recommendation)}
            <span
              className={getRecommendationColor(recommendation.recommendation)}
            >
              Loan Recommendation: {recommendation.recommendation}
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="prose max-w-none">
            <div
              className="whitespace-pre-wrap text-gray-700 leading-relaxed"
              dangerouslySetInnerHTML={{
                __html: formatText(recommendation.recommendation),
              }}
            />
          </div>
        </CardContent>
      </Card>

      {/* Reasoning Card */}
      {recommendation.reasoning && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertCircle className="w-5 h-5" />
              Reasoning
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div
              className="text-gray-700 leading-relaxed"
              dangerouslySetInnerHTML={{
                __html: formatText(recommendation.reasoning),
              }}
            />
          </CardContent>
        </Card>
      )}

      {/* Strengths Card */}
      {recommendation.strengths && (
        <Card className="border-green-200 bg-green-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-green-800">
              <CheckCircle className="w-5 h-5" />
              Financial Strengths
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div
              className="text-gray-700 leading-relaxed"
              dangerouslySetInnerHTML={{
                __html: formatText(recommendation.strengths),
              }}
            />
          </CardContent>
        </Card>
      )}

      {/* Weaknesses Card */}
      {recommendation.weaknesses && (
        <Card className="border-red-200 bg-red-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-red-800">
              <XCircle className="w-5 h-5" />
              Financial Weaknesses
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div
              className="text-gray-700 leading-relaxed"
              dangerouslySetInnerHTML={{
                __html: formatText(recommendation.weaknesses),
              }}
            />
          </CardContent>
        </Card>
      )}

      {/* Evidence Card */}
      {recommendation.evidence && (
        <Card className="border-blue-200 bg-blue-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-blue-800">
              <TrendingUp className="w-5 h-5" />
              Supporting Evidence
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div
              className="text-gray-700 leading-relaxed"
              dangerouslySetInnerHTML={{
                __html: formatText(recommendation.evidence),
              }}
            />
          </CardContent>
        </Card>
      )}

      {/* Additional Information */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            Analysis Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <TrendingUp className="w-8 h-8 mx-auto mb-2 text-blue-600" />
              <h4 className="font-semibold text-blue-900">Financial Health</h4>
              <p className="text-sm text-blue-700">
                Based on transaction patterns and account balances
              </p>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-600" />
              <h4 className="font-semibold text-green-900">Risk Assessment</h4>
              <p className="text-sm text-green-700">
                Evaluated using spending habits and income stability
              </p>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <AlertCircle className="w-8 h-8 mx-auto mb-2 text-purple-600" />
              <h4 className="font-semibold text-purple-900">Recommendation</h4>
              <p className="text-sm text-purple-700">
                AI-powered analysis of financial data
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
