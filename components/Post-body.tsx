import markdownStyles from "./markdown-styles.module.css";

type Props = {
  content: string;
};

export function PostBody({ content }: Props) {
  return (
    <div className="justify-center items-center flex flex-col">
        <div className="flex-row justify-center items-center max-w-[90vw] md:w-[50vw]">
          <div
            className={markdownStyles["markdown"]}
            dangerouslySetInnerHTML={{ __html: content }}
          >
           
          </div>
        </div>
    </div>
  );
}