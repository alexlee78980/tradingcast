
interface DateSelectionProps {
    onChange:(e:any)=>void;
    value:string;
}
const DateSelection:React.FC<DateSelectionProps> = ({onChange, value}) =>{
    return <div><input type="date" onChange={onChange} value={value}/></div>
}

export default DateSelection