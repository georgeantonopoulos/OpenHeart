'use client';

import { useTranslation } from 'react-i18next';
import { Languages, Check } from 'lucide-react';
import { useState, useEffect } from 'react';

export function LanguageSwitcher() {
    const { i18n, t } = useTranslation('common');
    const [isOpen, setIsOpen] = useState(false);
    const [mounted, setMounted] = useState(false);

    // Prevent hydration mismatch
    useEffect(() => {
        setMounted(true);
    }, []);

    if (!mounted) return null;

    const currentLang = i18n.language || 'en';

    const languages = [
        { code: 'en', label: 'English', flag: '🇺🇸' },
        { code: 'el', label: 'Ελληνικά', flag: '🇨🇾' },
    ];

    const changeLanguage = (lng: string) => {
        i18n.changeLanguage(lng);
        setIsOpen(false);
    };

    return (
        <div className="relative">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/50 border border-slate-700 text-slate-300 hover:text-white hover:bg-slate-800 transition-all"
                title={t('common.actions')}
            >
                <Languages className="w-4 h-4" />
                <span className="text-xs font-medium uppercase">{currentLang}</span>
            </button>

            {isOpen && (
                <>
                    <div
                        className="fixed inset-0 z-40"
                        onClick={() => setIsOpen(false)}
                    />
                    <div className="absolute right-0 mt-2 w-40 rounded-xl bg-slate-900 border border-slate-800 shadow-2xl z-50 overflow-hidden animate-in fade-in zoom-in-95 duration-100">
                        <div className="py-1">
                            {languages.map((lang) => (
                                <button
                                    key={lang.code}
                                    onClick={() => changeLanguage(lang.code)}
                                    className="flex items-center justify-between w-full px-4 py-2.5 text-sm text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
                                >
                                    <div className="flex items-center gap-2">
                                        <span className="text-lg leading-none">{lang.flag}</span>
                                        <span>{lang.label}</span>
                                    </div>
                                    {currentLang === lang.code && (
                                        <Check className="w-4 h-4 text-teal-400" />
                                    )}
                                </button>
                            ))}
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}
