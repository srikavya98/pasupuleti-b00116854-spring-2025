import { useState } from "react";
import axios from "axios";
import React from "react";


function App() {
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [sentiments, setSentiments] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const handleAnalyze = async () => {
    if (!youtubeUrl) return;
    setLoading(true);
    try {
      const response = await axios.post("http://localhost:3001/analyze", {
        url: youtubeUrl,
      });
      setSentiments(response.data.sentiments);
    } catch (error) {
      console.error("Error analyzing comments", error);
    }
    setLoading(false);
  };

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold mb-4">YouTube Comment Sentiment Analyzer</h1>
      <input
        className="border p-2 w-full mb-4"
        type="text"
        placeholder="Enter YouTube Video URL"
        value={youtubeUrl}
        onChange={(e) => setYoutubeUrl(e.target.value)}
      />
      <button
        className="bg-blue-500 text-white px-4 py-2 rounded"
        onClick={handleAnalyze}
        disabled={loading}
      >
        {loading ? "Analyzing..." : "Analyze Comments"}
      </button>

      <div className="mt-8">
        {sentiments.length > 0 && (
          <div>
            <h2 className="text-2xl font-semibold mb-2">Analysis Result:</h2>
            <ul className="space-y-2">
              {sentiments.map((item, idx) => (
                <li key={idx} className="border p-2 rounded">
                  <p><strong>Comment:</strong> {item.comment}</p>
                  <p><strong>Sentiment:</strong> {item.sentiment}</p>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
