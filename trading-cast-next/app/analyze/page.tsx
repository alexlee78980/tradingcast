
import AnalyzePage from "./AnalyzePage"

const Analyze = async () => {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/trades/v1/tickers`, {
        cache: "no-store"
    });
    const tickers = await res.json();
    return <div>
        <AnalyzePage tickers={tickers}/>
    </div>

}

export default Analyze