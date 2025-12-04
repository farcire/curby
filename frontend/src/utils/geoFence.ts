export const SF_BOUNDS = {
  north: 37.8324,
  south: 37.7034,
  east: -122.3482,
  west: -122.5155
};

export const SF_CENTER: [number, number] = [37.7749, -122.4194];

export function isInSanFrancisco(lat: number, lng: number): boolean {
  return lat >= SF_BOUNDS.south && 
         lat <= SF_BOUNDS.north &&
         lng >= SF_BOUNDS.west && 
         lng <= SF_BOUNDS.east;
}

export function getDistanceToSF(lat: number, lng: number): number {
  // Haversine distance to SF center
  const R = 6371; // Earth radius in km
  const dLat = (SF_CENTER[0] - lat) * Math.PI / 180;
  const dLng = (SF_CENTER[1] - lng) * Math.PI / 180;
  const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(lat * Math.PI / 180) * Math.cos(SF_CENTER[0] * Math.PI / 180) *
            Math.sin(dLng/2) * Math.sin(dLng/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c;
}