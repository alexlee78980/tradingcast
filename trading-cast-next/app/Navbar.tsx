"use client"

import Link from "next/link";
import { usePathname } from "next/navigation";

const NavBar: React.FC = () => {
    const pathname = usePathname();

    const links = [
        { href: "/", label: "Home" },
        { href: "/chart", label: "Chart" },
        { href: "/analyze", label: "Analyze" },
        { href: "/download", label: "Download" },
        { href: "/correlation", label: "Correlation" },
    ];

    return (
        <div className="flex bg-black h-20">
            <ul className="flex justify-center gap-4 w-full items-center text-white">
                {links.map(({ href, label }) => (
                    <li key={href}>
                        <Link
                            href={href}
                            className={pathname === href ? "underline underline-offset-4" : ""}
                        >
                            {label}
                        </Link>
                    </li>
                ))}
            </ul>
        </div>
    );
}

export default NavBar;