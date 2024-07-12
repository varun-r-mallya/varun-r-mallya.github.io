import { notFound } from "next/navigation";
import { getAllPosts, getPostBySlug } from "@/lib/api";
import PostBody from "@/components/Post-body";
import { PostHeader } from "@/components/Post-header";
import Comments from "@/components/utterances";

export default async function Post({ params }: Params) {
  const post = getPostBySlug(params.slug);

  if (!post) {
    return notFound();
  }

  return (
    <main>
        <article className="flex flex-row justify-center mt-16 md:mt-30 max-w-[90vw] md:max-w-3/4 ml-10 mr-10">
        <div className="flex flex-col justify-center items-center w-full">
            <div className="grid grid-flow-row">
              <PostHeader
                title={post.title}
                date={post.date}
              />
              <PostBody markdown={post.content} />
            </div>
            <Comments issueTerm={post.title} />
        </div>
        </article>
    </main>
  );
}

type Params = {
  params: {
    slug: string;
  };
};

export async function generateStaticParams() {
  const posts = getAllPosts();

  return posts.map((post) => ({
    slug: post.slug,
  }));
}