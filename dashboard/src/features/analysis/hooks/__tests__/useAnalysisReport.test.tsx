/**
 * FR-F19: useAnalysisReport — loads data, handles error path via mocked api.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useAnalysisReport } from "../useAnalysisReport";
import type { AnalysisReportPayload } from "@/lib/api.types";

describe("useAnalysisReport", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("starts with loading=false and generated=false", () => {
    const fetcher = vi.fn<() => Promise<AnalysisReportPayload>>();
    const { result } = renderHook(() => useAnalysisReport(fetcher));
    expect(result.current.loading).toBe(false);
    expect(result.current.generated).toBe(false);
    expect(result.current.data).toBeNull();
  });

  it("sets generated=true and populates summary on success", async () => {
    const payload: AnalysisReportPayload = {
      llm_summary: "Test summary",
      news: [],
      evidence: { key: "value" },
    };
    const fetcher = vi.fn<() => Promise<AnalysisReportPayload>>().mockResolvedValue(payload);
    const { result } = renderHook(() => useAnalysisReport(fetcher));

    await act(async () => {
      await result.current.generate();
    });

    expect(result.current.generated).toBe(true);
    expect(result.current.summary).toBe("Test summary");
    expect(result.current.evidence).toEqual({ key: "value" });
    expect(result.current.error).toBeNull();
  });

  it("sets error on fetch failure", async () => {
    const fetcher = vi.fn<() => Promise<AnalysisReportPayload>>().mockRejectedValue(
      new Error("Network error")
    );
    const { result } = renderHook(() => useAnalysisReport(fetcher));

    await act(async () => {
      await result.current.generate();
    });

    expect(result.current.generated).toBe(false);
    expect(result.current.error).toBe("Network error");
    expect(result.current.loading).toBe(false);
  });

  it("reset() clears state", async () => {
    const payload: AnalysisReportPayload = { llm_summary: "Hello" };
    const fetcher = vi.fn<() => Promise<AnalysisReportPayload>>().mockResolvedValue(payload);
    const { result } = renderHook(() => useAnalysisReport(fetcher));

    await act(async () => {
      await result.current.generate();
    });

    expect(result.current.generated).toBe(true);

    act(() => {
      result.current.reset();
    });

    expect(result.current.generated).toBe(false);
    expect(result.current.data).toBeNull();
  });
});
