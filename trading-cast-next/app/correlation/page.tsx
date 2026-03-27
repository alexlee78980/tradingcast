import CorrelationPage from "./CorrelationPage"


const Correlation = async() =>{
    const data = await fetch("http://127.0.0.1:8000/trades/v1/tickers", {
        cache:"no-store"
    })
    const result = await data.json()
    console.log(result)
    return <div>
        {result && <CorrelationPage items={result}></CorrelationPage>}</div>
}

export default Correlation