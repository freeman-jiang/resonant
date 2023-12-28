export default async function PaddedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <div className="mx-auto px-8 py-4 md:max-w-2xl">{children}</div>;
}
