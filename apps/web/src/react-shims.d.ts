declare namespace JSX {
  interface IntrinsicElements {
    [elementName: string]: Record<string, unknown>;
  }
}

declare module "react" {
  export const StrictMode: (props: { children?: unknown }) => unknown;
}

declare module "react-dom/client" {
  export function createRoot(element: Element): {
    render(children: unknown): void;
  };
}

declare module "react/jsx-runtime" {
  export function jsx(type: unknown, props: unknown, key?: unknown): unknown;
  export function jsxs(type: unknown, props: unknown, key?: unknown): unknown;
  export const Fragment: unknown;
}
