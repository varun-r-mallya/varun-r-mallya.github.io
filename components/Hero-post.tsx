import React from "react";
import Link from "next/link";

type Props = {
    title: string;
    date: string;
    slug: string;
  };

export default function HeroPost({
    title,
    date,
    slug,
  }: Props) {
    return (
      <section>
        <div className="flex flex-col justify-start items-start w-[90vw] mb-10">
          <div>
            <h3 className="mb-4 text-2xl lg:text-3xl text-white">
              <Link href={`/blog/${slug}`} className="hover:underline">
                {title}
              </Link>
            </h3>
            <div className="mb-4 md:mb-0 text-lg">
              {date}
            </div>
          </div>
        </div>
      </section>
    );
  }
