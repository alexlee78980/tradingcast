import type { ReactElement } from "react";

interface ButtonProps{
    children:ReactElement;
    onClick:()=>void;
}
const Button:React.FC<ButtonProps> = ({children, onClick}) =>{
    return <button onClick={onClick}>{children}</button>
}

export default Button