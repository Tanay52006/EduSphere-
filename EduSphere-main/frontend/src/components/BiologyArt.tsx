const cells: Record<string, number> = {
  sun: 0,
  molecule: 1,
  water: 2,
  chloroplast: 3,
  glucose: 4,
  mitochondria: 5,
  cell: 6,
  battery: 7,
  digestion: 8,
  flask: 9,
  seedling: 10,
  cofactor: 11,
  process: 11,
};
export function BiologyArt({
  kind,
  size = 64,
}: {
  kind: string;
  size?: number;
}) {
  const index = cells[kind] ?? 11;
  return (
    <span
      className="biology-art"
      aria-hidden="true"
      style={{
        width: size,
        height: size,
        backgroundPosition: `${((index % 4) * 100) / 3}% ${Math.floor(index / 4) * 50}%`,
      }}
    />
  );
}
