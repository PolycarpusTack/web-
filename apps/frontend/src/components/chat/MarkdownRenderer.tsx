import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import rehypeRaw from 'rehype-raw';
import 'katex/dist/katex.min.css';
import { Check, Copy } from "lucide-react";
import { Button } from '@/components/ui/button';
import { cn } from '@/components/lib/utils';

interface CodeBlockProps {
  language: string;
  value: string;
  className?: string;
}

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

const CodeBlock: React.FC<CodeBlockProps> = ({ language, value, className }) => {
  const [copied, setCopied] = React.useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={cn("relative group", className)}>
      <div className="absolute right-2 top-2 opacity-0 group-hover:opacity-100 transition-opacity z-10">
        <Button 
          variant="ghost" 
          size="icon" 
          className="h-8 w-8 bg-muted/50 hover:bg-muted"
          onClick={handleCopy}
        >
          {copied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
        </Button>
      </div>
      <div className="absolute top-0 right-0 px-2 py-1 text-xs font-mono bg-muted rounded-bl">
        {language}
      </div>
      <SyntaxHighlighter
        language={language}
        style={vscDarkPlus}
        customStyle={{
          margin: 0,
          borderRadius: '0.5rem',
          fontSize: '0.9rem',
          padding: '1.5rem 1rem 1rem',
        }}
      >
        {value}
      </SyntaxHighlighter>
    </div>
  );
};

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content, className }) => {
  return (
    <ReactMarkdown
      className={cn("prose dark:prose-invert prose-sm max-w-none break-words", className)}
      remarkPlugins={[remarkGfm, remarkMath]}
      rehypePlugins={[rehypeKatex, rehypeRaw]}
      components={{
        code({ node, className, children, ...props }: any) {
          const match = /language-(\w+)/.exec(className || '');
          const lang = match && match[1] ? match[1] : '';
          
          const inline = !className || !match;
          if (!inline && match) {
            return (
              <CodeBlock
                language={lang}
                value={String(children).replace(/\n$/, '')}
                {...props}
              />
            );
          }
          
          return (
            <code className={cn("px-1 py-0.5 rounded bg-muted font-mono text-sm", className)} {...props}>
              {children}
            </code>
          );
        },
        pre({ children }) {
          // This wrapper is needed to avoid default styling
          return <div className="not-prose">{children}</div>;
        },
        p({ children }) {
          return <p className="mb-4 last:mb-0">{children}</p>;
        },
        a({ href, children }) {
          return (
            <a 
              href={href} 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-primary underline hover:text-primary/80 transition-colors"
            >
              {children}
            </a>
          );
        },
        table({ children }) {
          return (
            <div className="overflow-x-auto my-4">
              <table className="border-collapse w-full">
                {children}
              </table>
            </div>
          );
        },
        blockquote({ children }) {
          return (
            <blockquote className="border-l-4 border-primary/20 pl-4 py-1 my-4 italic">
              {children}
            </blockquote>
          );
        },
        img({ src, alt }) {
          return (
            <img 
              src={src} 
              alt={alt || ''} 
              className="max-w-full h-auto rounded-md my-4"
              loading="lazy"
            />
          );
        },
        h1({ children }) {
          return <h1 className="text-2xl font-bold mt-6 mb-4">{children}</h1>;
        },
        h2({ children }) {
          return <h2 className="text-xl font-bold mt-6 mb-3">{children}</h2>;
        },
        h3({ children }) {
          return <h3 className="text-lg font-bold mt-5 mb-2">{children}</h3>;
        },
        h4({ children }) {
          return <h4 className="text-base font-bold mt-4 mb-2">{children}</h4>;
        },
        ul({ children }) {
          return <ul className="list-disc pl-6 mb-4">{children}</ul>;
        },
        ol({ children }) {
          return <ol className="list-decimal pl-6 mb-4">{children}</ol>;
        },
        li({ children }) {
          return <li className="mb-1">{children}</li>;
        },
        hr() {
          return <hr className="my-4 border-t border-muted" />;
        }
      }}
    >
      {content}
    </ReactMarkdown>
  );
};

export default MarkdownRenderer;