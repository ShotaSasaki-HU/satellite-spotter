export default function ReportPage() {
  return (
    <div className="relative w-full h-full">
      <div
        className={`
          absolute top-6 left-0 w-45 md:w-48 h-12
          flex items-center justify-center
          bg-bg-primary border-r-2 border-r-compass-gold z-1000
        `}
      >
        <h1 className="text-compass-gold text-xl md:text-2xl">観測レポート</h1>
      </div>
    </div>
  )
}
