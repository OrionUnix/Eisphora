"use client";

import { Disclosure } from "@headlessui/react";
import { BiPlus, BiMinus } from "react-icons/bi";
import { faqs } from "./data/faq";

const FAQSection: React.FC = () => {
  return (
    <section id="faq" className="relative w-full h-screen overflow-hidden flex items-center justify-center">
    
       
            <div className="w-full md:w-1/2 p-8">
              <p className="text-sm text-gray-500 uppercase tracking-wide mb-4">FAQ'S</p>
              <h2 className="text-4xl sm:text-5xl font-extrabold text-gray-900 leading-tight">
                <span className="block">Frequently</span>
                <span className="block">Asked</span>
                <span className="block">Questions</span>
              </h2>
              <p className="mt-6 text-gray-600 text-lg">
                Didn't find the answer to your question?
              </p>
       <a
        href="https://github.com/YOUR_GITHUB_USERNAME/eisphora/issues/new" 
        rel="noopener noreferrer" 
        className="mt-3 inline-block text-2xl lg:text-3xl text-blue-600 font-semibold hover:underline"
    >
                Open an Issue on GitHub
              </a>
            </div>

            <div className="w-full md:w-1/2 p-6 space-y-4">
              {faqs.map((faq, index) => (
                <Disclosure key={index} as="div">
                  {({ open }) => (
                    <div className="">
                      <Disclosure.Button className="flex justify-between w-full text-left text-lg font-semibold text-gray-900">
                        <span>{faq.question}</span>
                        {open ? (
                          <BiMinus className="h-6 w-6 text-blue-500 transition-transform duration-200 rotate-180" />
                        ) : (
                          <BiPlus className="h-6 w-6 text-blue-500 transition-transform duration-200" />
                        )}
                      </Disclosure.Button>
                      <div className="overflow-hidden transition-all duration-300 ease-out data-[headlessui-state=closed]:opacity-0 data-[headlessui-state=closed]:-translate-y-2">
                        <Disclosure.Panel className="mt-4 text-gray-600">
                          {faq.answer}
                        </Disclosure.Panel>
                      </div>
                    </div>
                  )}
                </Disclosure>
              ))}
            </div>
 
       
      
    </section>
  );
};

export default FAQSection;