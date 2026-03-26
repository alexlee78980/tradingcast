"use client"
import { useState } from "react"
interface SearchListProps{
    items:string[];
    onSelect:(ticker:string)=>void;
}
const SearchList:React.FC<SearchListProps> = ({ items, onSelect }) => {
    const [query, setQuery] = useState("")

    const filtered = items.filter(item =>
        item.toLowerCase().includes(query.toLowerCase())
    )
    const clickedTicker = (item:string) =>{
        setQuery("")
        console.log(`clicked ${item}`)
        onSelect(item)
    }
    return (
        <div className="relative">  {/* relative so dropdown positions correctly */}
            <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search..."
                className="border rounded-md p-2 w-full"
            />

            {/* Only show when user has typed something */}
            {query && (
                <ul className="absolute top-full left-0 w-full border rounded-md bg-white shadow-md z-10 max-h-60 overflow-y-auto">
                    {filtered.map(item => (
                        <li key={item} className="p-2 hover:bg-gray-100 cursor-pointer" onClick={()=>{clickedTicker(item)}}>
                            {item}
                        </li>
                    ))}
                </ul>
            )}
        </div>
    )
}
export default SearchList