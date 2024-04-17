/* eslint-env node */
module.exports = {
  env: {
    node: true,
    jest: true,
  },
  extends: [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:@typescript-eslint/recommended-requiring-type-checking",
    "plugin:import/warnings",
    "plugin:import/errors",
    "plugin:import/typescript",
    "plugin:jest/style",
    "plugin:jest/recommended",
    "plugin:jest-formatting/strict",
  ],
  ignorePatterns: [ 
    "node_modules", 
    "dist", 
    "coverage", 
    "*.conf.js", 
    "*.config.js", 
    "*.conf.ts", 
    "*.config.ts",
  ],
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: "latest",
    sourceType: "module",
    project: [ 
      "tsconfig.json", 
      "tsconfig.*.json",
    ],
  },
  plugins: [
    '@typescript-eslint',
  ],
  root: true,
  rules: {
    "no-multiple-empty-lines": [ "error", { max: 1, maxEOF: 0, maxBOF: 0 } ],
    // Auto fix indent on save
    "indent": [ "error", 2, { SwitchCase: 1 } ],
    // Don't allow console.log
    "no-console": "warn",
    // Only allow single quotes
    "quotes": [ "error", "single" ],
    // Never require a space before function parenthesis
    "space-before-function-paren": [ "error", "never" ],
    // No empty lines at start or end of blocks
    "padded-blocks": [ "error", "never" ],
    // No space before colon
    "key-spacing": [ "error", { beforeColon: false } ],
    // No space before comma
    "comma-spacing": [ "error", { before: false, after: true } ],
    // No space before semicolon
    "semi-spacing": [ "error", { before: false, after: true } ],
    // No space before colon in type
    "@typescript-eslint/type-annotation-spacing": [ "error", { before: false, after: true } ],
    // Always end line with semicolon
    "semi": [ "error", "always" ],
    // Always require trailing comma
    "comma-dangle": [ "error", "always-multiline" ],
    // Always space before and after ==, !=, ===, !==, <, >, <=, >=
    "space-infix-ops": "error",
    // No multiple spaces
    "no-multi-spaces": "error",
    // No trailing spaces
    "no-trailing-spaces": "error",
    // Order imports alphabetically
    "import/order": [ "error", { "newlines-between": "never" } ],
  },
  settings: {
    "import/parsers": {
      "@typescript-eslint/parser": [ ".ts" ]
    },
    "import/resolver": {
      typescript: {
        alwaysTryTypes: true,
        project: [ 
          "tsconfig.json", 
          "tsconfig.*.json" 
        ],
      },
    },
  },
}
