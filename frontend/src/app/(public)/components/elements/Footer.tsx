import React from 'react';
import { siteDetails } from "../../siteDetails";

const Footer: React.FC = () => {
    return (
        <footer className="bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700">
            <div className="mx-auto w-full max-w-screen-xl p-4 py-6 lg:py-8">
                <div className="md:flex md:justify-between">
                    <div className="mb-6 md:mb-0">
                        <a href={siteDetails.siteUrl} className="flex items-center">
                            <img src={siteDetails.siteLogo} className="h-8 me-3" alt={`${siteDetails.siteName} logo`} />
                            <span className="self-center text-2xl font-semibold whitespace-nowrap
                             dark:text-white">{siteDetails.siteName}</span>
                        </a>
                    </div>
                    <div className="grid grid-cols-2 gap-8 sm:gap-6 sm:grid-cols-3">
                        <div>
                            <h2 className="mb-6 text-sm font-semibold text-gray-900 uppercase dark:text-white">Projet</h2>
                            <ul className="text-gray-500 dark:text-gray-400 font-medium">
                                <li className="mb-4">
                                    <a href="/docs" className="hover:underline">Documentation</a>
                                </li>
                                <li>
                                    <a href="/blog" className="hover:underline">Blog</a>
                                </li>
                            </ul>
                        </div>
                        <div>
                            <h2 className="mb-6 text-sm font-semibold text-gray-900 uppercase dark:text-white">Communauté</h2>
                            <ul className="text-gray-500 dark:text-gray-400 font-medium">
                                <li className="mb-4">
                                    <a href={siteDetails.GitHubUrl} className="hover:underline">GitHub</a>
                                </li>
                                <li>
                                    <a href={siteDetails.DiscordUrl} className="hover:underline">Discord</a>
                                </li>
                            </ul>
                        </div>
                        <div>
                            <h2 className="mb-6 text-sm font-semibold text-gray-900 uppercase dark:text-white">Légal</h2>
                            <ul className="text-gray-500 dark:text-gray-400 font-medium">
                                <li className="mb-4">
                                    <a href="/privacy" className="hover:underline">Politique de confidentialité</a>
                                </li>
                                <li>
                                    <a href="/terms" className="hover:underline">Conditions d’utilisation</a>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
                <hr className="my-6 border-gray-200 sm:mx-auto dark:border-gray-700 lg:my-8" />
                <div className="sm:flex sm:items-center sm:justify-between">
                    <span className="text-sm text-gray-500 sm:text-center dark:text-gray-400">
                        © {new Date().getFullYear()} <a href={siteDetails.siteUrl} className="hover:underline">
                            {siteDetails.siteName}</a>. Tous droits réservés.
                    </span>

                </div>
            </div>
        </footer>
    );
};

export default Footer;
