/**
 * TypeScript interfaces for Project Lend API data structures
 */

export interface Donation {
  id: number;
  category: string;
  item_name: string;
  estimated_weight_lbs: number | null;
  estimated_expiry: string | null;
  timestamp: string;
  image_path: string;
  donor_id: string | null;
}

export interface Stats {
  total_items: number;
  total_weight_lbs: number;
  unique_donors: number;
  by_category: {
    [key: string]: number;
  };
}

export interface PipelineState {
  state: "IDLE" | "WARMUP" | "WATCHING" | "SETTLING" | "CLASSIFYING" | "COOLDOWN";
  timestamp: string;
  camera_active: boolean;
  motion_area: number;
  last_category: string | null;
  last_item: string | null;
  cooldown_remaining: number;
}
