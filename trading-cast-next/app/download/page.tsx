"use client"
import Button from "@/components/Button"
import DateSelection from "@/components/DateSelection"
import SearchBar from "@/components/SearchBar"
import { useState } from "react"


const Download:React.FC = () =>{
    const [value, setValue] = useState("");
    const [startDate, setStartDate] = useState("");
    const [endDate, setEndDate] = useState("");
    const changeStock = (e) =>{
        setValue(e.target.value)
    }
    const onDownload = async() =>{
        const today = new Date();
        const tenYearsAgo = new Date();
        tenYearsAgo.setFullYear(today.getFullYear() - 10);

        const formatDate = (date: Date) => date.toISOString().split("T")[0]; // "YYYY-MM-DD"

        const body = {
            ticker: value,                        
            start: startDate ? startDate : formatDate(tenYearsAgo),         
            end: endDate ? endDate : formatDate(today),             
        };

        const res = await fetch("http://127.0.0.1:8000/trades/download", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });

        const data = await res.json();
        console.log(data);
    }

    const changeStartDate = (e:any) =>{
        console.log(e.target.value)
        setStartDate(e.target.value)
    }

        const changeEndDate = (e:any) =>{
        console.log(e.target.value)
        setEndDate(e.target.value)
    }

    return <div className="flex flex-col justify-center items-center gap-4 ">
    <SearchBar value={value} onChange={changeStock}/>
      <DateSelection value={startDate} onChange={changeStartDate} />
      <DateSelection value={endDate} onChange={changeEndDate}/>
      <Button onClick={onDownload}>Download</Button>
      </div>
      }
export default Download