import { PostTitle } from "@/components/Post-title";

type Props = {
  title: string;
  date: string;
};

export function PostHeader({title, date}: Props) {
  return (
    <>
      <PostTitle>{title}</PostTitle>
      <div className="mb-6 text-md text-green-600">
        {date}
      </div>
    </>
  );
}