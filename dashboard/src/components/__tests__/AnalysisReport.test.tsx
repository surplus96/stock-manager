/**
 * FR-F19: AnalysisReport — renders without a11y violations, toggles expand.
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import AnalysisReport from "../AnalysisReport";

// react-markdown and remark-gfm are not installed in test environment;
// stub them so the import chain resolves without requiring node_modules.
vi.mock("react-markdown", () => ({
  default: ({ children }: { children: string }) => <div data-testid="markdown">{children}</div>,
}));
vi.mock("remark-gfm", () => ({ default: () => {} }));

function noop() {}

describe("AnalysisReport", () => {
  it("renders generate button when not yet generated", () => {
    render(
      <AnalysisReport
        title="Test Report"
        loading={false}
        onGenerate={noop}
        generated={false}
      />
    );
    expect(screen.getByRole("button", { name: /리포트 생성/i })).toBeInTheDocument();
  });

  it("renders loading indicator when loading=true", () => {
    render(
      <AnalysisReport
        title="Test Report"
        loading={true}
        onGenerate={noop}
        generated={false}
      />
    );
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("renders report content when generated=true", () => {
    render(
      <AnalysisReport
        title="Test Report"
        loading={false}
        onGenerate={noop}
        generated={true}
        llmSummary="AI summary content here"
      />
    );
    expect(screen.getByRole("region")).toBeInTheDocument();
    expect(screen.getByText("AI summary content here")).toBeInTheDocument();
  });

  it("toggles expand/collapse via chevron button", () => {
    render(
      <AnalysisReport
        title="Test Report"
        loading={false}
        onGenerate={noop}
        generated={true}
        llmSummary="Summary text"
      />
    );
    // Initially expanded — region is visible
    const region = screen.getByRole("region");
    expect(region).toBeInTheDocument();

    // Click collapse toggle
    const toggle = screen.getByRole("button", { name: /섹션 접기/i });
    expect(toggle).toHaveAttribute("aria-expanded", "true");
    fireEvent.click(toggle);
    expect(toggle).toHaveAttribute("aria-expanded", "false");
  });
});
