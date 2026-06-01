// Estilo compartido del tooltip de recharts (tema oscuro, legible).
export const TOOLTIP_PROPS = {
  contentStyle: {
    background: "#0b1118",
    border: "1px solid #2b3a4a",
    borderRadius: 8,
    color: "#e6edf3",
  },
  labelStyle: { color: "#e6edf3", fontWeight: 600 },
  itemStyle: { color: "#e6edf3" },
  labelFormatter: (v: unknown) => `día ${Math.round(Number(v))}`,
};
