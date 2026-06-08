export interface HealthResponse {
  status: "ok" | "error";
  network_name?: string | null;
  display_name?: string | null;
  network_root?: string | null;
  message?: string;
}

export interface CategorySummary {
  name: string;
  assigned_agent: string | null;
  example_count: number;
  examples: string[];
}

export interface SpecialistSummary {
  name: string;
  category: string;
  module_on_disk: boolean;
  storage_strategy: string | null;
  record_count: number;
  fields_tracked: string[];
  pending_count: number;
  na_count: number;
  found_count: number;
}

export interface EntityFieldStatus {
  field: string;
  category: string;
  agent: string;
  status: string;
  value: string | null;
}

export interface StatusResponse {
  network_name: string | null;
  network_root: string;
  display_name: string | null;
  seed_people_count: number;
  ontology_present: boolean;
  ontology_message: string;
  categories: CategorySummary[];
  specialists: SpecialistSummary[];
  entity_key: string | null;
  entity_matches: number;
  entity_fields: EntityFieldStatus[];
}

export interface OntologyCategory {
  name: string;
  description: string;
  examples: string[];
}

export interface CapabilitiesResponse {
  network_name: string | null;
  display_name: string | null;
  guide_present: boolean;
  guide: string | null;
  guide_note?: string;
  ontology: {
    present: boolean;
    message: string | null;
    categories: OntologyCategory[];
  };
  policy: Record<string, unknown>;
}
