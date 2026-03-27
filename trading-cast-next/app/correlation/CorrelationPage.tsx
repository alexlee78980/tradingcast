"use client"

import { useState } from "react"
import SearchList from "../analyze/SearchList"
import Correlation from "./Correlation"
interface CorrelationPageProps{
    items?:string[]
}
const CorrelationPage = ({items=[]}:CorrelationPageProps) => {
    const[data, setData] = useState<any>(null)
    const [loading, setLoading] = useState<boolean>(false)
    const getCorrelation = async(ticker:string) =>{
        console.log(ticker);
        setData(null)
        setLoading(true)
        const data  = await fetch(`http://127.0.0.1:8000/trades/v1/getCorrelation/${ticker}`)
        const result = await data.json()
        console.log(result)
        setLoading(false)
        setData(result)
    }
    return <div>
        <div className="w-50 m-10"><SearchList onSelect={getCorrelation} items={items}/></div>
        {loading && <div className="flex-1 flex items-center justify-center">
            <div className="w-10 h-10 border-4 border-gray-200 border-t-black rounded-full animate-spin"></div>
            </div>}
        {data &&<Correlation data={data}/>}

    </div>
}
export default CorrelationPage 