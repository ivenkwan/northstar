// ESLint 9 flat config — enforces PRD §17.3 prohibited patterns in CI.
// A time-bounded waiver is the only escape hatch (§17.3); there are none today.
import js from "@eslint/js";
import tseslint from "typescript-eslint";

const BANNED_FETCH = {
  selector: "CallExpression[callee.name='fetch']",
  message: "raw fetch is only permitted in apps/mobile/src/transport.ts (§17.3 transport boundary)",
};
const DOUBLE_ASSERTION = {
  selector: "TSAsExpression > TSAsExpression",
  message: "double type assertions (`as unknown as T`) are prohibited (§17.3)",
};
const EMPTY_CATCH = {
  selector: "CatchClause > Block[body.length=0]",
  message: "catch blocks must not silently swallow errors (§17.3)",
};

export default tseslint.config(
  {
    ignores: [
      "**/node_modules/**",
      "**/dist/**",
      "packages/contracts/src/generated/**", // generated output is never hand-edited (§17.4)
      "apps/mobile/.expo/**",
    ],
  },
  js.configs.recommended,
  ...tseslint.configs.recommendedTypeChecked,
  {
    files: ["apps/**/*.{ts,tsx}", "packages/**/*.ts"],
    languageOptions: {
      parserOptions: { projectService: true },
    },
    rules: {
      // §17.3: explicit/implicit any and unsafe usage
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/no-unsafe-assignment": "error",
      "@typescript-eslint/no-unsafe-member-access": "error",
      "@typescript-eslint/no-unsafe-argument": "error",
      "@typescript-eslint/no-unsafe-call": "error",
      "@typescript-eslint/no-unsafe-return": "error",
      // §17.3: @ts-ignore and friends
      "@typescript-eslint/ban-ts-comment": [
        "error",
        { "ts-expect-error": "allow-with-description", "ts-ignore": true, "ts-nocheck": true, "ts-check": true },
      ],
      // §17.3: non-null assertions
      "@typescript-eslint/no-non-null-assertion": "error",
      "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_", varsIgnorePattern: "^_" }],
      // §17.3: raw fetch outside the transport package + structural bans
      "no-restricted-syntax": ["error", BANNED_FETCH, DOUBLE_ASSERTION, EMPTY_CATCH],
      // catch blocks assume nothing (§17.3) — tsconfig enforces unknown; lint keeps it honest
      "no-throw-literal": "error",
      "@typescript-eslint/consistent-type-assertions": [
        "error",
        { objectLiteralTypeAssertions: "never", assertionStyle: "as" },
      ],
    },
  },
  {
    // The transport module is the sanctioned fetch boundary.
    files: ["apps/mobile/src/transport.ts"],
    rules: {
      "no-restricted-syntax": ["error", DOUBLE_ASSERTION, EMPTY_CATCH],
    },
  },
  {
    // Tests live outside tsconfig `include` (typecheck targets src only) and use
    // narrow casts on fixtures by design — lint them without type-aware rules.
    files: ["**/test/**/*.{ts,tsx}", "**/*.test.ts"],
    extends: [tseslint.configs.disableTypeChecked],
    rules: {
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/ban-ts-comment": "error",
      "@typescript-eslint/no-non-null-assertion": "error",
      "no-restricted-syntax": ["error", DOUBLE_ASSERTION, EMPTY_CATCH],
    },
  },
);
