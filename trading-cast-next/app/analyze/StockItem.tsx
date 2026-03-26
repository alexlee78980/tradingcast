"use client"
import Button from "@/components/Button"
import { ReactElement } from "react"

interface StockItemProps{
    children:string,
    onClose:(stock:string)=>void
}


const StockItem:React.FC<StockItemProps> = ({children, onClose}) =>{
    const closeStock = () =>{
        onClose(children)
    }
    return <div className="w-full bg-black mt-4 flex place-content-between">
        <span className="text-white flex-1 flex items-center justify-center">{children}</span>
        <Button onClick={closeStock}>X</Button>
    </div>
}

export default StockItem