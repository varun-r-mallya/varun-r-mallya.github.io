import { ReactNode } from "react";

type Props = {
  children?: ReactNode;
};

export function PostTitle({ children }: Props) {
  return (
    <h1 className="text-4xl md:text-5xl mb-12 text-center md:text-left font-semibold">
      {children}
    </h1>
  );
}