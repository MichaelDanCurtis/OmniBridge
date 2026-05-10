// @vitest-environment jsdom
import "@testing-library/jest-dom/vitest";

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import App from "./App";

describe("App", () => {
  it("renders the consultant workspace shell", () => {
    render(<App />);

    expect(
      screen.getByRole("heading", { name: "OmniBridge Consultant Workspace" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Claims Portal" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Approve Estimate" })).toBeInTheDocument();
  });
});
