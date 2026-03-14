
interface SearchBarProps{
    value: string;
    onChange: (e:any)=>void;
}

const SearchBar:React.FC<SearchBarProps> = ({value, onChange}) =>{
    return <input type="text" value={value} onChange={onChange}></input>
}

export default SearchBar