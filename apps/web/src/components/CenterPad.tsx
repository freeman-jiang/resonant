interface Props {
  children: React.ReactNode;
}

export const CenterPad = ({ children }: Props) => {
  return <div className="mx-auto px-8 py-4 md:max-w-2xl">{children}</div>;
};
