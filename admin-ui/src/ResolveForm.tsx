import { bindFieldLabel } from "./mvr";

export type ResolveMode = "id" | "lookup";

export interface ResolveFormProps {
  bindFields: string[];
  mode: ResolveMode;
  registryId: string;
  lookupValues: Record<string, string>;
  disabled?: boolean;
  radioName: string;
  onModeChange: (mode: ResolveMode) => void;
  onRegistryIdChange: (value: string) => void;
  onLookupFieldChange: (field: string, value: string) => void;
}

export default function ResolveForm({
  bindFields,
  mode,
  registryId,
  lookupValues,
  disabled = false,
  radioName,
  onModeChange,
  onRegistryIdChange,
  onLookupFieldChange,
}: ResolveFormProps) {
  return (
    <fieldset className="query-step-fieldset resolve-form" disabled={disabled}>
      <legend>Step 1 — Resolve by</legend>
      <div
        className="mode-radio-row"
        role="radiogroup"
        aria-label="Resolve mode"
      >
        <label>
          <input
            type="radio"
            name={radioName}
            checked={mode === "id"}
            onChange={() => onModeChange("id")}
          />
          Registry ID
        </label>
        <label>
          <input
            type="radio"
            name={radioName}
            checked={mode === "lookup"}
            onChange={() => onModeChange("lookup")}
          />
          MVR lookup
        </label>
      </div>
      <div className="resolve-inputs">
        {mode === "id" ? (
          <input
            type="search"
            placeholder="Registry UUID"
            value={registryId}
            onChange={(event) => onRegistryIdChange(event.target.value)}
            aria-label="Registry ID"
          />
        ) : (
          bindFields.map((field) => (
            <input
              key={field}
              type="search"
              placeholder={bindFieldLabel(field)}
              value={lookupValues[field] ?? ""}
              onChange={(event) =>
                onLookupFieldChange(field, event.target.value)
              }
              aria-label={`Lookup ${field}`}
            />
          ))
        )}
      </div>
    </fieldset>
  );
}
