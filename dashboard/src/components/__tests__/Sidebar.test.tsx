/**
 * FR-F19: Sidebar — hamburger toggles drawer, aria-expanded flips.
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import Sidebar from "../Sidebar";

// Stub Next.js navigation hooks
vi.mock("next/navigation", () => ({
  usePathname: () => "/",
}));

// Stub Next.js Link
vi.mock("next/link", () => ({
  default: ({
    href,
    children,
    ...rest
  }: {
    href: string;
    children: React.ReactNode;
    [key: string]: unknown;
  }) => (
    <a href={href} {...rest}>
      {children}
    </a>
  ),
}));

describe("Sidebar", () => {
  it("renders hamburger button with aria-expanded=false initially", () => {
    render(<Sidebar />);
    const hamburger = screen.getByRole("button", { name: /open navigation/i });
    expect(hamburger).toBeInTheDocument();
    expect(hamburger).toHaveAttribute("aria-expanded", "false");
  });

  it("toggles aria-expanded when hamburger is clicked", () => {
    render(<Sidebar />);
    const hamburger = screen.getByRole("button", { name: /open navigation/i });
    fireEvent.click(hamburger);
    // After click, aria-expanded should be "true" and label changes
    const closeBtn = screen.getByRole("button", { name: /close navigation/i });
    expect(closeBtn).toHaveAttribute("aria-expanded", "true");
  });

  it("contains primary navigation links", () => {
    render(<Sidebar />);
    expect(screen.getAllByRole("link", { name: /market overview/i }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("link", { name: /stock analyzer/i }).length).toBeGreaterThan(0);
  });
});
