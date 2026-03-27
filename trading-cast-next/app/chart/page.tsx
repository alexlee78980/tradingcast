"use client"
import styles from "./page.module.css"
import React, { useEffect, useState } from "react";
import { AgCharts } from "ag-charts-react";
import {
  AnimationModule,
  CandlestickSeriesModule,
  ContextMenuModule,
  CrosshairModule,
  LegendModule,
  ModuleRegistry,
  NumberAxisModule,
  OrdinalTimeAxisModule,
  TimeAxisModule,
  ZoomModule,
   CategoryAxisModule,
  LineSeriesModule
} from "ag-charts-enterprise";
import SearchBar from "../../components/SearchBar";
import Button from "../../components/Button";
import DateSelection from "../../components/DateSelection";

ModuleRegistry.registerModules([
  AnimationModule,
  CandlestickSeriesModule,
  CrosshairModule,
  LegendModule,
  NumberAxisModule,
  OrdinalTimeAxisModule,
    TimeAxisModule,  
    CategoryAxisModule,
  ContextMenuModule,
  ZoomModule,
    LineSeriesModule, 
]);

const ChartExample = () => {
  const [valueSearch,SetValueSearch] = useState("")
  const [startDate, setStartDate] = useState("")
  const [endDate, setEndDate] = useState("")
  const [options, setOptions] = useState<any>();
  const [rsiOptions, setRsiOptions] = useState<any>();

  const ChangeStock = (e:any) =>{
    SetValueSearch(e.target.value)
  }

  const onSearch = async() =>{
     const url = `${process.env.NEXT_PUBLIC_API_URL}/trades/v1/get/${valueSearch}?start=${startDate}&end=${endDate}`
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Response status: ${response.status}`);
    }

    let result = await response.json();
    console.log(result)
    result = result.map((v:any)=>{
      return {date: new Date(v.Date), 
              open: Number(v.Open),
              close:Number(v.Close),
              high:Number(v.High),
              low:Number(v.Low),
              volume:Number(v.Volume),
              moving:Number(v.moving10),
               rsi: Number(v.RSI)  
      }
    })
     console.log(result[0].date)
    
  
setOptions({
  zoom: {
    enabled: true,
    axes: "xy",
    anchorPointX: "pointer",
    anchorPointY: "pointer",
  },
  axes: [

    {
      type: "number",
      position: "left",
      id: "price-axis",
      keys: ["open", "close", "high", "low", "moving"],
      grid: { index: 0, size: "70%" },  
    },

  ],
  data: result,
  title: { text: valueSearch },
  footnote: { text: `${result[0].date} - ${result[result.length - 1].date}` },
  series: [

    {
      type: "candlestick",
      xKey: "date",
      lowKey: "low",
      highKey: "high",
      openKey: "open",
      closeKey: "close",
      axisId: "price-axis",               
    },

    {
      type: "line",
      xKey: "date",
      yKey: "moving",
      yName: "moving10",
      stroke: "blue",
      marker: { enabled: false },
      axisId: "price-axis",
    },

  ],
  listeners: {
    seriesNodeClick: (event: any) => {
      const { datum } = event;
      console.log("Date:", datum.date);
      console.log("Open:", datum.open);
      console.log("Close:", datum.close);
      console.log("High:", datum.high);
      console.log("Low:", datum.low);
      console.log("Volume:", datum.volume);
      console.log("RSI:", datum.rsi);
    },
  },
});

setRsiOptions({
  zoom: {
    enabled: true,
    axes: "xy",
    anchorPointX: "pointer",
    anchorPointY: "pointer",
  },
  axes: [
    { type: "ordinal-time", position: "bottom", id: "x-axis" },
    { type: "number", position: "left", id: "rsi-axis",  keys: ["rsi"],  min: 0, max: 100 } 
  ],
  data: result,
  title: { text: `${valueSearch} - RSI` },
  footnote: { text: `${result[0].date} - ${result[result.length - 1].date}` },
  series: [
    {
      type: "line",
      xKey: "date",
      yKey: "rsi",
      yName: "RSI (14)",
      stroke: "purple",
      marker: { enabled: false },
      axisId: "rsi-axis"   
    }
  ],
  listeners: {
    seriesNodeClick: (event: any) => {
      const { datum } = event;
      console.log("Date:", datum.date);
      console.log("RSI:", datum.rsi);
    },
  },
});
    console.log(result);
  } catch (error:any) {
    console.error(error.message);
  }
  }

  const onDownload = () =>{

  }

  const changeStartDate = (e:any) =>{
    console.log(e.target.value)
    setStartDate(e.target.value)
  }

    const changeEndDate = (e:any) =>{
    console.log(e.target.value)
    setEndDate(e.target.value)
  }

  return <div className="flex justify-center align-center">
    <div style={{"width":"1000px"}}>
    <AgCharts options={options} /> 
    <AgCharts options={rsiOptions} /> 
    <div className="flex flex-col justify-center items-center gap-4">
      <SearchBar value={valueSearch} onChange={ChangeStock}/>
      <DateSelection value={startDate} onChange={changeStartDate} />
      <DateSelection value={endDate} onChange={changeEndDate}/>
      <Button onClick={onSearch}>Search</Button>
      </div>
  </div></div>
};

export default ChartExample
