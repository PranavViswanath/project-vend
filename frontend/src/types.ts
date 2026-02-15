export interface Donation {
  id: number;
  category: "fruit" | "snack" | "drink";
  item_name: string;
  estimated_weight_lbs: number | null;
  estimated_expiry: string | null;
  timestamp: string;
  image_path: string | null;
  donor_id: string | null;
}

export interface Stats {
  total_items: number;
  total_weight_lbs: number;
  unique_donors: number;
  by_category: Record<string, number>;
}

export interface PipelineResult {
  donation_id: number;
  category: string;
  item_name: string;
  estimated_weight_lbs: number | null;
  estimated_expiry: string | null;
  image_path: string | null;
}

export interface PipelineState {
  mode: "idle" | "streaming" | "processing" | "classified" | "error";
  status_text: string;
  last_result: PipelineResult | null;
  updated_at: string;
}
