
import AnalyzePage from "./AnalyzePage"

const Analyze = async () => {
    const res = await fetch("http://127.0.0.1:8000/trades/v1/tickers", {
        cache: "no-store" // always fresh data, no caching
    });
    const tickers = await res.json();
    return <div>
        <AnalyzePage tickers={tickers}/>
    </div>

}

export default Analyze