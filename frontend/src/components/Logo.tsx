export function Logo({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
  const sizes = {
    sm: 'w-8 h-8',
    md: 'w-12 h-12',
    lg: 'w-16 h-16',
  };

  return (
    <div className={`${sizes[size]} relative`}>
      {/* Main circle with gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-purple-500 via-pink-500 to-orange-400 rounded-full shadow-lg">
        {/* Inner glow effect */}
        <div className="absolute inset-1 bg-gradient-to-br from-purple-400 to-pink-400 rounded-full opacity-50"></div>
      </div>
      
      {/* Parking "P" symbol */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="text-white font-black text-2xl" style={{ 
          fontFamily: 'system-ui, -apple-system, sans-serif',
          textShadow: '0 2px 4px rgba(0,0,0,0.2)'
        }}>
          P
        </div>
      </div>
      
      {/* Sparkle accent */}
      <div className="absolute -top-1 -right-1 w-3 h-3 bg-yellow-300 rounded-full animate-pulse shadow-sm"></div>
    </div>
  );
}