import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

// Import all locales
import commonEn from '../locales/en/common.json';
import cardiologyEn from '../locales/en/cardiology.json';
import commonEl from '../locales/el/common.json';
import cardiologyEl from '../locales/el/cardiology.json';

const resources = {
    en: {
        common: commonEn,
        cardiology: cardiologyEn,
    },
    el: {
        common: commonEl,
        cardiology: cardiologyEl,
    },
};

// Initialize i18next
i18n
    .use(initReactI18next)
    .init({
        resources,
        lng: typeof window !== 'undefined' ? localStorage.getItem('openheart-lang') || 'en' : 'en',
        fallbackLng: 'en',
        ns: ['common', 'cardiology'],
        defaultNS: 'common',
        interpolation: {
            escapeValue: false, // react already safes from xss
        },
        react: {
            useSuspense: false, // next.js handles suspense differently
        },
    });

// Handle language persistence
if (typeof window !== 'undefined') {
    i18n.on('languageChanged', (lng) => {
        localStorage.setItem('openheart-lang', lng);
        document.documentElement.lang = lng;
    });
}

export default i18n;
