'use client';
import React, { useState, useEffect } from 'react';
import Image from 'next/image';

export default function Home() {
  const [scrollPosition, setScrollPosition] = useState(0);

  const handleScroll = () => {
    const position = window.scrollY;
    setScrollPosition(position);
  };

  useEffect(() => {
    window.addEventListener('scroll', handleScroll);

    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  const opacity = Math.max(1 - scrollPosition / 150, 0);
  const opacity1 = scrollPosition < 600 ? Math.min(scrollPosition / 150, 1) : Math.min(- (scrollPosition - 600) / 150, 0);
  const opacity2 = scrollPosition > 300 ? Math.min(scrollPosition / 800, 1) : 0;
  return (
    <div className="min-w-screen bg-cover bg-fixed bg-repeat bg-center flex justify-center items-center" style={{ backgroundImage: "url('/stars.png')" }}>
      <div className="flex-col justify-center items-center min-h-screen">
          <div className='flex items-center justify-center mt-[40vh] mb-[25vh]' style={{ opacity: `${opacity}` }}>
            <div className='flex-col justify-center items-center'>
              <h1 className="text-4xl md:text-8xl text-green-500 font-mono font-thin">
                {'Varun R Mallya'}
              </h1>
              <h2 className="text-sm md:text-3xl text-green-500 font-mono font-thin">
                {'>'}I am a programmer and an engineer.
              </h2>
            </div>
          </div>
            <div className='flex items-center justify-center' style={{ opacity: `${opacity1}` }}>
              <div className="flex-col items-center justify-center mb-[40vh] w-[90vw] md:w-[40vw]" style={{ opacity: `${opacity1}` }}>
              <h2 className="text-sm text-white-500 font-mono font-thin"><span className='text-blue-500'>varun</span>@xeonworkstation <span className='text-blue-500'>~</span> % cat details.txt</h2>
              <h2 className="text-sm text-green-500 font-mono font-thin">
                Currently, I am enrolled in the Bachelor of Technology program at IIT Roorkee. 
                <br/>My primary focus lies in the realm of Software development, particularly Low Level programming.
                <br/>I also help out here <a href="https://sdslabs.co" className="text-white hover:underline">@sdslabs</a>
              </h2>
              <h2 className="text-sm text-white-500 font-mono font-thin"><span className='text-blue-500'>varun</span>@xeonworkstation <span className='text-blue-500'>~</span> % ./blog.sh</h2>
              <h2 className="text-sm text-green-500 font-mono font-thin">
                Server started <a href='/blog' className='text-white hover:text-green-300'>here...</a>
              </h2>
              </div>
            </div>
            <div className='flex items-center justify-center' style={{ opacity: `${opacity2}` }}>
            <div className="flex-col items-center justify-center mb-[40vh] w-[90vw] md:w-[40vw]" style={{ opacity: `${opacity2}` }}>
              <h2 className="text-sm text-white-500 font-mono font-thin"><span className='text-blue-500'>varun</span>@xeonworkstation <span className='text-blue-500'>~</span> % where Projects</h2>
              <h2 className="text-sm text-green-500 font-mono font-thin">
               <a href="/projects" className='hover:underline'>/home/varun/projects</a>
              </h2>
              <h2 className="text-sm text-green-500 font-mono font-thin">
               <a href="https://github.com/varun-r-mallya" className='hover:underline'>/home/github</a>
              </h2>
              <h2 className="text-sm text-white-500 font-mono font-thin"><span className='text-blue-500'>varun</span>@xeonworkstation <span className='text-blue-500'>~</span> % which $TECHNOLOGIES</h2>
              <h2 className="text-sm text-green-500 font-mono font-thin">
               {/* <img src="https://skillicons.dev/icons?i=go,cpp,c,python,js,react,next,flask,npm,arch,docker,)"></img>
               <br />
               <img src="https://skillicons.dev/icons?i=rust,nodejs,bash,html,mongodb,mysql,figma,firebase,webassembly,git,googlecloud,)"></img>
               <br />
               <img src="https://skillicons.dev/icons?i=arduino,debian,tailwind,postman,pytorch,tensorflow,obsidian,vim,neovim,clion,vscode,)"></img>
               <br />
               <img src="https://skillicons.dev/icons?i=express,css,gradle,linux,ubuntu,vite,)"></img> */}
              <img src="https://skillicons.dev/icons?i=go,cpp,c,python,js,react,next,flask,npm,arch,docker,rust,nodejs,bash,html,mongodb,mysql,figma,firebase,webassembly,git,googlecloud,arduino,debian,tailwind,postman,pytorch,tensorflow,obsidian,vim,neovim,clion,vscode,express,css,gradle,linux,ubuntu,vite" alt="Technologies" className="w-full" />
              </h2>
            </div>
            </div>
      </div>
    </div>
  );
}