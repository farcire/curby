import { useState, useEffect, useRef } from 'react';
import { Search, MapPin, Navigation, Building2, Mic, MicOff } from 'lucide-react';

interface SearchResult {
  id: string;
  name: string;
  displayName: string;
  coordinates: [number, number];
  type: 'street' | 'address' | 'intersection' | 'business';
}

interface EmbeddedSearchProps {
  onLocationSelect: (coords: [number, number], name: string) => void;
}

export function EmbeddedSearch({ onLocationSelect }: EmbeddedSearchProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);
  
  useEffect(() => {
    const searchAddress = async () => {
      if (query.length < 2) {
        setResults([]);
        setShowResults(false);
        return;
      }
      
      setIsSearching(true);
      setShowResults(true);
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

  // Close results when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setShowResults(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Initialize speech recognition
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'en-US';

      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setQuery(transcript);
        setIsListening(false);
      };

      recognition.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
    }
  }, []);

  const toggleVoiceInput = () => {
    if (!recognitionRef.current) {
      alert('Voice input is not supported in your browser. Please use Chrome, Edge, or Safari.');
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      recognitionRef.current.start();
      setIsListening(true);
    }
  };
  
  const handleSelect = (result: SearchResult) => {
    onLocationSelect(
      [result.coordinates[1], result.coordinates[0]], // lat, lng
      result.displayName
    );
    setQuery('');
    setShowResults(false);
  };

  return (
    <div ref={searchRef} className="relative w-80">
      {/* Search Input */}
      <div className="relative">
        <Search className="absolute left-2.5 top-1/2 transform -translate-y-1/2 h-4 w-4 text-white" />
        <input
          type="text"
          placeholder="Where do you want to go?"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => query.length >= 2 && setShowResults(true)}
          className="w-full pl-9 pr-10 py-1.5 bg-white/40 backdrop-blur-md border-2 border-white/60 rounded-md text-white placeholder-white/90 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-white focus:bg-white/50 shadow-lg"
        />
        {/* Voice Input Button - Inside search bar */}
        <button
          onClick={toggleVoiceInput}
          className={`absolute right-2 top-1/2 transform -translate-y-1/2 p-1 rounded transition-all ${
            isListening
              ? 'text-red-400 animate-pulse'
              : 'text-white hover:text-white/80'
          }`}
          title={isListening ? 'Stop listening' : 'Voice search'}
        >
          {isListening ? (
            <MicOff className="h-4 w-4" />
          ) : (
            <Mic className="h-4 w-4" />
          )}
        </button>
      </div>
      
      {/* Results Dropdown */}
      {showResults && (
        <div className="absolute top-full mt-2 w-full bg-white rounded-lg shadow-2xl border border-gray-200 max-h-80 overflow-y-auto z-[9999]">
          {isSearching && (
            <div className="p-3 text-center text-sm text-gray-500">Searching...</div>
          )}
          
          {!isSearching && query.length >= 2 && results.length === 0 && (
            <div className="p-3 text-center text-sm text-gray-500">
              No results found
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
            
            // Clean display name - remove cardinal directions for streets
            let displayName = result.displayName;
            if (result.type === 'street') {
              // Just show the street name without cardinal direction
              displayName = result.name;
            }
            
            return (
              <button
                key={result.id}
                onClick={() => handleSelect(result)}
                className="w-full text-left p-3 hover:bg-gray-50 transition-colors flex items-start gap-3 border-b border-gray-100 last:border-b-0"
              >
                <Icon className={`h-4 w-4 ${iconColor} flex-shrink-0 mt-0.5`} />
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-gray-900 text-sm truncate">{result.name}</div>
                  <div className="text-xs text-gray-500 truncate">{displayName}</div>
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}