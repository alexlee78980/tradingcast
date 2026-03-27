import Image from "next/image";
import Card from "./Card";

export default function Home() {
  return (
    <div className="overflow-hidden w-full px-10">
   <div className="flex mt-20 overflow-x-auto gap-30 px-4 max-w-full w-full pb-4">
      <Card gifpath="/img/ChartDemo.gif" title="Chart" description="Visualize stock price history with technical indicators including Moving Average and RSI to identify market trends." path="/chart"></Card>
            <Card gifpath="/img/AnalyzeDemo.gif" title="Analyze" description="Analyze historical stock data and predict future price movements using machine learning. Add supporting stocks to improve model training and get detailed performance metrics including accuracy to help inform your buy or sell decisions." path="/analyze"></Card>
                  <Card gifpath="/img/DownloadDemo1.gif" title="Download" description="Download and export historical stock data to a CSV file for offline analysis and research." path="/download"></Card>
                    <Card gifpath="/img/CorrelationDemo.gif" title="Correlation" description="Measure how closely a stock's daily price changes move in sync with others to identify patterns and build a more diversified portfolio" path="/correlation"></Card>
    </div>
    </div>
  );
}
