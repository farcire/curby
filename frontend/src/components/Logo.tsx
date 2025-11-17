export function Logo({ size = 'md', animated = false }: { size?: 'sm' | 'md' | 'lg'; animated?: boolean }) {
  const sizes = {
    sm: 'w-6 h-6',
    md: 'w-12 h-12',
    lg: 'w-16 h-16',
  };

  const textSizes = {
    sm: 'text-lg',
    md: 'text-2xl',
    lg: 'text-3xl',
  };

  return (
    <div className={`${sizes[size]} relative ${animated ? 'animate-bounce' : ''}`}>
      {/* Main circle with gradient - tilted for motion */}
      <div className="absolute inset-0 bg-gradient-to-br from-purple-500 via-pink-500 to-orange-400 rounded-full shadow-lg transform rotate-12">
        {/* Inner glow effect */}
        <div className="absolute inset-1 bg-gradient-to-br from-purple-400 to-pink-400 rounded-full opacity-50"></div>
      </div>
      
      {/* Parking "P" symbol - counter-rotated for upright appearance */}
      <div className="absolute inset-0 flex items-center justify-center transform -rotate-12">
        <div className={`text-white font-black ${textSizes[size]}`} style={{ 
          fontFamily: 'system-ui, -apple-system, sans-serif',
          textShadow: '0 2px 4px rgba(0,0,0,0.2)'
        }}>
          P
        </div>
      </div>
      
      {/* Motion lines for speed effect */}
      <div className="absolute -left-2 top-1/2 -translate-y-1/2 opacity-40">
        <div className="w-3 h-0.5 bg-gradient-to-r from-purple-400 to-transparent rounded-full"></div>
        <div className="w-2 h-0.5 bg-gradient-to-r from-pink-400 to-transparent rounded-full mt-1"></div>
      </div>
      
      {/* Sparkle accent */}
      <div className="absolute -top-1 -right-1 w-3 h-3 bg-yellow-300 rounded-full animate-pulse shadow-sm"></div>
    </div>
  );
}