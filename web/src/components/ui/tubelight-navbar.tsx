"use client"

import React, { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { LucideIcon, LogIn, LogOut, User } from "lucide-react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { cn } from "@/lib/utils"
import { useAuth } from "@/context/AuthContext"

interface NavItem {
    name: string
    url: string
    icon: LucideIcon
    mode?: string
    href?: string
}

interface NavBarProps {
    items: NavItem[]
    className?: string
    onTabChange?: (mode: string) => void
    activeMode?: string
}

export function NavBar({ items, className, onTabChange, activeMode }: NavBarProps) {
    const [activeTab, setActiveTab] = useState(items[0].name)
    const [isMobile, setIsMobile] = useState(false)
    const [userMenuOpen, setUserMenuOpen] = useState(false)
    const [mounted, setMounted] = useState(false)
    const { user, signOut, loading } = useAuth()
    const pathname = usePathname()
    const router = useRouter()

    // Hydration mismatch'i önle — auth state yalnızca client'ta bilinir
    useEffect(() => { setMounted(true) }, [])

    useEffect(() => {
        const handleResize = () => setIsMobile(window.innerWidth < 768)
        handleResize()
        window.addEventListener("resize", handleResize)
        return () => window.removeEventListener("resize", handleResize)
    }, [])

    // Dışarı tıklanınca menüyü kapat
    useEffect(() => {
        function handleClickOutside() { setUserMenuOpen(false) }
        if (userMenuOpen) document.addEventListener("click", handleClickOutside)
        return () => document.removeEventListener("click", handleClickOutside)
    }, [userMenuOpen])

    async function handleSignOut() {
        await signOut()
        router.push("/")
    }

    // E-postanın baş harfini avatar olarak kullan
    const avatarLetter = user?.email?.[0]?.toUpperCase() ?? "U"
    const shortEmail   = user?.email ? (user.email.length > 20 ? user.email.slice(0, 18) + "…" : user.email) : ""

    return (
        <div className={cn(
            "fixed bottom-0 sm:top-0 left-1/2 -translate-x-1/2 z-50 mb-6 sm:mt-6 pointer-events-none",
            className,
        )}>
            <div className="flex items-center gap-3 bg-background/5 border border-border backdrop-blur-lg py-1 px-1 rounded-full shadow-lg pointer-events-auto">

                {/* Nav items */}
                {items.map((item) => {
                    const Icon = item.icon
                    const isRouteItem = !!item.href
                    const isRouteActive = isRouteItem && pathname?.startsWith(item.href!)
                    const isActive = activeMode ? activeMode === item.mode : activeTab === item.name
                    const isItemActive = isRouteItem ? isRouteActive : isActive

                    const handleClick = (e: React.MouseEvent) => {
                        if (!isRouteItem) {
                            e.preventDefault()
                            setActiveTab(item.name)
                            if (onTabChange && item.mode) onTabChange(item.mode)
                        } else {
                            setActiveTab(item.name)
                        }
                    }

                    const commonClass = cn(
                        "relative cursor-pointer text-sm font-semibold px-6 py-2 rounded-full transition-colors",
                        "text-foreground/80 hover:text-primary",
                        isItemActive && "bg-muted text-primary",
                    )

                    const innerContent = (
                        <>
                            <span className="hidden md:inline">{item.name}</span>
                            <span className="md:hidden"><Icon size={18} strokeWidth={2.5} /></span>
                            {isItemActive && (
                                <motion.div
                                    layoutId="lamp"
                                    className="absolute inset-0 w-full bg-primary/5 rounded-full -z-10"
                                    initial={false}
                                    transition={{ type: "spring", stiffness: 300, damping: 30 }}
                                >
                                    <div className="absolute -top-2 left-1/2 -translate-x-1/2 w-8 h-1 bg-primary rounded-t-full">
                                        <div className="absolute w-12 h-6 bg-primary/20 rounded-full blur-md -top-2 -left-2" />
                                        <div className="absolute w-8 h-6 bg-primary/20 rounded-full blur-md -top-1" />
                                        <div className="absolute w-4 h-4 bg-primary/20 rounded-full blur-sm top-0 left-2" />
                                    </div>
                                </motion.div>
                            )}
                        </>
                    )

                    if (isRouteItem) {
                        return (
                            <Link key={item.name} href={item.href!} onClick={handleClick} className={commonClass}>
                                {innerContent}
                            </Link>
                        )
                    }
                    return (
                        <a key={item.name} href={item.url} onClick={handleClick} className={commonClass}>
                            {innerContent}
                        </a>
                    )
                })}

                {/* Auth Section — yalnızca client'ta render et */}
                {mounted && !loading && (
                    <div className="ml-1 pl-2 border-l border-white/10 flex items-center relative">
                        {user ? (
                            <>
                                {/* Avatar butonu */}
                                <button
                                    onClick={(e) => { e.stopPropagation(); setUserMenuOpen(!userMenuOpen) }}
                                    className="w-7 h-7 rounded-full bg-gradient-to-br from-primary to-primary/60 flex items-center justify-center text-xs font-bold text-white hover:opacity-90 transition-opacity"
                                    title={user.email}
                                >
                                    {avatarLetter}
                                </button>

                                {/* Dropdown menü */}
                                {userMenuOpen && (
                                    <div
                                        className="absolute right-0 top-10 w-52 bg-card border border-border/60 rounded-xl shadow-xl py-1 z-50"
                                        onClick={(e) => e.stopPropagation()}
                                    >
                                        <div className="px-3 py-2 border-b border-border/40">
                                            <p className="text-xs text-muted-foreground truncate">{shortEmail}</p>
                                        </div>
                                        <Link
                                            href="/profile"
                                            onClick={() => setUserMenuOpen(false)}
                                            className="flex items-center gap-2 px-3 py-2 text-sm text-foreground/80 hover:text-foreground hover:bg-muted/40 transition-colors"
                                        >
                                            <User size={13} /> Profil
                                        </Link>
                                        <button
                                            onClick={handleSignOut}
                                            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-rose-400 hover:bg-rose-500/10 transition-colors"
                                        >
                                            <LogOut size={13} /> Çıkış Yap
                                        </button>
                                    </div>
                                )}
                            </>
                        ) : (
                            <Link
                                href="/sign-in"
                                className="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-full text-foreground/70 hover:text-primary hover:bg-white/5 transition-colors whitespace-nowrap"
                            >
                                <LogIn size={13} /> Giriş Yap
                            </Link>
                        )}
                    </div>
                )}
            </div>
        </div>
    )
}
