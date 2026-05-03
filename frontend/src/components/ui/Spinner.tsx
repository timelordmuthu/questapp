// frontend/src/components/ui/Spinner.tsx
export default function Spinner({ size = 24 }: { size?: number }) {
  return (
    <div
      className="spinner"
      style={{ width: size, height: size }}
    />
  )
}
