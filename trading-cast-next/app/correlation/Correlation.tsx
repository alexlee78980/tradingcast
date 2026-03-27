"use client"
const Correlation = ({data}:any) => {
    
    console.log(data)
    if(!data){
        return
    }
    const pickColor = (value: number) => {
    const r = Math.round(255 * (1 - value)) 
    const g = Math.round(255 * value)        
    return `rgb(${r}, ${g}, 0)`
}

    return <div className="m-10">
        <div className="font-bold text-2xl mb-10 ">{data.ticker}</div>
        {Object.entries(data.correlations).map(([key, value]:any) => {
            return <div key={key} className="grid grid-cols-[70px_1fr] items-center gap-4 mb-4 mx-10">
                <div>{key}</div>
             <div className="mx-10 w-full border rounded-full h-6 mb-4 relative">
                <div className="absolute inset-y-0 left-1/2 w-px bg-gray-400"/>
                
                <div className="h-6 absolute" style={{
                    width: `${Math.abs(value.regular) * 50}%`,
                    left: value.regular >= 0 ? '50%' : `${50 - Math.abs(value.regular) * 50}%`,
                    backgroundColor: pickColor(value.regular),
                    borderRadius: value.regular >= 0 ? '0 9999px 9999px 0' : '9999px 0 0 9999px'
                }}/>
                <span className="absolute inset-0 flex items-center justify-center text-sm">
                    {value.regular.toFixed(2)}
                </span>
            </div>
            </div>
        })}
    </div>
}
export default Correlation
