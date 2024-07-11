import { getAllPosts } from "@/lib/api";
import  HeroPost from "@/components/Hero-post";

export default function Index() {
  const allPosts = getAllPosts();

  return (
    <main className="flex flex-row justify-center items-center font-mono text-green-600">
      <div className="flex flex-col justify-center items-center">
        <h1 className="text-5xl md:text-6xl mb-8">
          Blog
        </h1>
          <div className="flex flex-col justify-center items-center">
            {allPosts.map((post) => (
              <HeroPost
                key={post.slug}
                title={post.title}
                date={post.date}
                slug={post.slug}
              />
            ))  
            }
          </div>
      </div>
    </main>
  );
}