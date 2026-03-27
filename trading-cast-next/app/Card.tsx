import Button from "@/components/Button";
import Image from "next/image";
import Link from "next/link";
interface CardProps{
    gifpath:string;
    title:string;
    description:string;
    path:string;
}
const Card = ({gifpath, title, description, path}: CardProps) => {
    return <div className="border border-gray-500 rounded-xl w-[400px] flex flex-col flex-shrink-0">
        <div className="h-[150px] flex-shrink-0">
            <Image className="rounded-xl w-full h-full object-contain" src={gifpath} width={400} height={225} alt={title}/>
        </div>
        <div className="h-[50px] font-bold flex justify-center items-center">{title}</div>
        <div className="h-[120px] mx-5 overflow-hidden mb-4">{description}</div>
        <div className="flex justify-center mb-5 mt-auto">
            <Button><Link href={path}>→</Link></Button>
        </div>
    </div>
}
export default Card