import { useState, useEffect } from 'react';
import { Search, X, MapPin, Navigation, Building2 } from 'lucide-react';

interface SearchResult {
  id: string;
  name: string;
  displayName: string;
  coordinates: [number, number];
  type: 'street' | 'address' | 'intersection' | 'business';
}

interface AddressSearchProps {
  onLocationSelect: (coords: [number, number], name: string) => void;
  onClose: () => void;
}

export function AddressSearch({ onLocationSelect, onClose }: AddressSearchProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  
  useEffect(() => {
    const searchAddress = async () => {
      if (query.length < 2) {
        setResults([]);
        return;
      }
      
      setIsSearching(true);
      try {
        const response = await fetch(
          `${import.meta.env.VITE_API_URL}/api/v1/search?q=${encodeURIComponent(query)}&limit=10`
        );
        const data = await response.json();
        setResults(data);
      } catch (error) {
        console.error('Search error:', error);
        setResults([]);
      } finally {
        setIsSearching(false);
      }
    };
    
    const timer = setTimeout(searchAddress, 300); // Debounce
    return () => clearTimeout(timer);
  }, [query]);
  
  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-md w-full max-h-[80vh] flex flex-col">
        
        {/* Header */}
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-lg font-bold text-gray-900">Search SF Address</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="h-5 w-5" />
          </button>
        </div>
        
        {/* Search Input */}
        <div className="p-4 border-b border-gray-200">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Address, intersection, or business..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              autoFocus
            />
          </div>
          <p className="text-xs text-gray-500 mt-2">
            Try: "2125 Bryant St", "Bryant and 20th", or "Tartine Manufactory"
          </p>
        </div>
        
        {/* Results */}
        <div className="flex-1 overflow-y-auto p-2">
          {isSearching && (
            <div className="text-center py-8 text-gray-500">Searching...</div>
          )}
          
          {!isSearching && query.length >= 2 && results.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No results found. Try a different address.
            </div>
          )}
          
          {results.map((result) => {
            // Choose icon based on result type
            let Icon = MapPin;
            let iconColor = 'text-purple-600';
            if (result.type === 'intersection') {
              Icon = Navigation;
              iconColor = 'text-blue-600';
            } else if (result.type === 'business') {
              Icon = Building2;
              iconColor = 'text-green-600';
            }
            
            return (
              <button
                key={result.id}
                onClick={() => {
                  onLocationSelect(
                    [result.coordinates[1], result.coordinates[0]], // lat, lng
                    result.displayName
                  );
                  onClose();
                }}
                className="w-full text-left p-3 hover:bg-gray-50 rounded-lg transition-colors flex items-start gap-3"
              >
                <Icon className={`h-5 w-5 ${iconColor} flex-shrink-0 mt-0.5`} />
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-gray-900 truncate">{result.name}</div>
                  <div className="text-sm text-gray-500 truncate">{result.displayName}</div>
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}