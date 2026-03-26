"use client"
import Button from "@/components/Button"
import { ReactElement } from "react"

interface StockItemMainProps{
    children:string,
}


const StockItemMain:React.FC<StockItemMainProps> = ({children}) =>{
  
    return <div className="w-full b-1 mt-4 flex place-content-between border-2 min-h-12">
        <span className="text-black flex-1 flex items-center justify-center font-bold">➡ {children}</span>
    </div>
}

export default StockItemMain