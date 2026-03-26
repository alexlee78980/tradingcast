"use client"
import type { ReactElement } from "react";

interface ButtonProps{
    children:ReactElement;
    onClick:()=>void;
}
const Button:React.FC<ButtonProps> = ({children, onClick}) =>{
    return <button className="bg-black rounded-sm text-white p-4 hover:scale-105 hover:shadow-lg min-h-14" onClick={onClick}>{children}</button>
}

export default Button