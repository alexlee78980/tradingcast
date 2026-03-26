"use client"
import Button from "@/components/Button"
import SearchBar from "@/components/SearchBar"
import { useState } from "react"
import StockItem from "./StockItem"
import StockItemMain from "./StockItemMain"
import SearchList from "./SearchList"
interface AnalyzePageProps{
    tickers: string[]
}
const AnalyzePage: React.FC<AnalyzePageProps> = ({tickers}) => {
    console.log(tickers)
    const [val, setVal] = useState<string>("")
    const [stocks, setStocks] = useState<string[]>([]);
    const [predict, setPredict] = useState<string>("")
    const [result, setResult] = useState<any>(null);
    const [loading, setLoading] = useState<boolean>(false)
    const changeVal = (e) => {
        setVal(e.target.value)

    }
    const addStock = () => {
        if (!val || !val.trim()) return;
        setStocks(prev => prev.includes(val) ? prev : [...prev, val]);
    };

    const addMain = () =>{
        if (!val || !val.trim()) return;
        setPredict(val)
    }

    const trainModel = async () => {
        if (stocks.length === 0) return;

        setLoading(true)
        const tickersParam = stocks.splice(1).join(',');
        const res = await fetch(`http://127.0.0.1:8000/trades/v1/analyze/${stocks[0]}?tickers=${tickersParam}`);
        const data = await res.json();
        console.log(data);
        setLoading(false)
        setResult(data)
}
    const removeStock = (val: string) => {
        setStocks(prev => prev.filter(s => s !== val));
    };

    const addSelection = (ticker:string) =>{
        if (!ticker || !ticker.trim()) return;
        setStocks(prev => prev.includes(ticker) ? prev : [...prev, ticker]);
    }
    return <div className="flex mt-20 justify-evenly pl-20" >
        <div className="flex flex-col"><div className="flex-1 flex items-center gap-2">
            <SearchList items={tickers} onSelect={addSelection}/>
            <Button onClick={addStock}>Add</Button>
            <Button
            
            
            onClick={addMain}>Add main</Button>
            <Button onClick={trainModel}>Train</Button>
        </div>
                  {stocks[0] && <StockItemMain>{stocks[0]}</StockItemMain>}
            <div className="rows gap-4 overflow-y-auto  mt-4 max-h-[calc(100vh-200px)]">
    
                {stocks.slice(1).map((item) => 
                    <StockItem key={item} onClose={removeStock}>
                        {item}
                    </StockItem>
                    )}

            </div>
        </div>
        <div className="flex-1">
           {loading && <div className="flex-1 flex items-center justify-center">
            <div className="w-10 h-10 border-4 border-gray-200 border-t-blue-500 rounded-full animate-spin"></div>
            </div>}
            {result && (
  <div className="flex-1 p-6 flex flex-col gap-4">
    {/* Prediction */}
    <div className="border rounded-md p-4">
      <h2 className="font-bold text-lg mb-2">Prediction for {result.target}</h2>
      <span className={`font-bold text-2xl ${
        result.prediction === "Buy" ? "text-green-500" :
        result.prediction === "Sell" ? "text-red-500" :
        "text-yellow-500"
      }`}>
        {result.prediction}
      </span>
    </div>

    {/* Probabilities */}
    <div className="border rounded-md p-4">
      <h2 className="font-bold mb-2">Probabilities</h2>
      {Object.entries(result.probabilities).map(([label, prob]) => (
        <div key={label} className="flex items-center gap-2 mb-2">
          <span className="w-16 text-sm">{label}</span>
          <div className="flex-1 bg-gray-200 rounded-full h-4">
            <div
              className={`h-4 rounded-full ${
                label === "Buy" ? "bg-green-500" :
                label === "Sell" ? "bg-red-500" :
                "bg-yellow-500"
              }`}
              style={{ width: `${(prob as number * 100).toFixed(1)}%` }}
            />
          </div>
          <span className="text-sm w-12">{((prob as number) * 100).toFixed(1)}%</span>
        </div>
      ))}
    </div>

    {/* Accuracy */}
    <div className="border rounded-md p-4">
      <h2 className="font-bold mb-2">Model Accuracy</h2>
      <span className="text-2xl">{(result.accuracy * 100).toFixed(1)}%</span>
    </div>

    {/* Report */}
    <div className="border rounded-md p-4">
      <h2 className="font-bold mb-2">Classification Report</h2>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left border-b">
            <th className="pb-2">Label</th>
            <th className="pb-2">Precision</th>
            <th className="pb-2">Recall</th>
            <th className="pb-2">F1</th>
          </tr>
        </thead>
        <tbody>
          {["Sell", "Neutral", "Buy"].map(label => (
            <tr key={label} className="border-b">
              <td className="py-1">{label}</td>
              <td>{(result.report[label].precision * 100).toFixed(1)}%</td>
              <td>{(result.report[label].recall * 100).toFixed(1)}%</td>
              <td>{(result.report[label]["f1-score"] * 100).toFixed(1)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>

  </div>
)}
        </div>
    </div>
}

export default AnalyzePage