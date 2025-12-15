import { API_URL } from "./config";

// Types matching backend API response
export interface ApiRestaurant {
  id: string;
  name: string;
  description?: string;
  address?: string;
  phone?: string;
  email?: string;
  website?: string;
  cuisine?: string;
  price_level?: number;
  rating?: number;
  review_count?: number;
  open_time?: string;
  close_time?: string;
  distance?: number | null;
  image?: string;
  images?: string[];
  is_open?: boolean;
  specialty?: string[];
}

export interface ApiReview {
  id: string;
  restaurant_id: string;
  user_id?: string | null;
  user_name?: string;
  user_avatar?: string | null;
  author_name?: string;
  rating: number;
  title?: string | null;
  content?: string;
  images?: string[];
  likes?: number;
  is_verified?: boolean;
  visit_date?: string;
  reply?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  error?: string | null;
  meta?: {
    timestamp: string;
    pagination?: {
      page: number;
      limit: number;
      total: number;
      total_pages: number;
      has_next: boolean;
      has_prev: boolean;
    };
  };
}

// Frontend types (matching App.tsx interface)
export interface MenuItem {
  id: string;
  name: string;
  description: string;
  price: number;
  image: string;
  category: string;
}

export interface Restaurant {
  id: string;
  name: string;
  image: string;
  cuisine: string;
  rating: number;
  reviewCount: number;
  priceLevel: number;
  distance: string;
  openTime: string;
  specialty: string[];
  description: string;
  address: string;
  phone: string;
  menu: MenuItem[];
}

// Convert API restaurant to frontend Restaurant format
export function mapApiRestaurantToFrontend(apiRestaurant: ApiRestaurant): Restaurant {
  return {
    id: apiRestaurant.id,
    name: apiRestaurant.name,
    image: apiRestaurant.image || apiRestaurant.images?.[0] || 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=800',
    cuisine: apiRestaurant.cuisine || 'Ẩm thực Việt Nam',
    rating: apiRestaurant.rating || 4.0,
    reviewCount: apiRestaurant.review_count || 0,
    priceLevel: apiRestaurant.price_level || 2,
    distance: apiRestaurant.distance ? `${apiRestaurant.distance} km` : '0.5 km',
    openTime: formatOpenTime(apiRestaurant.open_time, apiRestaurant.close_time),
    specialty: apiRestaurant.specialty || [],
    description: apiRestaurant.description || '',
    address: apiRestaurant.address || '',
    phone: apiRestaurant.phone || '',
    menu: [], // Menu items loaded separately if needed
  };
}

function formatOpenTime(openTime?: string, closeTime?: string): string {
  if (!openTime) return '7:00 - 22:00';
  const open = openTime?.substring(0, 5) || '07:00';
  const close = closeTime?.substring(0, 5) || '22:00';
  return `${open} - ${close}`;
}

// API Functions
export async function fetchRestaurants(limit: number = 100, page: number = 1): Promise<Restaurant[]> {
  try {
    const response = await fetch(`${API_URL}/restaurants?limit=${limit}&page=${page}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const result: ApiResponse<ApiRestaurant[]> = await response.json();
    
    if (result.success && Array.isArray(result.data)) {
      return result.data.map(mapApiRestaurantToFrontend);
    }
    
    console.error('API returned unexpected format:', result);
    return [];
  } catch (error) {
    console.error('Error fetching restaurants:', error);
    return [];
  }
}

export async function fetchRestaurantById(id: string): Promise<Restaurant | null> {
  try {
    const response = await fetch(`${API_URL}/restaurants/${id}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const result: ApiResponse<ApiRestaurant> = await response.json();
    
    if (result.success && result.data) {
      return mapApiRestaurantToFrontend(result.data);
    }
    return null;
  } catch (error) {
    console.error('Error fetching restaurant:', error);
    return null;
  }
}

export async function getNewestRestaurants(): Promise<Restaurant[]> {
  try {
    const response = await fetch(`${API_URL}/restaurants/newest`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const result: ApiResponse<ApiRestaurant[]> = await response.json();
    
    if (result.success && Array.isArray(result.data)) {
      return result.data.map(mapApiRestaurantToFrontend);
    }
    return [];
  } catch (error) {
    console.error('Error fetching newest restaurants:', error);
    return [];
  }
}

export async function fetchRestaurantReviews(restaurantId: string): Promise<ApiReview[]> {
  try {
    const response = await fetch(`${API_URL}/reviews/restaurant/${restaurantId}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const result: ApiResponse<ApiReview[]> = await response.json();
    
    if (result.success && Array.isArray(result.data)) {
      return result.data;
    }
    return [];
  } catch (error) {
    console.error('Error fetching reviews:', error);
    return [];
  }
}

export async function searchRestaurants(query: string): Promise<Restaurant[]> {
  try {
    const response = await fetch(`${API_URL}/restaurants/search?q=${encodeURIComponent(query)}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const result: ApiResponse<ApiRestaurant[]> = await response.json();
    
    if (result.success && Array.isArray(result.data)) {
      return result.data.map(mapApiRestaurantToFrontend);
    }
    return [];
  } catch (error) {
    console.error('Error searching restaurants:', error);
    return [];
  }
}
