import { expect, test } from "@playwright/test";

test("explores the public environment and provenance", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "The orbital shell, read as one environment" })).toBeVisible();
  await expect(page.getByText("Validated development dataset")).toBeVisible();
  await page.getByRole("link", { name: "3D Environment", exact: true }).click();
  await expect(page.getByRole("heading", { name: "A population, not a constellation" })).toBeVisible();
  await expect(page.getByText("40,000", { exact: true })).toBeVisible({ timeout: 30_000 });
  await page.getByRole("link", { name: "Methodology" }).click();
  await expect(page.getByRole("heading", { name: "Reproducible by design" })).toBeVisible();
});
