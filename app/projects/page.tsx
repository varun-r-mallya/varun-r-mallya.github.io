'use client'
import axios from 'axios';
import { useEffect, useState } from 'react';
import Image from 'next/image';

interface Project {
    id: number;
    name: string;
    description: string;
    fork: boolean;
    html_url: string;
    stargazers_count: number;
    watchers: number;
    open_issues: number;
    forks: number;
    language: string;

  }

export default function Projects() {
    const [projects, setProjects] = useState<Project[]>([]);
    
    useEffect(() => {
        axios.get('https://api.github.com/users/varun-r-mallya/repos')
            .then((response: { data: Project[] }) => {
                setProjects(response.data);
            })
            .catch((error: any) => console.error("There was an error fetching the GitHub projects:", error));
    }, []);

    return (
        <div className='min-h-screen min-w-screen pb-10 font-mono' style={{ backgroundImage: "url('/stars.png')" }}>
            <div className='mt-16 md:mt-auto'>
                <h1 className="text-2xl font-mono text-center text-green-300">Stuff I've made over time</h1>
                <h2 className="text-1xl font-mono text-center text-green-500">Some nice, most stupid, but I hope you'll like them.</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 m-4 md:m-40 mt-10 md:mt-5">
                {projects.map(project => {
                    if(project.fork === false) {
                        return (
                            <div key={project.id} className="bg-gray-900 border-blue-600 border-opacity-100 p-4 rounded-md flex flex-col justify-center items-center">
                                <h3 className="text-l md:text-xl text-blue-500 font-semibold">{project.name}</h3>
                                <p className="mt-2 text-sm text-center max-w-[75%]">{project.description}</p>
                                <span>{project.language}</span> 
                                <div className='flex flex-row max-w-[75%] space-x-2 text-[0.8rem] md:text-sm'>
                                    <span>⭐ {project.stargazers_count} | </span>
                                    <span><Image src="/watchers.svg" width='20' height='20' color='white' alt='watchers icon'/></span>
                                    <span>{project.forks}</span>
                                </div>
                                <a className='rounded-full ' href={project.html_url}>
                                    <button className="bg-gray-700 hover:bg-gray-600 text-white font-bold py-2 px-4 rounded-full mt-4">
                                        <Image src='/github.svg' className='w-4 h-4 inline-block mr-2' alt='github' width='50' height='50'/> View on GitHub
                                    </button>
                                </a>
                            </div>
                        );
                    }
                    return null;
                })}
            </div>
        </div>
    );
}