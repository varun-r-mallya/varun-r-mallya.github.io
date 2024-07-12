'use client'
import Link from 'next/link';
import React, { useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faBars } from '@fortawesome/free-solid-svg-icons';
import { faXmark } from '@fortawesome/free-solid-svg-icons';

const DesktopNavLinks = () => {
  return (
    <nav className=" text-green-500 p-4 font-mono flex z-50 m-2">
      <ul className="space-x-4 flex-grow">
        <li>
          <Link href="/" className="hover:text-green-300">
            Home
          </Link>
        </li>
      </ul>
      <ul className="flex justify-end space-x-4">
        <li>
          <Link href="/contact" className="hover:text-green-300">
            Contact me
          </Link>
        </li>
        <li>
          <Link href="/projects" className="hover:text-green-300">
            Projects
          </Link>
        </li>
        <li>
          <Link href="/blog" className="hover:text-green-300">
            Blog
          </Link>
        </li>
      </ul>
    </nav>
  );
}

function MobileDrawer({ isOpen, onClose }) {
  return (
    <div
      className={`fixed flex flex-col justify-center items-center top-0 right-0 h-full w-2/4 bg-gray-900 opacity-100 text-green transition-transform duration-300 transform z-50 ${
        isOpen ? 'translate-x-0' : 'translate-x-full'
      }`}
    >
      <button className="absolute right-7 top-4 p-3 z-50" onClick={onClose}>
        <FontAwesomeIcon className="text-5xl" icon={faXmark} />
      </button>
      <ul className="flex flex-col justify-center items-center space-y-4 text-green-600">
        <li>
          <Link href="/" className="hover:text-green-300" onClick={onClose}>
            Home
          </Link>
        </li>
        <li>
          <Link href="/contact" className="hover:text-green-300" onClick={onClose}>
            Contact me
          </Link>
        </li>
        <li>
          <Link href="/projects" className="hover:text-green-300" onClick={onClose}>
            Projects
          </Link>
        </li>
        <li>
          <Link href="/blog" className="hover:text-green-300" onClick={onClose}>
            Blog
          </Link>
        </li>
        
      </ul>
    </div>
  );
}

function MobileMenuButton({ onClick }) {
  return (
    <button className="absolute right-2 top-2 p-2 z-50" onClick={onClick}>
      <FontAwesomeIcon className="text-4xl" icon={faBars} style={{ color: 'green' }}/>
    </button>
  );
}

export const NavBar = () => {
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const handleDrawerToggle = () => {
    setIsDrawerOpen(!isDrawerOpen);
  };

  return (
    <div className="z-50">
      <div className="hidden relative py-2 sm:flex flex-col justify-center">
      <DesktopNavLinks/>
      </div>
      <div className="sm:hidden relative flex flex-row my-2 ">
        <MobileMenuButton onClick={handleDrawerToggle} />
        <MobileDrawer isOpen={isDrawerOpen} onClose={handleDrawerToggle} />
      </div>
    </div>
  );
};
