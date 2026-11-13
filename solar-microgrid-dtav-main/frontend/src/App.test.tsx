// @vitest-environment jsdom
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import App from "./App";
import { fmt } from "./types";
describe("dashboard", () => {
  it("preserves unknown hardware data", () => {
    expect(fmt(undefined, " V")).toBe("—");
    expect(fmt(NaN)).toBe("—");
  });
  it("renders disconnected state", () => {
    vi.stubGlobal(
      "WebSocket",
      class {
        close() {}
      },
    );
    const r = render(<App />);
    expect(screen.getByText("DISCONNECTED")).toBeTruthy();
    expect(
      screen.getByText(
        "Waiting for the local backend. No device data is available.",
      ),
    ).toBeTruthy();
    r.unmount();
  });
});
