import { useState } from "react";
import axios from "axios";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip,
  PieChart, Pie, Cell, Legend, ResponsiveContainer
} from "recharts";
import './index.css';

// Define the structure of a single sentiment item
type SentimentItem = {
  comment: string;
  sentiment: "Positive" | "Neutral" | "Negative";
};

const COLORS = ["#34d399", "#fbbf24", "#f87171"];

export default function App() {
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [sentiments, setSentiments] = useState<SentimentItem[]>([]);
  const [allSentiments, setAllSentiments] = useState<SentimentItem["sentiment"][]>([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [limit] = useState(10);
  const [totalComments, setTotalComments] = useState(0);

  const fetchComments = async (url: string, currentPage: number) => {
    setLoading(true);
    try {
      const res = await axios.post(
        `http://localhost:3001/analyze?page=${currentPage}&limit=${limit}`,
        { url }
      );
      setSentiments(res.data.sentiments);
      setAllSentiments(res.data.all_sentiments);
      setTotalComments(res.data.total_fetched);
    } catch (err) {
      console.error("Fetch error", err);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = () => {
    if (!youtubeUrl) return;
    setPage(1);
    fetchComments(youtubeUrl, 1);
  };

  const totalPages = Math.ceil(totalComments / limit);

  const sentimentCount = {
    Positive: 0,
    Neutral: 0,
    Negative: 0
  };
  allSentiments.forEach(s => sentimentCount[s]++);

  const chartData = [
    { name: "Positive", value: sentimentCount.Positive },
    { name: "Neutral", value: sentimentCount.Neutral },
    { name: "Negative", value: sentimentCount.Negative }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-white py-12 px-6">
      <div className="max-w-5xl mx-auto bg-white p-8 rounded-2xl shadow-xl">
        <h1 className="text-4xl font-bold text-center mb-6 text-blue-700">
          YouTube Comment Sentiment Analyzer
        </h1>
        <div className="flex gap-4 mb-6 flex-col md:flex-row">
          <input
            className="flex-1 border border-blue-300 p-3 rounded-lg shadow-sm"
            type="text"
            placeholder="Paste YouTube video URL here..."
            value={youtubeUrl}
            onChange={(e) => setYoutubeUrl(e.target.value)}
          />
          <button
            onClick={handleAnalyze}
            disabled={loading}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition"
          >
            {loading ? "Analyzing..." : "Analyze"}
          </button>
        </div>

        {sentiments.length > 0 && (
          <>
            <div className="grid md:grid-cols-2 gap-6 mb-10">
              <div className="bg-blue-50 p-4 rounded-lg shadow-inner">
                <h2 className="text-xl font-semibold text-blue-600 mb-2 text-center">Histogram</h2>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={chartData}>
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value">
                      {chartData.map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="bg-blue-50 p-4 rounded-lg shadow-inner">
                <h2 className="text-xl font-semibold text-blue-600 mb-2 text-center">Pie Chart</h2>
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={chartData}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      label
                    >
                      {chartData.map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="bg-gray-50 p-4 rounded-lg shadow max-h-[300px] overflow-y-auto">
              <ul className="space-y-3">
                {sentiments.map((item, idx) => (
                  <li key={idx} className="p-4 bg-white rounded-lg shadow-sm border">
                    <p className="text-gray-800"><strong>Comment:</strong> {item.comment}</p>
                    <p className="text-sm text-blue-600 mt-1"><strong>Sentiment:</strong> {item.sentiment}</p>
                  </li>
                ))}
              </ul>
            </div>

            <div className="mt-6 flex justify-between items-center">
              <button
                onClick={() => {
                  const prev = Math.max(page - 1, 1);
                  setPage(prev);
                  fetchComments(youtubeUrl, prev);
                }}
                disabled={page === 1}
                className="px-4 py-2 bg-gray-300 rounded hover:bg-gray-400 disabled:opacity-50"
              >
                Previous
              </button>
              <span className="text-blue-600 font-semibold">Page {page} of {totalPages}</span>
              <button
                onClick={() => {
                  const next = Math.min(page + 1, totalPages);
                  setPage(next);
                  fetchComments(youtubeUrl, next);
                }}
                disabled={page >= totalPages}
                className="px-4 py-2 bg-gray-300 rounded hover:bg-gray-400 disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
