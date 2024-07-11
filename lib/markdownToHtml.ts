import rehypePrism from "rehype-prism";
import rehypeStringify from "rehype-stringify";
import remarkParse from "remark-parse";
import remarkRehype from "remark-rehype";
// import remarkPrism from "remark-prism";
import { unified } from "unified";

export default async function markdownToHtml(markdown: string) {
  // console.log(markdown)
  const content = await unified()
    .use(remarkParse) // Parse markdown content to a syntax tree
    .use(remarkRehype) // Turn markdown syntax tree to HTML syntax tree, ignoring embedded HTML
    // .use(remarkPrism) // Add syntax highlighting to code blocks
    .use(rehypePrism as any)
    .use(rehypeStringify) // Serialize HTML syntax tree
    .process(markdown);
  return content.toString();
}
