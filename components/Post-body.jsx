import markdownStyles from "./markdown-styles.module.css";
import { FC } from 'react';
import ReactMarkdown from 'react-markdown';
import { PrismLight as SyntaxHighlighter } from 'react-syntax-highlighter';
import tsx from 'react-syntax-highlighter/dist/cjs/languages/prism/tsx';
import typescript from 'react-syntax-highlighter/dist/cjs/languages/prism/typescript';
import javascript from 'react-syntax-highlighter/dist/cjs/languages/prism/javascript';
import cpp from 'react-syntax-highlighter/dist/cjs/languages/prism/cpp';
import go from 'react-syntax-highlighter/dist/cjs/languages/prism/go';
import python from 'react-syntax-highlighter/dist/cjs/languages/prism/python';
import yml from 'react-syntax-highlighter/dist/cjs/languages/prism/yaml';
import rust from 'react-syntax-highlighter/dist/cjs/languages/prism/rust';
import bash from 'react-syntax-highlighter/dist/cjs/languages/prism/bash';
import markdown from 'react-syntax-highlighter/dist/cjs/languages/prism/markdown';
import json from 'react-syntax-highlighter/dist/cjs/languages/prism/json';
import rangeParser from 'parse-numeric-range';
import { oneDark } from 'react-syntax-highlighter/dist/cjs/styles/prism';
import { ReactNode } from 'react';

SyntaxHighlighter.registerLanguage('tsx', tsx);
SyntaxHighlighter.registerLanguage('typescript', typescript);
SyntaxHighlighter.registerLanguage('rust', rust);
SyntaxHighlighter.registerLanguage('javascript', javascript);
SyntaxHighlighter.registerLanguage('cpp', cpp);
SyntaxHighlighter.registerLanguage('go', go);
SyntaxHighlighter.registerLanguage('python', python);
SyntaxHighlighter.registerLanguage('yaml', yml);
SyntaxHighlighter.registerLanguage('bash', bash);
SyntaxHighlighter.registerLanguage('markdown', markdown);
SyntaxHighlighter.registerLanguage('json', json);

const PostBody = ({ markdown }) => {
  
  const syntaxTheme = oneDark;

  const MarkdownComponents = {
    code({ node, inline, className, ...props }) {
      const hasLang = /language-(\w+)/.exec(className || '');
      const hasMeta = node?.data?.meta;

      const applyHighlights= (applyHighlights) => {
        if (hasMeta) {
          const RE = /{([\d,-]+)}/;
          const metadata = node.data.meta?.replace(/\s/g, '');
          const strlineNumbers = RE?.test(metadata)
            ? RE?.exec(metadata)?.[1]
            : '0';
          const highlightLines = rangeParser(strlineNumbers ?? '');
          const highlight = highlightLines;
          const data = highlight.includes(applyHighlights)
            ? 'highlight'
            : '';
          return { data };
        } else {
          return {};
        }
      };
  
      return hasLang ? (
        <SyntaxHighlighter
          style={syntaxTheme}
          language={hasLang[1]}
          PreTag="div"
          className="codeStyle"
          showLineNumbers={true}
          wrapLines={hasMeta}
          useInlineStyles={true}
          lineProps={applyHighlights}
        >
          {props.children}
        </SyntaxHighlighter>
      ) : (
        <code className={className} {...props} />
      )
    },
  };

  return (
    <div className="justify-center items-center flex flex-col">
        <div className="flex-row justify-center items-center max-w-[90vw] md:w-[50vw]">
          <ReactMarkdown
          className={markdownStyles.markdown}
          components={MarkdownComponents}
          >
            {markdown}
          </ReactMarkdown>
        </div>
    </div>
  );
}

export default PostBody;