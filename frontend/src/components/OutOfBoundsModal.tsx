import { Logo } from './Logo';

interface OutOfBoundsModalProps {
  distanceKm: number;
  onViewSF: () => void;
  onSearchAddress: () => void;
  onDismiss: () => void;
}

export function OutOfBoundsModal({
  onViewSF,
  onSearchAddress,
  onDismiss
}: OutOfBoundsModalProps) {
  
  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in">
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden animate-scale-in">
        
        {/* Gradient Header with Logo */}
        <div className="bg-gradient-to-r from-purple-600 via-pink-600 to-orange-500 p-6 text-center relative overflow-hidden">
          <div className="absolute inset-0 opacity-10">
            <div className="absolute top-0 left-0 w-32 h-32 bg-white rounded-full -translate-x-16 -translate-y-16"></div>
            <div className="absolute bottom-0 right-0 w-40 h-40 bg-white rounded-full translate-x-20 translate-y-20"></div>
          </div>
          <div className="relative flex items-center justify-center gap-3">
            <Logo size="sm" />
            <h2 className="text-2xl font-bold text-white">
              You're far from San Francisco!
            </h2>
          </div>
        </div>
        
        {/* Content */}
        <div className="p-6">
          <p className="text-gray-700 text-center leading-relaxed mb-6">
            Curby makes decoding San Francisco street parking rules easy. See where you can street park now.
          </p>
          
          <div className="space-y-3">
            <button
              onClick={onViewSF}
              className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-bold py-3.5 px-4 rounded-xl transition-all transform hover:scale-[1.02] shadow-lg hover:shadow-xl"
            >
              View SF Map
            </button>
            <button
              onClick={onSearchAddress}
              className="w-full bg-gradient-to-r from-blue-50 to-purple-50 hover:from-blue-100 hover:to-purple-100 text-purple-700 font-semibold py-3.5 px-4 rounded-xl transition-all border-2 border-purple-200 hover:border-purple-300"
            >
              Search SF Address
            </button>
            <button
              onClick={onDismiss}
              className="w-full text-gray-500 hover:text-gray-700 font-medium py-2 transition-colors"
            >
              Dismiss
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}