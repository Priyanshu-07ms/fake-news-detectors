// src/App.test.js
import { render, screen } from "@testing-library/react";
import App from "./App";

test("renders app header", () => {
  render(<App />);
  const heading = screen.getByText(/Fake News Radar/i);
  expect(heading).toBeInTheDocument();
});
