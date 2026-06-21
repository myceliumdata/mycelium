import { describe, expect, it } from "vitest";
import {
  DEFAULT_MVR_BIND_FIELDS,
  defaultRecordTypeFromPolicy,
  listRecordTypesFromPolicy,
  mvrBindFieldsFromPolicy,
  statusEntityKeyForResolve,
} from "./mvr";

const crmPolicy = {
  mvr: {
    bind_fields: ["name", "employer"],
  },
};

const baseballPolicy = {
  mvr: {
    default_record_type: "player",
    record_types: {
      player: {
        bind_fields: ["player", "debut_team", "debut_year"],
      },
      team: {
        bind_fields: ["team"],
      },
    },
  },
};

describe("mvrBindFieldsFromPolicy", () => {
  it("returns flat CRM bind fields", () => {
    expect(mvrBindFieldsFromPolicy(crmPolicy)).toEqual(["name", "employer"]);
  });

  it("returns baseball player bind fields by default", () => {
    expect(mvrBindFieldsFromPolicy(baseballPolicy)).toEqual([
      "player",
      "debut_team",
      "debut_year",
    ]);
  });

  it("returns baseball team bind fields when record type is team", () => {
    expect(mvrBindFieldsFromPolicy(baseballPolicy, "team")).toEqual(["team"]);
  });

  it("falls back to CRM defaults when policy is missing", () => {
    expect(mvrBindFieldsFromPolicy(undefined)).toEqual([
      ...DEFAULT_MVR_BIND_FIELDS,
    ]);
  });
});

describe("listRecordTypesFromPolicy", () => {
  it("returns sorted record type keys for baseball", () => {
    expect(listRecordTypesFromPolicy(baseballPolicy)).toEqual([
      "player",
      "team",
    ]);
  });

  it("returns empty list for flat CRM policy", () => {
    expect(listRecordTypesFromPolicy(crmPolicy)).toEqual([]);
  });
});

describe("defaultRecordTypeFromPolicy", () => {
  it("reads default_record_type from baseball policy", () => {
    expect(defaultRecordTypeFromPolicy(baseballPolicy)).toBe("player");
  });

  it("returns null when default is absent", () => {
    expect(defaultRecordTypeFromPolicy(crmPolicy)).toBeNull();
  });
});

describe("statusEntityKeyForResolve", () => {
  it("uses first non-empty bind field without assuming name", () => {
    const key = statusEntityKeyForResolve(
      "lookup",
      "",
      { player: "Hank Aaron", debut_team: "", debut_year: "" },
      ["player", "debut_team", "debut_year"],
    );
    expect(key).toBe("Hank Aaron");
  });
});
